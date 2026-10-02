#!/usr/bin/env python3
"""Scrape LinkedIn's public jobs-guest endpoint for the roles in queries.txt.

Usage: python3 scrape.py queries.txt        # one query per line
Writes seen.json (dedup state), prints only jobs not seen before and not already
applied to per the archived tracker.

Location, commute radius and search window all come from identity.local.json's
"search" block - nothing about one particular city is hardcoded here.

ponytail: stdlib only, no bun, no portal CLIs. LinkedIn is the only source -
freehire's public /jobs endpoint ignores query params, so it returned noise.
Add a second source only if LinkedIn's yield drops.
"""
import html
import json
import pathlib
import re
import sys
import time
import urllib.parse
import subprocess
import datetime
import csv

HERE = pathlib.Path(__file__).resolve().parent
SEEN = HERE / "seen.json"
TRACKER = HERE / "tracker.csv"
TODAY = datetime.date.today().isoformat()
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

# Where the candidate will actually commute, from identity.local.json. A location
# outside it is a hard fail, so filter here rather than presenting it and making him
# reject it every morning.
_CONFIG_FILE = HERE / "identity.local.json"
if not _CONFIG_FILE.exists():
    sys.exit(f"missing {_CONFIG_FILE.name} - copy identity.example.json and fill it in")
CONFIG = json.loads(_CONFIG_FILE.read_text()).get("search")
if not CONFIG or not CONFIG.get("commute_towns"):
    sys.exit(f"{_CONFIG_FILE.name} needs a \"search\" block with commute_towns "
             "- see identity.example.json")


def _ascii(s):
    """Fold a location string to plain lowercase ascii so config towns can be written
    as ordinary words. LinkedIn returns both 'M&uuml;nchen' and percent-encoded forms,
    and nobody should have to spell 'unterschlei(ss|%C3%9F)heim' in a config file."""
    s = urllib.parse.unquote(s or "").lower()
    for a, b in (("\u00fc", "u"), ("\u00f6", "o"), ("\u00e4", "a"), ("\u00df", "ss"),
                 ("\u00e9", "e"), ("\u00e8", "e")):
        s = s.replace(a, b)
    return s


TOWNS = [_ascii(t) for t in CONFIG["commute_towns"]]


def in_range(location, towns=None):
    """True if this posting's location is somewhere the candidate would commute.

    `towns` is injectable so the selftest can assert on a fixed list rather than on
    whatever city this particular machine is configured for."""
    loc = _ascii(location)
    return bool(loc) and any(t in loc for t in (TOWNS if towns is None else towns))


TITLE = re.compile(r'<span class="sr-only">\s*(.*?)\s*</span>', re.S)
COMPANY = re.compile(r'hidden-nested-link[^>]*>\s*(.*?)\s*</a>', re.S)
PLACE = re.compile(r'job-search-card__location">\s*(.*?)\s*</span>', re.S)
WHEN = re.compile(r'datetime="([\d-]+)"')


def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def fetch(query, location=None, days=None, start=0):
    location = location or CONFIG["location"]
    days = days or CONFIG["window_days"]
    q = urllib.parse.urlencode({
        "keywords": query, "location": location,
        "f_TPR": f"r{days * 86400}", "start": start})
    # ponytail: curl, not urllib - this machine sits behind a TLS-intercepting proxy
    # whose self-signed root urllib rejects. curl uses the system trust store and works.
    p = subprocess.run(["curl", "-sSf", "--max-time", "30", "-A", UA, f"{API}?{q}"],
                       capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr.strip()[:120] or f"curl exit {p.returncode}")
    return p.stdout


def parse(page):
    out = []
    for chunk in page.split('data-entity-urn="urn:li:jobPosting:')[1:]:
        jid = chunk.split('"')[0]
        t = TITLE.search(chunk)
        c = COMPANY.search(chunk)
        p = PLACE.search(chunk)
        d = WHEN.search(chunk)
        out.append({
            "id": jid,
            "title": clean(t.group(1)) if t else None,
            "company": clean(c.group(1)) if c else None,
            "location": clean(p.group(1)) if p else None,
            "posted": d.group(1) if d else None,
            "url": f"https://www.linkedin.com/jobs/view/{jid}",
        })
    return out


def norm(s):
    """Squash to comparable form: 'CHECK24 Services GmbH' and 'CHECK24' must match.
    ponytail: prefix compare, not fuzzy matching - exact tuples already let three
    applied-to jobs through because the tracker spells companies more formally."""
    s = re.sub(r"\b(gmbh|ag|se|kg|co|deutschland|group|services|germany)\b", "",
               (s or "").lower())
    return re.sub(r"[^a-z0-9]", "", s)


def applied_companies():
    """Company+role already in the archived tracker - never show these again."""
    if not TRACKER.exists():
        return set()
    with open(TRACKER, newline="", encoding="utf-8") as f:
        return {(norm(r[1])[:8], norm(r[3])[:28])
                for r in csv.reader(f) if len(r) > 3}


def main(qfile):
    queries = [q.strip() for q in open(qfile, encoding="utf-8")
               if q.strip() and not q.startswith("#")]
    seen = json.loads(SEEN.read_text()) if SEEN.exists() else {}
    done = applied_companies()
    fresh = []

    for q in queries:
        try:
            results = parse(fetch(q))
        except Exception as e:                      # one bad query never kills the run
            print(f"  ! {q[:40]}: {e}", file=sys.stderr)
            continue
        new = 0
        for r in results:
            if r["id"] in seen:
                continue
            if not in_range(r["location"]):
                seen[r["id"]] = {"skipped": "location", "first_seen": TODAY}
                continue
            if (norm(r["company"])[:8], norm(r["title"])[:28]) in done:
                seen[r["id"]] = {"skipped": "applied", "first_seen": TODAY}
                continue
            r["first_seen"] = TODAY
            seen[r["id"]] = r
            fresh.append(r)
            new += 1
        print(f"{q[:48]:48s} {len(results):3d} hits, {new:2d} new")
        time.sleep(1.5)                             # be polite to a public endpoint

    SEEN.write_text(json.dumps(seen, indent=1, ensure_ascii=False))
    print(f"\n{len(fresh)} new jobs in range | {len(seen)} total tracked")
    json.dump(fresh, open(HERE / "latest.json", "w"), indent=1, ensure_ascii=False)


def _selftest():
    """ponytail: one check - the parser survives a real card, the filters bite."""
    page = ('data-entity-urn="urn:li:jobPosting:123"<span class="sr-only">\n Working Student '
            'AI &amp; Data </span><a class="hidden-nested-link">ACME GmbH</a>'
            '<span class="job-search-card__location">\n München, Bavaria </span>'
            '<time datetime="2026-09-25">')
    j = parse(page)[0]
    assert j["id"] == "123", j
    assert j["title"] == "Working Student AI & Data", j["title"]
    assert j["company"] == "ACME GmbH", j["company"]
    # Fixed town list: this must pass on a clean clone whatever city is configured.
    towns = ["munchen", "unterschleissheim"]
    assert in_range(j["location"], towns), j["location"]
    assert in_range("M%C3%BCnchen, Bayern", towns), "percent-encoded form must match"
    assert in_range("Unterschlei\u00dfheim", towns), "sz must fold to ss"
    assert in_range("M\u00dcNCHEN", towns), "case must not matter"
    assert not in_range("Berlin, Germany", towns)
    assert not in_range("Hamburg", towns)
    assert not in_range(None, towns) and not in_range("", towns)
    assert TOWNS, "commute_towns is empty - scrape would reject every posting"
    print("selftest ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
    else:
        main(sys.argv[1])
