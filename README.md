# jobhunt

An agentic job-hunt pipeline. Every morning when you open the laptop, it scrapes new
postings, reads each one in full, judges it against your own profile, and leaves you a
folder of finished, verified CV and cover-letter PDFs.

**It never submits anything.** The run stops at review-ready documents. Filling real
application forms happens with you at the keyboard.

    /jobhunt              full run: scrape -> judge -> draft up to `max_per_day`
    /jobhunt scrape       scrape and judge only, no documents
    /jobhunt embedded     bias the queries toward a focus
    /jobhunt draft 3      documents for entry 3 of the last ranked list
    /jobhunt evidence     rebuild the evidence brief from documents/

Runs by hand in [Claude Code](https://claude.com/claude-code), or unattended at login
via launchd — see [SETUP.md](SETUP.md) step 6.

## How it works

Five small scripts do the mechanical work. Every act of judgment is the agent's.

```
launchd (login/boot, + 08:57 / 13:13 / 18:41 fallbacks)
  └─ tools/daily_run.sh              network probe, once-per-day stamp
       └─ claude -p "/jobhunt"
            ├─ scrape.py             LinkedIn jobs-guest -> seen.json, latest.json
            ├─ postings.py --bundle  full descriptions -> to_judge.md
            │    ▸ agent reads every description, writes ranked.json
            ├─ postings.py --check   validates that verdict file
            ├─ postings.py --archive postings -> QUEUE/<slug>/posting.md
            │    ▸ agent writes QUEUE/_tailoring.json
            ├─ tools/make_app.py     templates + tailoring -> cv.html, cover_letter.html
            ├─ build.py render       headless Chrome -> PDF
            ├─ build.py verify       13 mechanical checks, per document
            ├─ track.py add          one tracker row per drafted job
            └─ agent writes QUEUE/SUMMARY.md
```

**There is no keyword scorer.** An earlier version weighted title keywords and needed a
hand-maintained dict of 44 per-job corrections — keyed to job IDs that expire — to stay
honest, and it hardcoded one person's skills as numbers. It fetches the full
description and judges the body instead. That is also what makes this repo useful to
someone else: there are no weights to retune, only a vault to fill in.

**Rendering and verification stay deterministic, on purpose.** Nobody is awake at 09:00
to catch a regression, so the one-page check, the extractable-contact check and the
forbidden-claim check are Python, not judgment. See *Checks* below.

## Your information

Three inputs, none of them tracked in git:

| Where | What | Who writes it |
|---|---|---|
| `my_profile/` | Education, experience, skills, projects, language levels, letter voice | **you**, in Obsidian or any editor |
| `documents/` | Diplomas, language certificates, reference letters, transcripts | you, by dropping files in |
| `identity.local.json` | Contact details, forbidden claims, search config | you, once |

`documents/EVIDENCE.md` is the agent's reading of that paper — what each document *proves*, so
a cover letter can quote a reference letter's real wording instead of paraphrasing from
memory. Generated, gitignored, regenerable.

The vault is read **live, every run, and never summarised into a second file.** Two
copies drift, and the stale one is the one that ends up in a CV.

## Layout

    .claude/commands/jobhunt.md  the workflow - single source of truth, and the agent's brief
    setup.py                    first-run setup; --check reports profile gaps
    scrape.py                   LinkedIn jobs-guest -> seen.json, latest.json
    postings.py                 fetch / bundle / archive / check descriptions
    build.py                    render HTML->PDF, verify submittability
    track.py                    the application record: add / sent / set / list / stats
    tools/make_app.py           fill the templates from _tailoring.json
    tools/summarize_documents.py  documents/ -> EXTRACT.md for the agent to distil
    tools/daily_run.sh          the unattended wrapper launchd calls
    tools/install_schedule.sh   generate + load the launchd plist for THIS repo
    templates/                  *_example.html tracked; your *_master.html gitignored
    identity.local.json         contact details, forbidden claims, search config  (yours)
    queries.txt                 one search query per line                         (yours)
    my_profile/                 your profile vault                                (yours)
    documents/                  your diplomas and reference letters               (yours)
    tracker.csv                 application history                               (yours)
    applications/<date>/        the drafted queue                                 (yours)

## Checks

```bash
python3 setup.py --check                    # dependencies, config, profile gaps
python3 scrape.py --selftest
python3 postings.py --selftest
python3 build.py --selftest
python3 track.py --selftest
python3 tools/summarize_documents.py --selftest
python3 postings.py --check                 # after the agent writes ranked.json
python3 build.py verify applications/<date>
```

`build.py verify` is the one that matters. Per document: 7-file manifest · CV and letter
exactly one page · no `(cid:` markers, replacement characters or ligatures · no surviving
`__PLACEHOLDER__` · email and phone extractable as literal text · profile photo in the
CV, signature in the letter · no claim matching your `forbidden_claims`.

Every one of those rules is there because it caught a real defect once.

## Privacy

This repo is designed to be public with a private working copy. Nothing identifying is
tracked: not the vault, not the templates (they embed a photo and a handwritten
signature as base64), not `identity.local.json`, not `tracker.csv`, not the drafted
queues, not `documents/`. A pushed signature cannot be recalled.

Before you push a fork:

```bash
git ls-files -z | xargs -0 grep -ril "your.email@example.com"   # expect no output
```

## Tracking what you sent

The pipeline only ever writes `drafted`. Moving a row past that is yours, because only
you know what actually went out:

```bash
python3 track.py stats                 # counts by status, and how many never went out
python3 track.py list drafted          # what is staged and unsent
python3 track.py sent <slug>           # you sent it
python3 track.py set interview <slug>  # or rejected / offer / withdrawn / ghosted
```

`tracker.csv` is also the deduplication source — `scrape.py` reads it so a company and
role you have already applied to never resurfaces.

## Setting it up

```bash
python3 setup.py          # dependencies, config, queries, vault scaffold
python3 setup.py --check  # until it reports a complete profile
```

See **[SETUP.md](SETUP.md)** for the detail. A fresh clone scrapes and judges immediately; drafting
needs your own profile vault, CV templates and `identity.local.json` — none of which are
in this repo, by design.

## History

Supersedes the `ai-job-search` agent retired 2026-09-25 and the `/jobhunting` command it
replaced. `rank.py`, `detail.sh` and `tools/fetch_postings.py` were folded into
`postings.py` and the agent's own judgment.
