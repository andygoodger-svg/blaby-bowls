#!/bin/bash
# One-time setup for the Blaby Bowls scraper on macOS (tested on Tahoe / macOS 26).
# Installs a LaunchAgent that runs the scraper at 07:00 daily.
# If the Mac is asleep at 07:00, launchd runs it automatically at the next wake.
set -e

PLIST_SRC="/Volumes/SSD_1/blaby-bowls/com.blaby.scraper.plist"
LA_DIR="$HOME/Library/LaunchAgents"
PLIST_DST="$LA_DIR/com.blaby.scraper.plist"
LABEL="com.blaby.scraper"
UID_NUM="$(id -u)"

echo "Blaby Bowls scheduler setup"
echo "==========================="

if [ ! -f "$PLIST_SRC" ]; then
  echo "ERROR: missing $PLIST_SRC — is the SSD mounted?"
  exit 1
fi

# 1. Copy the LaunchAgent into the user's LaunchAgents folder.
mkdir -p "$LA_DIR"
cp "$PLIST_SRC" "$PLIST_DST"
echo "  Copied LaunchAgent to $PLIST_DST"

# 2. (Re)load it using modern launchctl syntax.
#    'bootout' unloads a previous version if present; errors here are harmless.
launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID_NUM" "$PLIST_DST"
launchctl enable "gui/$UID_NUM/$LABEL"
echo "  LaunchAgent bootstrapped — scraper will run at 07:00 daily"
echo "  (If the Mac is asleep at 07:00, it'll run as soon as you wake it.)"

# 3. Summary.
echo
echo "Loaded launchd jobs matching 'blaby':"
launchctl list | grep blaby || echo "  (none shown — but agent is installed)"
echo
echo "Setup complete."
echo
echo "To run a manual test right now:"
echo "    launchctl kickstart -k gui/$UID_NUM/$LABEL"
echo "    tail -f /Volumes/SSD_1/blaby-bowls/scraper.log"
echo
echo "To remove later:"
echo "    launchctl bootout gui/$UID_NUM/$LABEL"
echo "    rm $PLIST_DST"
