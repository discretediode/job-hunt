# Setting this up for yourself

## Quick start

```bash
python3 setup.py           # checks dependencies, writes your config, scaffolds the vault
python3 setup.py --check   # re-run until it reports a complete profile
```

`setup.py` walks you through steps 1–4 below and tells you what is still missing or
ambiguous. The manual detail for each step follows, for when you want to know what it
did or would rather do it yourself.

---

A fresh clone gives you a working **scraper and judge** immediately. Getting the
**document drafting** working takes an hour or two, because everything that makes it
personal is deliberately not in this repository — no CV, no photo, no signature, no
contact details, no application history.

You never edit Python to make this yours. Everything that varies between people lives in
`identity.local.json` and `queries.txt`, both gitignored.

Budget: 15 minutes for steps 1–3, an hour or two for steps 4–5, 10 minutes for step 6.

---

## 1. Dependencies

| Need | Check | Get it |
|---|---|---|
| Python 3.9+ | `python3 --version` | preinstalled on macOS |
| pypdf | `python3 -c "import pypdf"` | `pip3 install pypdf` |
| Google Chrome | `ls "/Applications/Google Chrome.app"` | renders HTML to PDF |
| Claude Code | `claude --version` | the agent that does the writing |
| curl | `curl --version` | preinstalled |

No Node, no bun, no API keys, no scraping libraries.

Verify:

```bash
python3 postings.py --selftest
python3 tools/summarize_documents.py --selftest
```

Both should print `selftest ok`. `scrape.py --selftest` and `build.py --selftest` fail
until step 2 — they read `identity.local.json`.

## 2. Identity

```bash
cp identity.example.json identity.local.json
```

Edit it. `identity.local.json` is gitignored and must stay that way — it holds your
email, phone and city, and it is the only configuration file in the project.

- `email` and `phone_digits` are what `build.py` looks for in every rendered PDF. If
  they don't appear as selectable text, verification fails — which is the point: a CV
  whose contact details are trapped inside an image is unreachable by a recruiter.
- `forbidden_claims` is a list of `[regex, why]`. These are matched against every PDF
  and a hit **fails the build**. Keep the `__[A-Z0-9_]+__` rule. Replace the rest with
  the overstatements *you* must never make: a language level above what you can
  evidence, a qualification you don't hold, a project described as finished when it isn't.

  This is the single most valuable thing in the repo. An unattended agent writing
  flattering prose at 09:00 will drift toward overstatement unless something mechanical
  stops it.

The `search` block in the same file is the whole of your localisation:

| Key | What it does |
|---|---|
| `location` | A LinkedIn place string, passed straight to the search endpoint — `"Berlin, Germany"`, `"Greater London, United Kingdom"` |
| `commute_towns` | Your city plus every town you'd actually commute to. Plain lowercase, umlauts written out. A posting matching none of these is filtered at the source |
| `role_type`, `out_of_scope` | What kind of post you want, and what to reject outright |
| `max_per_day` | How many applications to draft per run. Fewer is always allowed; the run never pads |
| `window_days` | How far back to search |
| `cv_language`, `letter_language` | `"en"`, and `"match_posting"` to answer in the posting's own language |

```bash
python3 build.py --selftest      # now passes
python3 scrape.py --selftest     # now passes
```

## 3. Your search queries

```bash
cp queries.example.txt queries.txt
```

One query per line, written the way you'd type them into LinkedIn's search box, in the
language the postings are in. Gitignored — your target market is nobody else's business.

A broad query that returns some noise costs little, because every new hit gets its full
description fetched and judged. A query for work you *cannot evidence* costs you a
morning of reading rejections.

Test:

```bash
python3 scrape.py queries.txt
python3 postings.py --bundle
```

You should get real postings in `latest.json` and their full descriptions in
`to_judge.md`. This half now works — the judging itself happens inside a `/jobhunt` run.

## 4. Your profile vault

Create `my_profile/` with these filenames — the workflow refers to them by name:

```
my_profile/
  personal_info.md              name, address, contact, links
  education.md                  degrees, institutions, dates, grades
  experiences.md                jobs, with what you actually did
  projects.md                   what you built, the stack, the decisions
  skills.md                     technical skills AND declared language levels
  extracullicular_activities.md societies, volunteering, anything else real
  guidelines_for_anschreiben.md how your cover letters should sound
```

