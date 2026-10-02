#!/usr/bin/env python3
"""The application record. Every job this repo has drafted, sent, or heard back on.

  python3 track.py add <queue> [spec-file]   append this run's drafted rows
  python3 track.py sent <slug> [...]         mark as actually sent
  python3 track.py set <status> <slug> [...] any other status change
  python3 track.py list [status]             show the pipeline, newest first
  python3 track.py stats                     counts by status
  python3 track.py --selftest

tracker.csv is the permanent record and the deduplication source: scrape.py reads it so
a company+role already applied to never resurfaces. It is gitignored - it names every
employer approached and the weaknesses stated to them.

ponytail: csv module, one file, no database. A few hundred rows will never need more,
and a CSV is something the candidate can open in Numbers and fix by hand. csv.writer
does the quoting, so a comma or a quote inside a note cannot shift the columns.
"""
import csv
import datetime
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TRACKER = HERE / "tracker.csv"
TODAY = datetime.date.today().isoformat()

COLUMNS = ["date", "company", "sector", "role", "role_type", "channel", "status",
           "contact_person", "fit_rating", "notes", "cv_file", "cover_letter_file",
           "source", "deadline", "status_date"]

# drafted is where every row starts; the rest are things only the candidate can confirm.
# "applied" is the retired ai-job-search agent's word for sent - 10 archived rows carry
# it, so it stays recognised rather than showing up as an unknown status.
STATUSES = ["drafted", "sent", "applied", "acknowledged", "interview", "offer",
            "rejected", "withdrawn", "ghosted"]
SENT_LIKE = {"sent", "applied", "acknowledged", "interview", "offer", "rejected", "ghosted"}

I_DATE, I_COMPANY, I_ROLE = 0, 1, 3
I_STATUS, I_CV = 6, 10
I_STATUS_DATE = 14


def read():
    """Rows as lists, padded to COLUMNS width. Old 14-column rows load fine."""
    if not TRACKER.exists():
        return []
    with TRACKER.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.reader(f) if r]
    return [r + [""] * (len(COLUMNS) - len(r)) if len(r) < len(COLUMNS) else r
            for r in rows]


def write(rows):
    with TRACKER.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


def has_header(rows):
    return bool(rows) and rows[0][:2] == ["date", "company"]


def add(queue, spec_file=None):
    """Append one drafted row per job in the queue's tailoring spec.

    Pulls score/verdict/why from ranked.json so the agent does not have to restate
    them, and skips a job already recorded for this date - running twice is harmless.
    """
    q = pathlib.Path(queue)
    spec_path = pathlib.Path(spec_file) if spec_file else q / "_tailoring.json"
    specs = json.loads(spec_path.read_text())
    ranked = {j["id"]: j for j in
              json.loads((HERE / "ranked.json").read_text())} if (HERE / "ranked.json").exists() else {}

    rows = read()
    existing = {(r[I_DATE], r[I_COMPANY], r[I_ROLE]) for r in rows}
    added = 0
    for s in specs:
        r = ranked.get(s.get("id"), {})
        key = (TODAY, s["company"], s["role"])
        if key in existing:
            print(f"  skip  {s['slug']} (already recorded today)")
            continue
        fit = f"{r.get('score', '')} - {r.get('verdict', '')}".strip(" -")
        rows.append([
            TODAY, s["company"], s.get("sector", ""), s["role"],
            s.get("role_type", "working student"), s.get("channel", "LinkedIn"),
            "drafted", s.get("contact_person", ""), fit,
            s.get("notes") or r.get("why", ""),
            f"{queue}/{s['slug']}/cv.pdf", f"{queue}/{s['slug']}/cover_letter.pdf",
            s.get("source", "linkedin-search"), s.get("deadline", ""), TODAY,
        ])
        existing.add(key)
        added += 1
        print(f"  add   {s['slug']}")
    write(rows)
    print(f"\n{added} added, {len(rows) - (1 if has_header(rows) else 0)} rows total")


