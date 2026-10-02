#!/bin/bash
# Install (or repair) the daily launchd schedule for this repo.
#
#   bash tools/install_schedule.sh            install / reinstall
#   bash tools/install_schedule.sh --uninstall
#
# The plist is GENERATED from this repo's real location rather than shipped with a
# path in it. launchd needs absolute paths, and a hand-edited "/Users/YOURNAME"
# placeholder is exactly the kind of thing that is wrong the moment a directory is
# renamed - which has already happened here once, breaking every run silently.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.bob.daily"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

uninstall() {
  launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null && echo "booted out $LABEL" || true
  rm -f "$PLIST" && echo "removed $PLIST"
}

if [[ "${1:-}" == "--uninstall" ]]; then
  uninstall
  exit 0
fi

[[ -x "$REPO/tools/daily_run.sh" ]] || chmod +x "$REPO/tools/daily_run.sh"
mkdir -p "$HOME/Library/LaunchAgents" "$REPO/applications/_logs"

# Boot out any previous copy, including the older label this repo used to ship.
for old in "$LABEL" com.jobhunt.daily; do
  launchctl bootout "$DOMAIN/$old" 2>/dev/null && echo "booted out existing $old" || true
done
rm -f "$HOME/Library/LaunchAgents/com.jobhunt.daily.plist"

cat > "$PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$REPO/tools/daily_run.sh</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$REPO</string>

  <!-- Primary trigger: run as soon as you are on the machine, at login or boot.
       The script's once-per-day stamp means repeated logins do not re-run it. -->
  <key>RunAtLoad</key>
  <true/>

  <!-- Safety net for the laptop that sleeps rather than shuts down: RunAtLoad never
       fires again for it. launchd runs a calendar entry missed during sleep on the
       next wake, so these catch a day where you opened the lid instead of booting.
       Off-the-hour on purpose. Each hits the once-per-day guard and exits if the day
       already ran. -->
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>57</integer></dict>
    <dict><key>Hour</key><integer>13</integer><key>Minute</key><integer>13</integer></dict>
    <dict><key>Hour</key><integer>18</integer><key>Minute</key><integer>41</integer></dict>
  </array>

  <key>StandardOutPath</key>
  <string>$REPO/applications/_logs/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>$REPO/applications/_logs/launchd.err.log</string>

  <key>ProcessType</key>
  <string>Background</string>
</dict>
</plist>
PLISTEOF

plutil -lint "$PLIST" >/dev/null
launchctl bootstrap "$DOMAIN" "$PLIST"

echo
echo "installed $LABEL"
echo "  repo:  $REPO"
echo "  plist: $PLIST"
echo "  logs:  $REPO/applications/_logs/"
echo
launchctl list | grep "$LABEL" || echo "  (not listed yet - check 'launchctl list | grep bob')"
echo
echo "To remove: bash tools/install_schedule.sh --uninstall"