Plain Markdown. It happens to be an Obsidian vault, but nothing requires Obsidian.

Two rules:

- **`skills.md` is the authority on your language levels.** The agent is told never to
  claim above what it declares. Be accurate, not optimistic.
- **Keep one copy.** It's gitignored and read-only to the agent. If you keep a second
  copy elsewhere and edit that one, your CV will quietly go stale.

> **macOS:** don't put this under `~/Desktop` or `~/Documents`. Those are privacy-protected,
> and a scheduled background run cannot read them — it fails at 09:00 with nobody watching.
> This repo's own vault was moved out of `~/Desktop` for exactly that reason.

## 4b. Your documents (optional, recommended)

Drop the actual paper into `documents/` — diplomas, language certificates, reference
letters, transcripts, any externally-authored CV:

```
documents/
  diplomas/      school-leaving and language qualifications
  references/    reference letters from past employers
  cv/            any externally-authored CV versions
  postings/      saved job adverts
```

Then, inside Claude Code: `/jobhunt evidence`

That runs `tools/summarize_documents.py` to pull the text out of anything machine-readable,
reads any scan or photo directly, and writes `documents/EVIDENCE.md` — one entry per
document saying what it *proves*. Cover letters then quote a reference letter's real
wording instead of paraphrasing it from memory.

All of `documents/` is gitignored, including both derived files. A transcript and a
reference letter are more personal than anything else in this repo.

## 5. Your CV and cover-letter templates

```bash
cp templates/cv_example.html    templates/cv_master.html
cp templates/cover_example.html templates/cover_master.html
```

Both masters are gitignored. Replace everything in `[SQUARE BRACKETS]` with your own
details, and swap the grey placeholder images for your photo and signature as base64
data URIs — the command is in a comment in each file.

**Keep the anchors.** `tools/make_app.py` finds its edit points by literal match:

| File | Must contain |
|---|---|
| `cv_master.html` | `<p class="tagline">…</p>` and `<h2>Profile</h2><p class="tight">…</p>` |
| `cover_master.html` | `Application for __ROLE_TITLE__`, `Kind regards,`, `<p class="date">__DATELINE__</p>` |

Redesign the styling freely; break an anchor and the build raises rather than silently
producing a wrong document.

Check your masters render and pass:

```bash
mkdir -p /tmp/t && cp templates/cv_master.html /tmp/t/cv.html
python3 build.py render /tmp/t
```

One page, your photo embedded, your email and phone extractable as text.

## 6. The daily schedule (optional)

The agent is useful run by hand — just type `/jobhunt` in Claude Code. If you want it every
morning:

```bash
bash tools/install_schedule.sh
```

That generates the plist from wherever this repo actually lives and loads it. There is
no path to hand-edit — an earlier version shipped a `/Users/YOURNAME` placeholder, and
the day the directory was renamed every scheduled run broke silently, because launchd
had no reason to tell anyone.

It fires at login, with fallbacks at 08:57 / 13:13 / 18:41 for days the machine wakes
rather than boots. `applications/_logs/.last_run` enforces once per day, not launchd.

To stop it: `bash tools/install_schedule.sh --uninstall`

Logs land in `applications/_logs/<date>.log`. A failed run leaves the day unstamped so a
later trigger retries.

> **Laptops sleep.** A full run needs 30–50 minutes awake. Runs here have died to sleep
> mid-draft. If that happens, wrap the `claude` call in `tools/daily_run.sh` with
> `caffeinate -i`.

---

## What you end up with

```
job-hunt/
  identity.local.json      yours, gitignored     ← step 2
  queries.txt              yours, gitignored     ← step 3
  my_profile/              yours, gitignored     ← step 4
  documents/               yours, gitignored     ← step 4b
  templates/*_master.html  yours, gitignored     ← step 5
  tracker.csv              created on first run
  applications/<date>/     the drafted queue, one folder per run
```

Everything personal stays on your machine. If you push your fork, check first:

```bash
git ls-files | xargs grep -l "your@email.com" ; echo "(no output = clean)"
```

## It never submits anything

The run stops at finished, verified documents. Filling and sending real application
forms happens with you at the keyboard. That boundary is Rule 1 in
`.claude/commands/jobhunt.md` — keep it.
