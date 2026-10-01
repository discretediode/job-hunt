# jobhunt

Manual job-hunt pipeline for Munich Werkstudent roles. **Runs only on `/jobhunting`.**
No launchd agent, no cron, no schedule — that is the point.

    /jobhunting            full run: scrape -> rank -> 10 drafted applications
    /jobhunting scrape     scrape and rank only
    /jobhunting embedded   bias the queries toward a focus
    /jobhunting draft 3    documents for entry 3 of the last ranked list

Nothing is ever submitted. The run stops at verified, review-ready documents.

## Setting it up for yourself

See **[SETUP.md](SETUP.md)**. A fresh clone scrapes and ranks immediately; drafting
needs your own profile vault, CV templates and `identity.local.json` — none of which
are in this repo, by design.

## Layout

    .claude/commands/jobhunting.md   the workflow (single source of truth)
    scrape.py                        LinkedIn jobs-guest -> seen.json, latest.json
    rank.py                          score vs profile -> ranked.json
    detail.sh <id>                   full description for one posting
    build.py                         render HTML->PDF, verify submittability
    queries.txt                      one search query per line
    templates/                       *_example.html tracked; your *_master.html gitignored
    tracker.csv                      application history (tracked in git)
    applications/<date>/             the drafted queue (gitignored)

## Profile

Read from the Obsidian vault at `my_profile/` — read-only, gitignored, never copied.
Two copies drift; one does not. Moved here from `~/Desktop/cv-automator` on
2026-09-30: macOS privacy protection blocks unattended reads of `~/Desktop`, which
would have broken the scheduled run.

## Checks

    python3 scrape.py --selftest
    python3 rank.py --selftest
    python3 build.py --selftest
    python3 build.py verify applications/<date>

## History

Supersedes the `ai-job-search` agent retired 2026-09-25. Its output is archived at
`~/job-applications-archive/` and its 40 tracker rows carried forward into `tracker.csv`.
