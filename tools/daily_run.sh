#!/bin/bash
# Unattended daily run for Bob. Fired by launchd at login/boot, with three calendar
# safety nets for the laptop-that-sleeps case. Runs /bob once per day; the
# date stamp below is what enforces "once", not launchd.
#
# Reconstructed 2026-09-29 to match the retired ai-job-search wrapper: same
# once-per-day stamp, same log lines, same per-day log file.

set -uo pipefail

# Derive the repo from this script's own location. Hardcoding an absolute path cost a
# day once already: the directory was renamed and every scheduled run broke silently,
# because launchd had no reason to tell anyone. This also lets a fork live anywhere.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGDIR="$REPO/applications/_logs"
STAMP="$LOGDIR/.last_run"
TODAY="$(date +%F)"
LOG="$LOGDIR/$TODAY.log"

mkdir -p "$LOGDIR"

# Once per day. Repeated logins and the three calendar fallbacks all land here and
# exit immediately once the day has run.
if [[ -f "$STAMP" && "$(cat "$STAMP")" == "$TODAY" ]]; then
  echo "$(date): already ran today ($TODAY), skipping" >> "$LOG"
  exit 0
fi

# Wait for a network, then REFUSE to run without one. Two failures on 2026-10-01
# came from this block: it probed https://www.linkedin.com, which blocks plain
# requests and times out even on a healthy connection, so the loop always exhausted -
# and then fell through and ran anyway, burning the attempt on an ENOTFOUND.
# Probe what is actually used: the Anthropic API and LinkedIn's jobs-guest endpoint.
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
PROBE_LI="https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=test&start=0"

online=0
for _ in $(seq 1 30); do
  if curl -sS --max-time 10 -o /dev/null https://api.anthropic.com/v1/models 2>/dev/null \
     && curl -sS --max-time 10 -o /dev/null -A "$UA" "$PROBE_LI" 2>/dev/null; then
    online=1
    break
  fi
  sleep 10
done

if [[ $online -eq 0 ]]; then
  echo "=== $(date) no network after 5 minutes - not starting /bob ===" >> "$LOG"
  echo "$(date): day left unstamped; the next trigger will retry" >> "$LOG"
  exit 1
fi

cd "$REPO" || exit 1

# PATH is minimal under launchd - Homebrew and the user's tools are not on it.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

echo "=== $(date) starting /bob ===" >> "$LOG"

claude -p "/bob" \
  --allowedTools "Read" "Write" "Edit" "Glob" "Grep" "WebFetch" "WebSearch" "Task" \
    "Bash(python3 *)" \
    "Bash(curl *)" \
    "Bash(/Applications/Google Chrome.app/Contents/MacOS/Google Chrome *)" \
    "Bash(mkdir -p applications/*)" \
    "Bash(cp templates/* *)" \
    "Bash(git status*)" "Bash(git diff*)" \
  >> "$LOG" 2>&1
STATUS=$?

echo "=== $(date) finished /bob (exit $STATUS) ===" >> "$LOG"

# Only stamp the day as done if the run actually succeeded. The old wrapper
# stamped unconditionally, so the two runs killed with signal 9 (exit 137) on
# 22 Sep burned the day and no retry ever fired. A failed run now leaves the day
# open for the next calendar fallback to retry.
if [[ $STATUS -eq 0 ]]; then
  # Stamp the date the run FINISHED, recomputed - not $TODAY from start-up. A run
  # begun at 23:54 and finished at 00:22 stamped the previous day, so the new day
  # read as un-run and a duplicate fired hours later. The finished day is the one
  # that has a queue, so it is the one to mark done.
  date +%F > "$STAMP"
  echo "$(date): stamped $(cat "$STAMP") as complete" >> "$LOG"
else
  echo "$(date): exit $STATUS - day left unstamped so a later trigger can retry" >> "$LOG"
fi

exit $STATUS
