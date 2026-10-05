#!/usr/bin/env python3
"""First-run setup. Gets a fresh clone from nothing to a working profile.

  python3 setup.py           interactive: dependencies, config, queries, vault
  python3 setup.py --check   non-interactive: report what is missing or ambiguous
  python3 setup.py --selftest

Everything personal is created here and gitignored. Nothing this writes is ever
committed.

The --check pass is the one that matters after day one: it is what the agent runs
before drafting, so an ambiguous profile becomes a question asked rather than a
confident guess printed onto a PDF.

ponytail: input() and pathlib, no questionary, no rich, no yaml. A setup script that
needs its own dependency tree to install dependencies is a joke.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CONFIG = HERE / "identity.local.json"
EXAMPLE = HERE / "identity.example.json"
QUERIES = HERE / "queries.txt"
QUERIES_EXAMPLE = HERE / "queries.example.txt"
VAULT = HERE / "my_profile"
DOCS = HERE / "documents"

VAULT_FILES = {
    "personal_info.md": "Name, city, contact, links. The CV header comes from here.",
    "education.md": "Degrees, institutions, dates, grades. Degree LEVEL gates many postings.",
    "experiences.md": "Jobs, with what you actually did - not the job description.",
    "projects.md": "What you built, the stack, the decisions you made and why.",
    "skills.md": "Technical skills AND declared language levels. The authority on both.",
    "extracullicular_activities.md": "Societies, volunteering, anything else real.",
    "guidelines_for_anschreiben.md": "How your cover letters should sound, in your voice.",
}

DOC_DIRS = ["diplomas", "references", "cv", "postings"]

# Core files: without these the agent has nothing truthful to write a CV from.
CORE = {"skills.md", "education.md", "experiences.md"}


def substance(text):
    """What is left after headings and HTML comments - i.e. what the candidate wrote.

    scaffold() writes an 80-90 character stub per file: a heading plus a comment saying
    what belongs there. Measuring raw length counted those as content, so a completely
    unfilled vault passed --check with exit 0 - the exact opposite of the guarantee the
    blocker/ask split is supposed to give.
    """
    t = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    t = re.sub(r"^\s{0,3}#.*$", "", t, flags=re.M)
    return t.strip()


# ─────────────────────────────── checks ───────────────────────────────

def deps():
    """[(name, ok, how_to_fix)] for every external thing the pipeline shells out to."""
    out = []
    out.append(("python3 >= 3.9", sys.version_info >= (3, 9), "install a newer Python"))
    try:
        import pypdf  # noqa: F401
        out.append(("pypdf", True, ""))
    except ImportError:
        out.append(("pypdf", False, "pip3 install pypdf"))
    out.append(("curl", bool(shutil.which("curl")), "install curl"))
    try:
        sys.path.insert(0, str(HERE))
        import build
        out.append(("Chrome/Chromium", bool(build.CHROME),
                    "install Google Chrome - it renders the PDFs"))
    except Exception as e:
        out.append(("Chrome/Chromium", False, f"could not probe: {e}"))
    out.append(("claude CLI", bool(shutil.which("claude")),
                "install Claude Code - it is the agent that does the writing"))
    return out


def profile_gaps():
    """Everything that would make the agent guess. [(severity, where, what)].

    'blocker' means drafting cannot proceed honestly. 'ask' means the agent should put
    the question to the candidate before writing a claim that depends on it.
    """
    gaps = []

    if not CONFIG.exists():
        gaps.append(("blocker", "identity.local.json",
                     "missing - run setup.py, or copy identity.example.json"))
        return gaps

    try:
        cfg = json.loads(CONFIG.read_text())
    except json.JSONDecodeError as e:
        gaps.append(("blocker", "identity.local.json", f"is not valid JSON: {e}"))
        return gaps

    for key in ("email", "phone_digits", "postcode_city_en", "postcode_city_local"):
        v = str(cfg.get(key, "")).strip()
        if not v or "example" in v.lower() or "YOURNAME" in v:
            gaps.append(("blocker", f"identity.local.json:{key}",
                         "still empty or still the example value"))
    if not cfg.get("forbidden_claims"):
        gaps.append(("blocker", "identity.local.json:forbidden_claims",
                     "empty - this is the guard that stops an unattended run overstating"))
    else:
        if not any(r[0] == r"__[A-Z0-9_]+__" for r in cfg["forbidden_claims"]):
            gaps.append(("ask", "identity.local.json:forbidden_claims",
                         "the __PLACEHOLDER__ rule was removed - that is the last guard "
                         "against mailing a template"))
        if any("EXAMPLE" in (r[1] or "") for r in cfg["forbidden_claims"]):
            gaps.append(("ask", "identity.local.json:forbidden_claims",
                         "still contains EXAMPLE rules - replace them with the "
                         "overstatements YOU must never make"))

    s = cfg.get("search") or {}
    if not s:
        gaps.append(("blocker", "identity.local.json:search", "missing search block"))
    else:
        if not s.get("commute_towns"):
            gaps.append(("blocker", "identity.local.json:search.commute_towns",
                         "empty - every posting would be filtered out"))
        if not s.get("location"):
            gaps.append(("blocker", "identity.local.json:search.location", "empty"))
        if not s.get("role_type"):
            gaps.append(("ask", "identity.local.json:search.role_type",
                         "what kind of post do you actually want?"))

    if not QUERIES.exists():
        gaps.append(("blocker", "queries.txt", "missing - copy queries.example.txt"))
    elif not [l for l in QUERIES.read_text().splitlines()
              if l.strip() and not l.startswith("#")]:
        gaps.append(("blocker", "queries.txt", "no queries, only comments"))

    if not VAULT.exists():
        gaps.append(("blocker", "my_profile/", "missing - the agent has nothing to write from"))
        return gaps

    for name, why in VAULT_FILES.items():
        f = VAULT / name
        sev = "blocker" if name in CORE else "ask"
        if not f.exists():
            gaps.append((sev, f"my_profile/{name}", f"missing. {why}"))
        elif len(substance(f.read_text())) < 40:
            gaps.append((sev, f"my_profile/{name}",
                         f"still the empty scaffold - nothing written in it yet. {why}"))

    skills = VAULT / "skills.md"
    if skills.exists() and len(substance(skills.read_text())) >= 40:
        text = substance(skills.read_text())
        low = text.lower()
        if "language" not in low and "sprache" not in low:
            gaps.append(("blocker", "my_profile/skills.md",
                         "declares no languages. The agent is forbidden from claiming a "
                         "level above what this file states, so with none stated it "
                         "cannot claim any - and most postings ask."))
        elif not any(lv in text for lv in
                     ("A1", "A2", "B1", "B2", "C1", "C2", "Native", "native",
                      "Muttersprache", "Fluent", "fluent")):
            gaps.append(("ask", "my_profile/skills.md",
                         "languages are listed without levels. Which level for each? "
                         "Postings state a bar and the agent must not guess over it."))

    for name in ("templates/cv_master.html", "templates/cover_master.html"):
        if not (HERE / name).exists():
            gaps.append(("blocker", name,
                         f"missing - copy {name.replace('_master', '_example')} and "
                         "put your own details in it"))

    if DOCS.exists():
        real = [p for p in DOCS.rglob("*") if p.is_file()
                and p.name not in (".DS_Store", ".gitkeep", "README.md",
                                   "EXTRACT.md", "EVIDENCE.md")]
        if real and not (DOCS / "EVIDENCE.md").exists():
            gaps.append(("ask", "documents/EVIDENCE.md",
                         f"{len(real)} document(s) present but never read. Run `/jobhunt evidence`."))
    return gaps


# ─────────────────────────────── interactive ───────────────────────────────

def ask(prompt, default=""):
    d = f" [{default}]" if default else ""
    try:
        got = input(f"  {prompt}{d}: ").strip()
    except EOFError:
        return default
    return got or default


def make_config():
    if CONFIG.exists():
        print(f"\n{CONFIG.name} already exists - leaving it alone.")
        return
    print("\n── Your details ──")
    print("  These go into every CV and are checked for in every rendered PDF.")
    cfg = json.loads(EXAMPLE.read_text())
    cfg["email"] = ask("Email")
    cfg["phone_digits"] = "".join(c for c in ask("Phone (any format)") if c.isdigit())
    city_en = ask("Postcode and city, in English", "City, Country")
    cfg["postcode_city_en"] = city_en
    cfg["postcode_city_local"] = ask("The same, spelled locally", city_en)

    print("\n── Where you will work ──")
    cfg["search"]["location"] = ask("Search location (a LinkedIn place string)",
                                    cfg["search"]["location"])
    towns = ask("Towns you would commute to, comma-separated, plain lowercase",
                ", ".join(cfg["search"]["commute_towns"]))
    cfg["search"]["commute_towns"] = [t.strip().lower() for t in towns.split(",") if t.strip()]
    cfg["search"]["role_type"] = ask("Role type", cfg["search"]["role_type"])
    cfg["search"]["max_per_day"] = int(ask("Max applications to draft per day",
                                           str(cfg["search"]["max_per_day"])) or 10)

    print("\n── What you must never claim ──")
    print("  The guard that stops an unattended run from overstating. The __PLACEHOLDER__")
    print("  rule is kept automatically. Add your own: a language level above what you can")
    print("  evidence, a certificate you do not hold. Blank line to finish.")
    keep = [r for r in cfg["forbidden_claims"] if r[0] == r"__[A-Z0-9_]+__"]
    while True:
        rx = ask("Regex (blank to finish)")
        if not rx:
            break
        keep.append([rx, ask("  Why it is forbidden") or "overstatement"])
    cfg["forbidden_claims"] = keep
    CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    print(f"\n  wrote {CONFIG.name}  (gitignored)")


def scaffold():
    if not QUERIES.exists() and QUERIES_EXAMPLE.exists():
        QUERIES.write_text(QUERIES_EXAMPLE.read_text())
        print(f"  wrote {QUERIES.name} from the example - edit it for your market")
    VAULT.mkdir(exist_ok=True)
    for name, why in VAULT_FILES.items():
        f = VAULT / name
        if not f.exists():
            f.write_text(f"# {name[:-3].replace('_', ' ').title()}\n\n<!-- {why} -->\n")
            print(f"  created my_profile/{name}")
    for d in DOC_DIRS:
        (DOCS / d).mkdir(parents=True, exist_ok=True)
    print(f"  ensured documents/{{{','.join(DOC_DIRS)}}}/")


def report(gaps):
    blockers = [g for g in gaps if g[0] == "blocker"]
    asks = [g for g in gaps if g[0] == "ask"]
    if blockers:
        print("\nBLOCKERS - drafting cannot proceed honestly until these are fixed:")
        for _, where, what in blockers:
            print(f"  ✗ {where}\n      {what}")
    if asks:
        print("\nAMBIGUOUS - the agent should ask you about these before writing:")
        for _, where, what in asks:
            print(f"  ? {where}\n      {what}")
    if not gaps:
        print("\n  Profile complete. Nothing ambiguous.")
    return 1 if blockers else 0


def main():
    print("jobhunt - setup\n" + "=" * 52)
    print("\n── Dependencies ──")
    bad = 0
    for name, ok, fix in deps():
        print(f"  {'ok ' if ok else 'MISSING'}  {name}" + (f"   → {fix}" if not ok else ""))
        bad += not ok
    if bad:
        print(f"\n  {bad} missing. Install them, then run setup.py again.")

    if not CONFIG.exists():
        make_config()
    print("\n── Scaffolding ──")
    scaffold()

    print("\n── Profile check ──")
    rc = report(profile_gaps())
    print("\nNext:")
    print("  1. Fill in my_profile/*.md - that is where every CV sentence comes from.")
    print("  2. cp templates/cv_example.html templates/cv_master.html   (and cover_)")
    print("     then put your own details, photo and signature in them.")
    print("  3. Drop diplomas and reference letters into documents/, then run `/jobhunt evidence`.")
    print("  4. python3 setup.py --check      until it is clean")
    print("  5. /jobhunt                      in Claude Code")
    print("  6. bash tools/install_schedule.sh   to run it every morning (optional)")
    return rc


def _selftest():
    """ponytail: the gap checker must distinguish blockers from questions, and must
    never pass a profile that declares no language levels."""
    sev = {g[0] for g in profile_gaps()}
    assert sev <= {"blocker", "ask"}, sev
    assert set(VAULT_FILES) >= {"skills.md", "education.md", "experiences.md"}
    assert all(isinstance(v, str) and v for v in VAULT_FILES.values())
    assert all(isinstance(w, str) and w for _, w, _ in profile_gaps())
    # The scaffold stub must never read as filled-in content.
    stub = "# Skills\n\n<!-- Technical skills AND declared language levels. -->\n"
    assert len(stub) > 40, "stub is long enough to have fooled a raw length check"
    assert len(substance(stub)) < 40, substance(stub)
    assert len(substance("# Skills\n\n* Python, C/C++\n\n## Languages\n"
                         "* German: C1\n* English: C2\n")) >= 40
    assert CORE <= set(VAULT_FILES)
    for name, ok, fix in deps():
        assert isinstance(ok, bool) and (ok or fix), (name, ok, fix)
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--selftest":
        _selftest()
    elif a and a[0] == "--check":
        sys.exit(report(profile_gaps()))
    else:
        sys.exit(main())