def set_status(status, slugs):
    if status not in STATUSES:
        sys.exit(f"unknown status {status!r} - one of: {', '.join(STATUSES)}")
    rows = read()
    hit = 0
    for r in rows:
        if any(s in r[I_CV] for s in slugs):
            was = r[I_STATUS]
            r[I_STATUS], r[I_STATUS_DATE] = status, TODAY
            print(f"  {r[I_COMPANY]:28s} {was} -> {status}")
            hit += 1
    if not hit:
        sys.exit(f"no row matched: {', '.join(slugs)}\n"
                 "(match is on the slug inside the cv_file column; try 'list')")
    write(rows)
    print(f"\n{hit} updated")


def listing(status=None):
    rows = [r for r in read() if r[I_DATE] != "date"]
    if status:
        rows = [r for r in rows if r[I_STATUS] == status]
    for r in sorted(rows, key=lambda r: r[I_DATE], reverse=True):
        slug = pathlib.Path(r[I_CV]).parent.name if r[I_CV] else ""
        print(f"{r[I_DATE]}  {r[I_STATUS]:13s} {r[I_COMPANY][:26]:26s} "
              f"{r[I_ROLE][:44]:44s} {slug}")
    print(f"\n{len(rows)} row{'s' if len(rows) != 1 else ''}"
          + (f" with status {status}" if status else ""))


def stats():
    rows = [r for r in read() if r[I_DATE] != "date"]
    counts = {}
    for r in rows:
        counts[r[I_STATUS] or "(blank)"] = counts.get(r[I_STATUS] or "(blank)", 0) + 1
    width = max((len(s) for s in counts), default=10)
    for s in STATUSES + [k for k in counts if k not in STATUSES]:
        if s in counts:
            print(f"  {s:{width}s}  {counts[s]:4d}")
    print(f"  {'TOTAL':{width}s}  {len(rows):4d}")
    sent = sum(counts.get(s, 0) for s in SENT_LIKE)
    if rows:
        print(f"\n{counts.get('drafted', 0)} drafted but never sent "
              f"({100 * counts.get('drafted', 0) // len(rows)}% of the record).")
        if sent:
            print(f"{sent} actually went out.")


def _selftest():
    """ponytail: the two things that can silently corrupt the record - a short legacy
    row, and a note containing a comma - must both survive a read/write round trip."""
    import io, tempfile
    legacy = ["2026-01-01", "ACME GmbH", "sector", "Working Student AI", "working student",
              "LinkedIn", "drafted", "", "42 - strong",
              'Note with, a comma and "quotes"', "applications/x/a/cv.pdf",
              "applications/x/a/cover_letter.pdf", "linkedin-search", ""]   # 14 cols
    buf = io.StringIO()
    csv.writer(buf).writerow(legacy)
    back = next(csv.reader(io.StringIO(buf.getvalue())))
    assert back == legacy, back
    padded = back + [""] * (len(COLUMNS) - len(back))
    assert len(padded) == 15, len(padded)
    assert padded[I_STATUS] == "drafted" and padded[I_COMPANY] == "ACME GmbH"
    assert padded[I_STATUS_DATE] == ""
    assert "comma" in padded[9] and '"quotes"' in padded[9], padded[9]
    assert len(COLUMNS) == 15 and COLUMNS[I_STATUS] == "status"
    assert COLUMNS[I_CV] == "cv_file" and COLUMNS[I_STATUS_DATE] == "status_date"
    assert "drafted" in STATUSES and "sent" in STATUSES
    assert "applied" in STATUSES, "the archived agent's status must stay recognised"
    assert "drafted" not in SENT_LIKE and "sent" in SENT_LIKE
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:] or ["--selftest"]
    cmd = a[0]
    if cmd == "--selftest":
        _selftest()
    elif cmd == "add":
        add(a[1], a[2] if len(a) > 2 else None)
    elif cmd == "sent":
        set_status("sent", a[1:])
    elif cmd == "set":
        set_status(a[1], a[2:])
    elif cmd == "list":
        listing(a[1] if len(a) > 1 else None)
    elif cmd == "stats":
        stats()
    else:
        sys.exit(__doc__)
