# CLAUDE.md

Context for Claude Code working in this repo. See `README.md` for the user-facing description; this file is the quick-start for an AI agent picking the project up.

## What this is

A daily scraper that pulls Blaby Bowls Club's fixtures, results, and league-table data from three different bowls-league websites, renders the data as static HTML, and pushes the HTML to a GitHub Pages site. Runs unattended on a MacBook Air (Apple Silicon, macOS Tahoe / 26) via a launchd LaunchAgent, at 07:00 daily.

Published at: https://andygoodger-svg.github.io/blaby-bowls/
GitHub remote: `andygoodger-svg/blaby-bowls`

## Layout

- `scraper_mac.py` — **the scraper that's actually in use** (v3). Scrapes Hinckley via HTML, Leicester via `.docx` downloads, South Leics via the Google Sheets CSV export. Sends a Telegram ping on completion, then `git add/commit/push`es to GitHub Pages.
- `scraper.py` — older v2, superseded. Leave it alone unless explicitly asked.
- `scheduler.py` — old long-running Python polling loop. **No longer used** — launchd handles scheduling now. Only kept in the repo for reference.
- `run_scraper.sh` — shell wrapper that invokes the scraper via the local venv and appends stdout/stderr to `scraper.log`. Handy for manual runs.
- `Blaby Scheduler.app` — legacy Automator wrapper around `scheduler.py`. **No longer used** on this Mac. Kept around for the other Mac.
- `com.blaby.scraper.plist` — the LaunchAgent definition. A copy is installed at `~/Library/LaunchAgents/com.blaby.scraper.plist`.
- `setup_schedule.sh` — one-time installer for the LaunchAgent (bootstrap/enable via `launchctl`).
- `diagnose.sh` — quick diagnostic runner (tails the log, checks launchd state, runs scraper directly).
- `venv/` — Python 3.14 virtualenv. **Use this** — do not create a new one. Interpreter at `venv/bin/python3`.
- `index.html`, `fixtures.html`, `results.html`, `table-*.html` — generated output. Overwritten on each scraper run. Don't hand-edit.
- `scraper.log`, `scheduler.log` — run logs. Scheduler log is legacy.

## How to run things

```bash
# Manual scrape + publish (the real thing — will push to GitHub and ping Telegram)
/Users/andrewgoodger/blaby-bowls/venv/bin/python3 /Users/andrewgoodger/blaby-bowls/scraper_mac.py

# Trigger the LaunchAgent-scheduled run immediately (for testing the schedule)
launchctl kickstart -k gui/$(id -u)/com.blaby.scraper
tail -f /Users/andrewgoodger/blaby-bowls/scraper.log

# Inspect launchd state
launchctl print gui/$(id -u)/com.blaby.scraper

# Re-install / update the LaunchAgent after editing the plist
/Users/andrewgoodger/blaby-bowls/setup_schedule.sh

# Remove the LaunchAgent
launchctl bootout gui/$(id -u)/com.blaby.scraper
rm ~/Library/LaunchAgents/com.blaby.scraper.plist
```

## Secrets

- Telegram bot token and chat ID live in `/Users/andrewgoodger/blaby-bowls/.env`.
- `.env` is gitignored. Never commit it. Never echo its contents back to the user.
- `scraper_mac.py` loads `.env` at startup via a tiny inline loader (`_load_dotenv`) — no `python-dotenv` dependency.
- If `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` is missing, `send_telegram()` logs a warning and skips silently.

## Scheduling

- LaunchAgent label: `com.blaby.scraper`, defined in `com.blaby.scraper.plist`.
- `StartCalendarInterval` set to `Hour=7 Minute=0`. If the Mac is asleep at 07:00, launchd fires the job at the next wake — this is intentional, the user is usually awake by 7am anyway.
- `RunAtLoad=false`, so installing/reloading the plist does not trigger a run.
- No `pmset` wake/sleep schedule is used on this Mac (the user's other Mac used one; this one doesn't).

## Deploy flow

Every successful `scraper_mac.py` run ends with `git add -A && git commit -m "Auto-update: <timestamp>" && git push`. The GitHub repo has Pages enabled serving from the repo root, so the push is the deploy. If the push fails, the function logs a warning and returns; there's no retry.

## Diagnostics

If the scraper stops working, run these in order:

```bash
# 1. Check last exit code and run count
launchctl print gui/$(id -u)/com.blaby.scraper | grep -E "state|exit|runs"

# 2. Check what the log says (launchd truncates on each run, so this is the last run only)
cat ~/blaby-bowls/scraper.log

# 3. Run directly to rule out launchd environment issues
/Users/andrewgoodger/blaby-bowls/venv/bin/python3 /Users/andrewgoodger/blaby-bowls/scraper_mac.py

# 4. Check system log for sandbox/permission errors (most useful for exit code 78)
/usr/bin/log show --predicate 'composedMessage CONTAINS "blaby"' --last 5m
```

**Exit code 78 (EX_CONFIG)** — launchd's `xpcproxy` was blocked by macOS Sandbox. Usually means a path in the plist points to an external/removable volume. All paths must be on the internal drive.

**Exit code 1 / git push fails** — GitHub credentials expired. Run `gh auth login -h github.com` and sign in as `andygoodger-svg`.

**Venv broken** — recreate it: `python3 -m venv ~/blaby-bowls/venv && ~/blaby-bowls/venv/bin/pip install beautifulsoup4 requests python-docx lxml`

## Conventions & gotchas

