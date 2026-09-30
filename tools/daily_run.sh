#!/bin/bash
# Unattended daily job run. Fired by launchd at login/boot, with three calendar
# safety nets for the laptop-that-sleeps case. Runs /jobhunting once per day; the
# date stamp below is what enforces "once", not launchd.
#
# Reconstructed 2026-09-29 to match the retired ai-job-search wrapper: same
# once-per-day stamp, same log lines, same per-day log file.

set -uo pipefail

REPO="$HOME/jobhunt"
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

# Wait for a network. At boot, launchd can fire before Wi-Fi associates, and a
# scrape against a dead resolver burns the day's single run on nothing.
for _ in $(seq 1 30); do
  if curl -sSf --max-time 5 -o /dev/null https://www.linkedin.com 2>/dev/null; then
    break
  fi
  sleep 10
done

cd "$REPO" || exit 1

# PATH is minimal under launchd - Homebrew and the user's tools are not on it.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

echo "=== $(date) starting /jobhunting ===" >> "$LOG"

claude -p "/jobhunting" \
  --allowedTools "Read" "Write" "Edit" "Glob" "Grep" "WebFetch" "WebSearch" "Task" \
    "Bash(python3 *)" \
    "Bash(./detail.sh *)" \
    "Bash(curl *)" \
    "Bash(/Applications/Google Chrome.app/Contents/MacOS/Google Chrome *)" \
    "Bash(mkdir -p applications/*)" \
    "Bash(cp templates/* *)" \
    "Bash(git status*)" "Bash(git diff*)" \
  >> "$LOG" 2>&1
STATUS=$?

echo "=== $(date) finished /jobhunting (exit $STATUS) ===" >> "$LOG"

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
