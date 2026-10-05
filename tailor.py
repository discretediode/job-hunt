#!/usr/bin/env python3
"""
Automatic Tailoring Engine.
Takes ranked.json -> Top 10 jobs -> _tailoring.json specs.

This script automates the 'tailoring' phase by asking an LLM to generate
specific text for the CV and Cover Letter based on the job's requirements
and the candidate's profile.
"""
import json
import pathlib
import sys
import subprocess
import time

HERE = pathlib.Path(__file__).resolve().parent
RANKED = HERE / "ranked.json"
VAULT = HERE / "my_profile"
IDENTITY = HERE / "identity.local.json"

def get_vault_context():
    """Read all markdown files in the vault."""
    context = []
    for f in VAULT.glob("*.md"):
        context.append(f"--- {f.name} ---\n{f.read_text()}")
    return "\n\n".join(context)

def tailor_jobs():
    if not RANKED.exists():
        sys.exit(f"missing {RANKED.name} - run judge.py first")

    ranked = json.loads(RANKED.read_text())
    if not ranked:
        print("No ranked jobs to tailor.")
        return

    # Take the top 10 fitting jobs
    top_10 = ranked[:10]

    vault_text = get_vault_context()
    identity = json.loads(IDENTITY.read_text()) if IDENTITY.exists() else {}
    forbidden = identity.get("forbidden_claims", [])

    # We'll tailor each job individually to ensure high quality and avoid context drift
    tailoring_specs = {}

    for i, job in enumerate(top_10, 1):
        print(f"Tailoring {i}/10: {job.get('company')} - {job.get('title')}...")

        prompt = f"""
You are an expert CV and Cover Letter writer. Your goal is to tailor a candidate's application for a specific job.

CANDIDATE PROFILE:
{vault_text}

JOB POSTING:
Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Description: {job.get('why')} (Judge's reasoning)

FORBIDDEN CLAIMS:
The following claims are strictly forbidden. If you include them, the application will be rejected:
{json.dumps(forbidden, indent=1)}

TASK:
Generate a tailoring specification in JSON format.
1. CV Tagline: A one-sentence punchy headline that positions the candidate as the perfect fit.
2. CV Profile: A 3-4 sentence professional summary focusing on the intersection of the candidate's skills and the job's needs.
3. Cover Letter Body: 3-4 paragraphs of persuasive prose.
   - Paragraph 1: The "Why them" (why this company and this role).
   - Paragraph 2: The "Why me" (concrete evidence from the profile).
   - Paragraph 3: The "Bridge" (how the candidate solves their specific problem).
   - Paragraph 4: Call to action.
4. Form Fields: Common application questions (e.g., "Why do you want to work here?") and a concise answer.

OUTPUT FORMAT:
Return ONLY a JSON object:
{{
  "tagline": "...",
  "profile": "...",
  "cover_letter": "...",
  "form_fields": {{
    "question": "answer",
    ...
  }}
}}
"""

        try:
            p = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True, text=True, check=True
            )
            result_text = p.stdout

            # Extract JSON
            import re
            match = re.search(r"\{\s*\"tagline\".*\}\s*", result_text, re.S)
            if not match:
                # Try a more general JSON search if the specific one fails
                match = re.search(r"\{.*\}", result_text, re.S)

            if not match:
                print(f"  ! Failed to extract JSON for {job['id']}")
                continue

            tailoring_specs[job["id"]] = json.loads(match.group(0))
            time.sleep(1) # be polite

        except Exception as e:
            print(f"  ! Error tailoring {job['id']}: {e}")

    # Save the final specs to _tailoring.json
    with open(HERE / "_tailoring.json", "w", encoding="utf-8") as f:
        json.dump(tailoring_specs, f, indent=1, ensure_ascii=False)

    print(f"\nTailoring complete. Specifications saved to _tailoring.json")

if __name__ == "__main__":
    tailor_jobs()
