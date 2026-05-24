# CLAUDE.md

Context for Claude Code working in this repo. See `README.md` for the user-facing description; this file is the quick-start for an AI agent picking the project up.

#MEMORY
when saving to mem0, always tag with project:blaby-bowling-club

## What this is

A daily scraper that pulls Blaby Bowls Club's fixtures, results, and league-table data from three different bowls-league websites, renders the data as static HTML, and pushes the HTML to a GitHub Pages site. Runs unattended at 07:00 daily.

**Where the daily run actually executes:** The project is checked out on both Andrew's MacBook Air and the Mac Mini (`ssh macmini`, 192.168.68.79). The Mac Mini is the host that does the scheduled run — the MacBook Air has no LaunchAgent installed for this project. See **Scheduling** below for the two different mechanisms.

Published at: https://andygoodger-svg.github.io/blaby-bowls/
GitHub remote: `andygoodger-svg/blaby-bowls`

## Layout

- `scraper_mac.py` — **the scraper that's actually in use** (v3). Scrapes Hinckley via HTML, Leicester via `.docx` downloads, South Leics via the Google Sheets CSV export. Sends a Telegram ping on completion, then `git add/commit/push`es to GitHub Pages.
- `scraper.py` — older v2, superseded. Leave it alone unless explicitly asked.
- `scheduler.py` — long-running Python polling loop. Still in use on the Mac Mini (wrapped by `Blaby Scheduler.app`); not used on the MacBook Air.
- `run_scraper.sh` — shell wrapper that invokes the scraper via the local venv and appends stdout/stderr to `scraper.log`. Handy for manual runs.
- `Blaby Scheduler.app` — Automator wrapper around `scheduler.py`. **This is what triggers the daily 07:00 run on the Mac Mini.** Registered with launchd as `application.com.apple.automator.Blaby-Scheduler.<...>` (visible via `launchctl list | grep -i blaby`). Not used on the MacBook Air.
- `com.blaby.scraper.plist` — the LaunchAgent definition. Intended for the MacBook Air setup (installed at `~/Library/LaunchAgents/com.blaby.scraper.plist`). **Not installed on the Mac Mini** — the Mini uses the Automator app instead.
- `setup_schedule.sh` — one-time installer for the LaunchAgent (bootstrap/enable via `launchctl`). MacBook Air only.
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

There are **two scheduling setups** depending on which machine you're on.

### Mac Mini (this is the machine that produces the daily published commits)
- Triggered by a **LaunchDaemon** at `/Library/LaunchDaemons/com.blaby.scraper.plist` (root-installed, runs as `andrewgoodger`). `StartCalendarInterval` fires `venv/bin/python3 scraper_mac.py` at 07:00 daily. Not visible via user-scope `launchctl list` — `sudo launchctl list | grep blaby` to see it.
- The plist is checked into the repo as `com.blaby.scraper.plist` but lives at `/Library/LaunchDaemons/` not `~/Library/LaunchAgents/` (so `launchctl print gui/$(id -u)/com.blaby.scraper` returns "Could not find service" — that's expected; check `system/com.blaby.scraper` instead).
- `scheduler.py` and `Blaby Scheduler.app` are **legacy / unused** on the Mini as of 2026-05-24. Prior to that date a second copy of the project on `/Volumes/SSD_1/blaby-bowls/` was also auto-starting via an Automator login item and trying to push stale data — that was the source of the "push failed" Telegram on 2026-05-24 07:00. The SSD `scheduler.py` has been replaced with a no-op stub; the login item still exists in System Settings → Login Items and should be removed manually next time someone is at the machine.
- `scheduler.log` on the Mini is stale and unused — the LaunchDaemon logs only into `scraper.log`.

### MacBook Air
- LaunchAgent label: `com.blaby.scraper`, defined in `com.blaby.scraper.plist`, installed via `setup_schedule.sh`.
- `StartCalendarInterval` set to `Hour=7 Minute=0`. If the Mac is asleep at 07:00, launchd fires the job at the next wake.
- Currently **not installed** on the MacBook Air (no plist in `~/Library/LaunchAgents/`). The Mini is doing the daily work; the MacBook Air is just a dev checkout.

### Multi-machine git divergence
- Both machines push to the same `main` branch on GitHub. If you commit on the MacBook Air, the Mini's local main goes behind and the next 07:00 push will be rejected.
- `scraper_mac.py`'s `git_push()` now does a `git pull --rebase origin main` before pushing (the fix in commit `37c3b08`, added 2026-05-19 after a push-failed Telegram from yesterday's 07:00 run on the Mini).
- If a push genuinely fails, `send_telegram()` posts: *"Blaby Bowls scraper ran at <ts> but push failed. Check logs."*
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

### Changes made 2026-05-08 (session 4)

**Leicester dynamic URL discovery** — The Leicester league re-uploads their docx files every week or two (new GUIDs each time), breaking the hardcoded attachment URLs. Added `discover_leicester_docx_urls()` which scrapes the league's fixture and table pages at runtime to find the current download link automatically. Fallback GUIDs (7 May 2026 upload) still in `LEICESTER_DOCX` for when the page is unreachable.

**Leicester table parser rewritten** — `parse_leicester_table_div1()` now extracts columns by fixed position index (0,1,3,4,5,7,8,9,11,12,13,15) matching the docx's 16-column layout (with empty spacer columns). Uses the same two-row grouped header as South Leics (Games W/D/L, Rinks W/D/L, Shots F/A, Diff, Pts). Previously was cutting off at `cells[:8]` and losing most columns.

**South Leics fixture display fixed** — When results are entered into the Google Sheet, fixture rows gain score columns ([Home, HomeScore, AwayScore, Away]). Previously `cells[1]` was used as the Away team, giving the score instead. Now scans reversed cells for the last non-numeric value.

**South Leics result date matching fixed** — Date assignment now matches each result to its fixture by opponent name lookup, not sequential position. This correctly handles the case where results in the sheet are newest-first but fixtures are oldest-first.

### Changes made 2026-05-24 (session 5)

**Orphan SSD scheduler disabled** — The `/Volumes/SSD_1/blaby-bowls/` copy (pre-migration leftover, scraper dated 24 Apr) was still being auto-launched at login by a separate `Blaby Scheduler.app` Automator login item. It ran at 07:00 each day with stale code (no rebase fix, stale Leicester GUIDs), failed to push, and sent a "push failed" Telegram alert — while the internal LaunchDaemon's run succeeded in parallel and published correctly. Replaced `/Volumes/SSD_1/blaby-bowls/scheduler.py` with a no-op stub that logs and exits, so the login item launches cleanly without invoking the stale scraper. Killed the running PIDs (1705/1715).

### To-do / watch items

- Manually remove the "Blaby Scheduler" entry from System Settings → General → Login Items & Extensions (it currently points at `/Volumes/SSD_1/blaby-bowls/Blaby Scheduler.app`, which now runs the no-op stub). The whole `/Volumes/SSD_1/blaby-bowls/` directory can be deleted once that's done.
- Monitor daily runs to confirm Hinckley fixture counts increase from 7 to ~14 per team once the league publishes second-half fixtures.
- If South Leics fixture counts don't increase once the season is underway, open a fixture sheet in a browser, click the second tab, and read the `gid=XXXXX` value from the URL — update `fetch_south_leics_fixture_sheet()` to use those actual gid values.
- The duplicate launchd job `com.andrewgoodger.blaby-bowls` is still present — confirm with user before removing.
- Leicester docx structure: the wide two-column table layout is parsed by `parse_leicester_fixtures_structured()`. If the club changes their docx format, this will need revisiting.
