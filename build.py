#!/usr/bin/env python3
"""Render an application folder's HTML to PDF and verify it is submittable.

Usage:
  python3 build.py render <folder>    # cv.html + cover_letter.html -> PDF
  python3 build.py verify <queue>     # check every folder in applications/<date>/
  python3 build.py --selftest

The verify rules are the old pipeline's checklist, kept verbatim because each one
caught a real defect: a two-page CV, a surviving __PLACEHOLDER__, a stripped
stylesheet that let ligatures back in, a claim about German the candidate cannot make.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

from pypdf import PdfReader

HERE = pathlib.Path(__file__).resolve().parent
# Chrome renders the PDFs. Look in the usual places per platform, then fall back to
# anything on PATH, so a fork on Linux works without editing source.
# ponytail: a list and a loop, not a config key - there is one right answer per machine.
_CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "/snap/bin/chromium",
]


import os

def find_chrome():
    # 1. Check for explicit config in identity.local.json or env var
    config_path = os.environ.get("CHROME_PATH")
    if config_path and pathlib.Path(config_path).exists():
        return config_path

    try:
        id_cfg = json.loads(IDENTITY_FILE.read_text())
        id_chrome = id_cfg.get("chrome_path")
        if id_chrome and pathlib.Path(id_chrome).exists():
            return id_chrome
    except Exception:
        pass

    # 2. Fallback to usual places
    for c in _CHROME_CANDIDATES:
        if pathlib.Path(c).exists():
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


CHROME = find_chrome()
NEEDED = {"cv.html", "cv.pdf", "cover_letter.html", "cover_letter.pdf",
          "form_fields.txt", "posting.md", "fit.md"}

# Identity and the claims the candidate must never make live in identity.local.json,
# which is gitignored. Keeping them out of source is what lets this repo be pushed:
# contact details and biographical specifics never enter git history.
IDENTITY_FILE = HERE / "identity.local.json"


def identity():
    if not IDENTITY_FILE.exists():
        sys.exit(f"missing {IDENTITY_FILE.name} - copy identity.example.json and fill it in")
    return json.loads(IDENTITY_FILE.read_text())


ID = identity()
FORBIDDEN = [(rx, why) for rx, why in ID["forbidden_claims"]]


def render(folder):
    """HTML -> PDF via headless Chrome. 120s timeout, one retry: Chrome has
    self-updated mid-run before and hung a render indefinitely."""
    if not CHROME:
        sys.exit("no Chrome or Chromium found - install one, or add its path to "
                 "_CHROME_CANDIDATES in build.py")
    d = pathlib.Path(folder)
    for name in ("cv", "cover_letter"):
        src = d / f"{name}.html"
        if not src.exists():
            continue
        out = d / f"{name}.pdf"
        cmd = [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
               f"--print-to-pdf={out}", str(src)]
        for attempt in (1, 2):
            try:
                subprocess.run(cmd, capture_output=True, timeout=120, check=False)
                if out.exists() and out.stat().st_size > 1000:
                    print(f"  rendered {out.name} ({out.stat().st_size // 1024} KB)")
                    break
            except subprocess.TimeoutExpired:
                print(f"  ! render timed out (attempt {attempt}) for {src.name}",
                      file=sys.stderr)
        else:
            raise RuntimeError(f"could not render {src}")


def check(d):
    """Return a list of problems with one application folder. Empty list = clean."""
    problems = []
    missing = NEEDED - {f.name for f in d.iterdir()}
    if missing:
        problems.append("missing " + ", ".join(sorted(missing)))
    for name in ("cv", "cover_letter"):
        pdf = d / f"{name}.pdf"
        if not pdf.exists():
            continue
        r = PdfReader(pdf)
        text = "".join(p.extract_text() or "" for p in r.pages)
        images = sum(len(p.images) for p in r.pages)
        if len(r.pages) != 1:
            problems.append(f"{name}: {len(r.pages)} pages, must be 1")
        if "cid:" in text:
            problems.append(f"{name}: (cid: markers in text layer")
        if "�" in text:
            problems.append(f"{name}: replacement characters in text layer")
        if re.search(r"[ﬀ-ﬆ]", text):
            problems.append(f"{name}: ligatures - stylesheet damaged")
        for rx, why in FORBIDDEN:
            if re.search(rx, text):
                problems.append(f"{name}: {why}")
        if name == "cv":
            if ID["email"] not in text.replace(" ", ""):
                problems.append("cv: email not extractable as text")
            if ID["phone_digits"] not in re.sub(r"\D", "", text):
                problems.append("cv: phone not extractable as text")
            if images != 1:
                problems.append(f"cv: {images} images, expected 1 (profile photo)")
        elif images < 1:
            problems.append("cover_letter: signature image missing")
    return problems


def verify(queue):
    q = pathlib.Path(queue)
    bad = 0
    for d in sorted(p for p in q.iterdir() if p.is_dir() and not p.name.startswith("_")):
        problems = check(d)
        print(f"{d.name:52s} {'OK' if not problems else 'FAIL: ' + '; '.join(problems)}")
        bad |= bool(problems)
    print("\nCLEAN" if not bad else "\nISSUES FOUND")
    return 1 if bad else 0


def _selftest():
    """ponytail: the forbidden-claim rules must actually fire."""
    def hits(t):
        return [w for rx, w in FORBIDDEN if re.search(rx, t)]
    assert FORBIDDEN, "no forbidden-claim rules loaded from identity.local.json"
    assert hits("Dear __COMPANY__,"), "placeholder rule not firing"
    assert not hits("Python, C++, embedded C"), "false positive on ordinary skills text"
    for rx, _ in FORBIDDEN:
        re.compile(rx)  # every rule must be a valid regex
    print("selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "--selftest"
    if cmd == "--selftest":
        _selftest()
    elif cmd == "render":
        for folder in sys.argv[2:]:
            print(folder)
            render(folder)
    elif cmd == "verify":
        sys.exit(verify(sys.argv[2]))
    else:
        sys.exit(f"unknown command: {cmd}")
