#!/bin/bash
# Quick diagnostics for the Blaby Bowls scraper / LaunchAgent.
set +e

echo "=== 1. Last 20 lines of scraper.log ==="
tail -20 /Volumes/SSD_1/blaby-bowls/scraper.log
echo

echo "=== 2. Log file last modified ==="
stat -f "%Sm  %N" /Volumes/SSD_1/blaby-bowls/scraper.log
echo

echo "=== 3. launchd job status ==="
launchctl print "gui/$(id -u)/com.blaby.scraper" 2>/dev/null | grep -E "state|last exit|runs|path" | head -15
echo

echo "=== 4. Venv python check ==="
ls -l /Volumes/SSD_1/blaby-bowls/venv/bin/python3
/Volumes/SSD_1/blaby-bowls/venv/bin/python3 --version 2>&1
echo

echo "=== 5. Running scraper directly (this is the real test) ==="
/Volumes/SSD_1/blaby-bowls/venv/bin/python3 /Volumes/SSD_1/blaby-bowls/scraper_mac.py
echo
echo "=== Done. Exit code: $? ==="
