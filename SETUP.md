# Setting this up for yourself

A fresh clone gives you a working **scraper and ranker** immediately. Getting the
**document drafting** working takes most of an afternoon, because everything that makes
it personal is deliberately not in this repository — no CV, no photo, no signature, no
contact details, no application history.

Budget: 10 minutes for steps 1–3, a couple of hours for steps 4–5, 10 minutes for step 6.

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
python3 scrape.py --selftest
python3 rank.py --selftest
```

Both should print `selftest ok`. `build.py --selftest` fails until step 2.

## 2. Identity

```bash
cp identity.example.json identity.local.json
```

Edit it. `identity.local.json` is gitignored and must stay that way — it holds your
email, phone and city.

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

```bash
python3 build.py --selftest     # now passes
```

## 3. Localise the search

Three places assume Munich. Change all three:

- **`queries.txt`** — one search query per line. The shipped set is German/Munich and
  Werkstudent-shaped. Rewrite for your market, language and role type.
- **`scrape.py`** — the `MUNICH` regex (the commute radius: city plus surrounding towns
  you'd accept) and the `location=` default in `fetch()` (a LinkedIn place string, e.g.
  `"Berlin, Germany"`, `"Greater London, United Kingdom"`).
- **`templates/cover_example.html`** and **`tools/make_app.py`** — the `Munich, __DATE__`
  dateline, and the local-language spelling swap.

Test:

```bash
python3 scrape.py queries.txt
python3 rank.py
```

You should see real postings ranked. This half now works.

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
| `cover_master.html` | `Application for __ROLE_TITLE__`, `Kind regards,`, `Munich, __DATE__` |

Redesign the styling freely; break an anchor and the build raises rather than silently
producing a wrong document.

Check your masters render and pass:

```bash
mkdir -p /tmp/t && cp templates/cv_master.html /tmp/t/cv.html
python3 build.py render /tmp/t
```

One page, your photo embedded, your email and phone extractable as text.

## 6. The daily schedule (optional)

The agent is useful run by hand — just type `/jobhunting` in Claude Code. If you want it
every morning:

```bash
cp tools/com.jobhunt.daily.plist.example ~/Library/LaunchAgents/com.jobhunt.daily.plist
# edit it: replace /Users/YOURNAME with your home directory
plutil -lint ~/Library/LaunchAgents/com.jobhunt.daily.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.jobhunt.daily.plist
launchctl list | grep jobhunt
```

It fires at login, with fallbacks at 08:57 / 13:13 / 18:41 for days the machine wakes
rather than boots. `applications/_logs/.last_run` enforces once per day, not launchd.

To stop it: `launchctl bootout gui/$(id -u)/com.jobhunt.daily`

Logs land in `applications/_logs/<date>.log`. A failed run leaves the day unstamped so a
later trigger retries.

> **Laptops sleep.** A full run needs 30–50 minutes awake. Runs here have died to sleep
> mid-draft. If that happens, wrap the `claude` call in `tools/daily_run.sh` with
> `caffeinate -i`.

---

## What you end up with

```
jobhunt/
  my_profile/              yours, gitignored     ← step 4
  templates/*_master.html  yours, gitignored     ← step 5
  identity.local.json      yours, gitignored     ← step 2
  tracker.csv              created on first run
  applications/<date>/     ten drafted applications per run
```

Everything personal stays on your machine. If you push your fork, check first:

```bash
git ls-files | xargs grep -l "your@email.com" ; echo "(no output = clean)"
```

## It never submits anything

The run stops at finished, verified documents. Filling and sending real application
forms happens with you at the keyboard. That boundary is Rule 1 in
`.claude/commands/jobhunting.md` — keep it.
