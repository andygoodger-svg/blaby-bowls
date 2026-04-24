#!/bin/bash
# Quick diagnostics for the Blaby Bowls scraper / LaunchAgent.
set +e

echo "=== 1. Last 20 lines of scraper.log ==="
tail -20 /Users/andrewgoodger/blaby-bowls/scraper.log
echo

echo "=== 2. Log file last modified ==="
stat -f "%Sm  %N" /Users/andrewgoodger/blaby-bowls/scraper.log
echo

echo "=== 3. launchd job status ==="
launchctl print "gui/$(id -u)/com.blaby.scraper" 2>/dev/null | grep -E "state|last exit|runs|path" | head -15
echo

echo "=== 4. Venv python check ==="
ls -l /Users/andrewgoodger/blaby-bowls/venv/bin/python3
/Users/andrewgoodger/blaby-bowls/venv/bin/python3 --version 2>&1
echo

echo "=== 5. Running scraper directly (this is the real test) ==="
/Users/andrewgoodger/blaby-bowls/venv/bin/python3 /Users/andrewgoodger/blaby-bowls/scraper_mac.py
echo
echo "=== Done. Exit code: $? ==="
