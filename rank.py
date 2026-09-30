#!/usr/bin/env python3
"""Score latest.json against the candidate's actual skills. Prints high-to-low.

ponytail: keyword weights over title+company, not an LLM call per job. 122 jobs,
and the title carries most of the signal. Hand-check the top 15, which is where
a wrong score actually costs something.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

# What he can evidence, weighted by how strongly he can evidence it.
WEIGHTS = [
    # Built it, repeatedly, with artifacts to show
    (r"\bllm|rag\b|generative|agentic|ai.agent|prompt", 30),
    (r"\bai\b|\bki\b|artificial intel|künstliche intel|machine learning|\bml\b|deep learning", 24),
    (r"python", 24),
    (r"automat|automatis", 22),
    (r"data (science|analyt|engineer)|datenanalyse|data analyst", 20),
    # Degree + research-assistant work
    (r"messtechnik|messdaten|prüfstand|pruefstand|versuch|validierung|erprobung|testlabor", 20),
    (r"embedded|firmware|mikrocontroller|stm32|\bc\+\+|hardware.?nah", 20),
    (r"mechatronik|mechatronic|elektrotechnik|elektronik", 16),
    (r"elektrische? (antrieb|maschin)|antriebstechnik|hochvolt|batterie", 14),
    (r"regelungstechnik|steuerungstechnik|control system", 12),
    (r"computer vision|yolo|bildverarbeitung|perception", 14),
    (r"robotic|robotik|roboter", 10),
    # Adjacent, learnable, stated interest
    (r"software.?entwickl|software engineer|softwareentwicklung|developer|backend", 14),
    (r"fintech|banking|bank\b|kredit|payment|trading|finanz|finance|quantitative", 12),
    (r"power bi|dashboard|reporting|business intelligence|\bbi\b", 10),
    (r"digitalisierung|transformation|prozess", 10),
    (r"ci/cd|devops|docker|gitlab|kubernetes", 8),
    (r"consultant|consulting|solution engineer|customer success|technical sales", 6),
    (r"sql|snowflake|datenbank|database", 6),
    # Format fit
    (r"werkstudent|working student|studentische", 10),
    (r"intern\b|internship|praktik", 4),
]

# Things that genuinely do not fit him - subtract, don't hide.
PENALTIES = [
    (r"\bphd\b|ph\.d|doktorand|promotion", -45),
    (r"master thesis|masterarbeit|abschlussarbeit", -25),
    (r"steuer|tax\b|audit|wirtschaftsprüf|actuar|aktuariell", -30),
    (r"recht|legal|jurist|compliance|regulatory|governance|dora", -22),
    (r"marketing|sales\b|vertrieb|retail|account manage|hr\b|human resources|people & culture", -20),
    (r"\bseo\b|content|design(er)?\b|ux\b|grafik", -22),
    (r"pharmakov|klinisch|medizin|tribologie|kältetechnik|versorgungstechnik|gebäudetechnik", -18),
    (r"assistenz|team assist|projektassistenz|returns management|data labeling", -25),
    (r"senior|lead\b|principal|manager \(|head of", -20),
]


# Descriptions I actually fetched and read. Title keywords cannot see "requires 2+
# years" or "Master's only" or a body that matches far better than its bland title.
# ponytail: a dict of verified deltas beats a second scoring engine.
OVERRIDES = {
    "4471107882": (-60, "full-time, needs 2+ yrs experience - not a student role"),
    "4471111653": (-40, "same company, same full-time engineer track"),
    "4470099614": (+32, "body is the best match of the run: Python+Excel automation, AI agent rollout, prompts"),
    "4449564930": (+26, "automates measurement-data capture and evaluation - his SFRA work plus Python"),
    "4459960863": (+22, "hardware-near C on AUTOSAR plus automating dev processes with AI tools"),
    "4384875844": (+18, "names LLMs, ASR, RAG and embeddings into production"),
    "4467203459": (+16, "financial data into production, then automated analyses"),
    "4422909021": (+10, "ML+LLM+genAI on credit comparison; explicitly no finance expertise needed"),
    "4467199577": (+8, "requires experience with AI coding agents; Python accepted"),
    "4468227944": (+6, "agentic chat/voice QA, welcomes early-semester students"),
    "4469696510": (+6, "Python/Docker/GitLab, but wants Kubernetes and Jenkins migration"),
    "4470163540": (+5, "prototypes and automations for AI use cases; English sufficient"),
    "4467978408": (-12, "asks for Master's enrolment; he is mid-Bachelor"),
    "4438674690": (-22, "ausschliesslich Masterstudierende - hard gate"),
    "4461203694": (-12, "pure Power BI reporting, no Python, no build"),
    "4448143027": (-10, "audit consulting, and posted across Frankfurt/Hamburg/Munich"),
    # 2026-09-29 run
    "4470857822": (-40, "requires enrolment in a master's programme - hard gate"),
    "4470876723": (-30, "wants Psychologie digitaler Medien, not an engineering degree"),
    "4462294503": (-20, "German native/C2 required plus a business degree; he has neither"),
    "4471773622": (+22, "bland title: E/E architecture as code, Git, CI/CD validation, AI tooling in VS Code"),
    "4473072178": (+20, "body is prompt library and prompt engineering, not HR admin"),
    "4470876722": (-10, "additive-manufacturing project management, programming only a nice-to-have"),
}


def score(job):
    text = f"{job.get('title') or ''} {job.get('company') or ''}".lower()
    pts, hits = 0, []
    for rx, w in WEIGHTS:
        if re.search(rx, text):
            pts += w
            hits.append(rx.split("|")[0].strip("\\b"))
    for rx, w in PENALTIES:
        if re.search(rx, text):
            pts += w
            hits.append("-" + rx.split("|")[0].strip("\\b"))
    if job.get("id") in OVERRIDES:
        delta, why = OVERRIDES[job["id"]]
        pts += delta
        hits.append(f"VERIFIED: {why}")
    return pts, hits


def main():
    jobs = json.load(open(HERE / "latest.json"))
    for j in jobs:
        j["score"], j["hits"] = score(j)
    jobs.sort(key=lambda j: (-j["score"], str(j.get("posted"))))
    for i, j in enumerate(jobs, 1):
        print(f"{i:3d} | {j['score']:4d} | {str(j.get('posted'))[:10]} | "
              f"{str(j.get('company'))[:24]:24s} | {str(j.get('title'))[:62]:62s} | {j['id']}")
    json.dump(jobs, open(HERE / "ranked.json", "w"), indent=1, ensure_ascii=False)
    print(f"\n{len(jobs)} ranked")


def _selftest():
    """ponytail: the scorer must rank a core match above a penalised one."""
    good = {"title": "Werkstudent KI & Automatisierung Python", "company": "X"}
    meh = {"title": "Werkstudent Steuerberatung Tax", "company": "Y"}
    emb = {"title": "Werkstudent Embedded Messtechnik Prüfstand", "company": "Z"}
    assert score(good)[0] > score(meh)[0], (score(good), score(meh))
    assert score(emb)[0] > score(meh)[0]
    assert score(meh)[0] < 0, score(meh)
    print("selftest ok")


if __name__ == "__main__":
    _selftest() if len(sys.argv) > 1 and sys.argv[1] == "--selftest" else main()
