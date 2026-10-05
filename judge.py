#!/usr/bin/env python3
"""
Automatic Job Judge.
Takes latest.json -> LLM Analysis -> ranked.json.

This script replaces the manual 'bundle' and manual judgment process.
It reads the user's profile vault and the latest job postings, then asks
an LLM to score them and assign a verdict and track.
"""
import json
import pathlib
import sys
import subprocess
import time

HERE = pathlib.Path(__file__).resolve().parent
LATEST = HERE / "latest.json"
RANKED = HERE / "ranked.json"
TEMPLATE = HERE / "ranked.template.json"
VAULT = HERE / "my_profile"

def get_vault_context():
    """Read all markdown files in the vault to provide context to the LLM."""
    context = []
    for f in VAULT.glob("*.md"):
        context.append(f"--- {f.name} ---\n{f.read_text()}")
    return "\n\n".join(context)

def judge_jobs():
    if not LATEST.exists():
        sys.exit(f"missing {LATEST.name} - run scrape.py first")

    jobs = json.loads(LATEST.read_text())
    if not jobs:
        print("No new jobs to judge.")
        return

    vault_text = get_vault_context()

    # We'll process jobs in batches to avoid context window issues,
    # though for 10-50 jobs, one prompt usually suffices.
    # For this universal version, we delegate the actual LLM call to the
    # 'claude' CLI as the user already has it configured.

    prompt = f"""
You are a professional career coach and recruiter. Your task is to judge how well
the following job postings fit the candidate's profile.

CANDIDATE PROFILE:
{vault_text}

JOB POSTINGS:
{json.dumps(jobs, indent=1, ensure_ascii=False)}

JUDGMENT RULES:
1. Score (0-100): How well the candidate fits. 100 is a perfect match.
2. Verdict: 'strong', 'good', 'weak', or 'reject'.
3. Why: A brief, honest explanation of the fit and the gaps.
4. Track: Assign to one of the candidate's target tracks defined in their identity.
   If it doesn't fit any, use 'none'.

OUTPUT FORMAT:
Return ONLY a JSON array of objects matching this schema:
{{
  "id": "job_id",
  "score": integer,
  "verdict": "strong"|"good"|"weak"|"reject",
  "why": "reasoning",
  "track": "track_name"
}}
Ensure every job ID from the input is present.
"""

    # Call Claude CLI to do the judgment
    # ponytail: use subprocess to call claude, matching the daily_run.sh pattern
    try:
        p = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, check=True
        )
        result_text = p.stdout

        # Extract JSON from the response (handles cases where Claude adds markdown blocks)
        match = re.search(r"\[\s*\{.*\}\s*\]", result_text, re.S)
        if not match:
            raise RuntimeError("Claude did not return a valid JSON array")

        judgments = json.loads(match.group(0))

        # Merge judgments back into the template structure
        final_ranked = []
        judgment_map = {j["id"]: j for j in judgments}

        for j in jobs:
            res = judgment_map.get(j["id"], {"score": 0, "verdict": "reject", "why": "No judgment provided", "track": "none"})
            final_ranked.append({
                **j,
                "score": res.get("score"),
                "verdict": res.get("verdict"),
                "why": res.get("why"),
                "track": res.get("track"),
            })

        # Sort by score descending
        final_ranked.sort(key=lambda x: (x["score"] or 0), reverse=True)

        RANKED.write_text(json.dumps(final_ranked, indent=1, ensure_ascii=False) + "\n")
        print(f"Successfully judged {len(final_ranked)} jobs. Ranked results saved to {RANKED.name}")

    except Exception as e:
        print(f"Judgment failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import re # needed for the regex match
    judge_jobs()