- **Paths are absolute** everywhere. `OUTPUT_DIR = "/Users/andrewgoodger/blaby-bowls"` is hardcoded in `scraper_mac.py`. Don't make it relative — launchd runs with an unpredictable `cwd`.
- **Project lives on the internal drive** at `~/blaby-bowls`. Previously on `/Volumes/SSD_1/blaby-bowls` (external SSD), but macOS Sandbox blocked launchd's `xpcproxy` from spawning binaries or opening log files on external volumes (exit code 78 / EX_CONFIG).
- **The `venv/bin/python3` symlink** targets Homebrew Python 3.14. If the user updates Homebrew or removes Python 3.14, the symlink breaks and the whole thing stops working. Fix by recreating the venv with whatever Python is installed.
- **GitHub auth** uses `gh` CLI with the `andygoodger-svg` account via osxkeychain. If pushes start failing, run `gh auth login -h github.com` and sign in as `andygoodger-svg`.
- **Season dates:** Hinckley opens early May; South Leics starts 28 April. Before then, the generated pages show "No data yet" placeholders — that's not a bug.
- **Rows with "blaby" (case-insensitive)** in league tables get CSS class `blaby-row` applied to highlight them. When adding new leagues, mirror this pattern.

## Status (as of 2026-05-01)

Scheduling is working correctly — launchd fires at 07:00 daily and successful runs are confirmed in `scraper.log` for Apr 22, 23, 24. No further debugging needed.

### Changes made 2026-04-24 (session 1)

**Leicester data caching** — The Leicester Bowls League website occasionally returns 521 (Cloudflare origin) errors (happened on the 07:00 run today). Previously this wiped the Leicester sections from the live site. Now `scraper_mac.py` persists the last successful parse to `.leicester_cache.json` and loads it as a fallback when a download fails. The Telegram notification includes a ⚠️ warning when cached data is being used.

**South Leics tables re-enabled** — `scrape_south_leics()` now tries to fetch the tables sheet each run, but validates the content (must contain "division 1" / "div 1") before using it — silently falls back to a placeholder if the sheet still contains Partridge Cup data or returns nothing.

**Debug output removed** — `parse_leicester_docx()` no longer dumps 16 rows of raw cell data per run. Replaced with a single summary line.

**Telegram failure reporting** — The Telegram notification now includes a ⚠️ line if any Leicester download failed and cached data was used.

### Changes made 2026-04-24 (session 2)

**Hinckley full-season fixtures** — `scrape_hinckley_team_fixtures()` was only fetching `f=0` (first half of season, up to end of June). Now fetches both `f=0` and `f=1` and merges, deduplicating by `(date, opponent)`. Expected fixture count to roughly double (~7 → ~14 per team) once the league publishes the second half of the season.

**South Leics full-season fixtures** — `fetch_south_leics_fixture_sheet()` now tries `gid=0` (first tab) and `gid=1` (second tab) for each division sheet and merges the rows. If the league splits their schedule across two sheet tabs, both halves will now appear. Note: `gid=1` currently returns duplicate data (no new rows), so the second half is likely not yet published or is on a different tab ID.

**Migration to internal drive** — Project was previously on `/Volumes/SSD_1/blaby-bowls` (external SSD). All code now updated to use `OUTPUT_DIR = "/Users/andrewgoodger/blaby-bowls"`. The external SSD location should no longer be used.

### Changes made 2026-04-29 / 2026-05-01 (session 3)

**South Leics results display fixed** — Results were found by the scraper but filtered out because dates were empty. Two fixes: (1) date regex now flexible (accepts with/without day-of-week and appends "2026" if year absent); (2) `gen_results` filter changed to include results with no date as well as those containing "2026".

**South Leics result dates from fixtures** — Results sheet has no date column. Added a post-pass that looks up dates from `fixture_divs` and assigns them sequentially per Blaby team (Blaby A gets fixture 1's date, Blaby B gets fixture 1's date, etc.).

**South Leics league tables** — Fixed wrong `SOUTH_LEICS_TABLES_SHEET` ID (was pointing at Partridge Cup sheet). Correct sheet ID: `1nEOs1LaiaFjhLKg9XBc3qhr2gLPbRfl9i93lGQ8aurI`. Table parsing rewritten to split by division and only show divisions containing a Blaby team. Two-row column header added (Games W/D/L, Rinks W/D/L, Shots F/A, Diff, Pts).

**Leicester docx URLs updated** — Files were re-uploaded on 30 April 2026 (new GUIDs). Updated `LEICESTER_DOCX` to new attachment URLs:
- `div1`: `f=d1ddf780-e031-4311-a40c-2136c80a392a.docx`
- `tables`: `f=77235161-97d1-4f24-8edd-abf94b26e021.docx`

**Leicester docx content validation** — Added `PK` magic-byte check immediately after download. If the server returns an HTML error page with HTTP 200, the scraper now raises a clear `ValueError` ("Server returned non-docx content; URL may need updating") instead of failing inside python-docx with the cryptic "Package not found" error.

### To-do / watch items

- Monitor daily runs to confirm Hinckley fixture counts increase from 7 to ~14 per team once the league publishes second-half fixtures.
- If South Leics fixture counts don't increase once the season is underway, open a fixture sheet in a browser, click the second tab, and read the `gid=XXXXX` value from the URL — update `fetch_south_leics_fixture_sheet()` to use those actual gid values.
- The duplicate launchd job `com.andrewgoodger.blaby-bowls` is still present — confirm with user before removing.
- Leicester docx structure: the wide two-column table layout is parsed by `parse_leicester_fixtures_structured()`. If the club changes their docx format, this will need revisiting.
- When the Leicester league re-uploads the docx files (e.g. end of season update), the `f=` GUIDs in `LEICESTER_DOCX` will need updating again — the clearest symptom is the "Server returned non-docx content" error in the log.
