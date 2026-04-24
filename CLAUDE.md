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

## Conventions & gotchas

- **Paths are absolute** everywhere. `OUTPUT_DIR = "/Users/andrewgoodger/blaby-bowls"` is hardcoded in `scraper_mac.py`. Don't make it relative — launchd runs with an unpredictable `cwd`.
- **Project lives on the internal drive** at `~/blaby-bowls`. Previously on `/Volumes/SSD_1/blaby-bowls` (external SSD), but macOS Sandbox blocked launchd's `xpcproxy` from spawning binaries or opening log files on external volumes (exit code 78 / EX_CONFIG).
- **The `venv/bin/python3` symlink** targets Homebrew Python 3.14. If the user updates Homebrew or removes Python 3.14, the symlink breaks and the whole thing stops working. Fix by recreating the venv with whatever Python is installed.
- **GitHub auth** uses `gh` CLI with the `andygoodger-svg` account via osxkeychain. If pushes start failing, run `gh auth login -h github.com` and sign in as `andygoodger-svg`.
- **Season dates:** Hinckley opens early May; South Leics starts 28 April. Before then, the generated pages show "No data yet" placeholders — that's not a bug.
- **Rows with "blaby" (case-insensitive)** in league tables get CSS class `blaby-row` applied to highlight them. When adding new leagues, mirror this pattern.
