# Blaby Bowls

Auto-updating fixtures, results, and league tables for Blaby Bowls Club's 2026 season. A Python scraper pulls Blaby-related data from three different bowls league websites each morning, renders it into a set of self-contained HTML pages, and pushes them to GitHub Pages at:

**https://andygoodger-svg.github.io/blaby-bowls/**

## What it tracks

Blaby Bowls Club plays in three leagues, each with its own (quite different) website:

| League | Teams | Source | Scrape method |
| --- | --- | --- | --- |
| Hinckley & District Triples | Blaby A, Blaby B (Div 1), Blaby C (Div 4) | [bowlsresultstwo.co.uk](https://www.bowlsresultstwo.co.uk/hinckley/) | HTML scrape of per-team fixture pages |
| Leicester Bowls League | Division 1 (plus Div 2 North / South) | [leicesterbowlsleague.co.uk](https://www.leicesterbowlsleague.co.uk/) | Downloads published `.docx` files and parses tables |
| South Leicestershire Triples | League table & fixtures | [Google Sites page](https://sites.google.com/view/southleicestershiretriples/) | Google Sheets CSV export (v3) — plain HTML is JS-rendered and can't be scraped directly |

Rows containing "Blaby" are highlighted in the generated HTML so they stand out in each league table.

## Generated pages

The scraper writes these files into the repo root and commits them:

- `index.html` — landing page with links to everything
- `fixtures.html` — upcoming matches across all three leagues
- `results.html` — played matches with scores
- `table-hinckley-div1.html` — Division 1 table (Blaby A, Blaby B)
- `table-hinckley-div4.html` — Division 4 table (Blaby C)
- `table-leicester.html` — Leicester Bowls League table
- `table-south-leics.html` — South Leicestershire Triples table

All pages use a shared inline CSS block (green Blaby theme, mobile-friendly).

## Scripts in this folder

- `scraper.py` — **v2** of the scraper. Writes to `/opt/blaby-bowls` and was the original Linux-oriented version.
- `scraper_mac.py` — **v3**, the one actually in use. Writes to `/Volumes/SSD_1/blaby-bowls`, scrapes South Leics via CSV export (no JS workaround needed), and sends a Telegram notification when a run completes.
- `scheduler.py` — simple in-process scheduler that wakes every 30 seconds and runs `scraper_mac.py` at 07:00 daily. Designed to start at login and run continuously.
- `run_scraper.sh` — one-shot wrapper that invokes the scraper and appends stdout/stderr to `scraper.log`. Useful for launchd, cron, or a manual run.
- `Blaby Scheduler.app` — Mac app bundle that launches the scheduler (so it can live in the Dock / login items rather than a terminal window).

## Logs

- `scraper.log` — full output from each scraper run (what URLs were hit, how many rows parsed, errors)
- `scheduler.log` — one line per scheduler event (start, run triggered, exit code)

## How to run it manually

```bash
# One-off scrape + publish (uses the venv bundled alongside this folder)
./run_scraper.sh

# Or call the Python directly
/Volumes/SSD_1/blaby-venv/bin/python3 scraper_mac.py
```

A successful run ends with a `git add / commit / push` to publish the new HTML to GitHub Pages, and a Telegram ping to confirm.

## Setup notes

- Python venv lives at `/Volumes/SSD_1/blaby-venv` (note: outside this repo). Key dependencies: `requests`, `beautifulsoup4`, `python-docx`.
- This folder is a git repo that pushes to `andygoodger-svg/blaby-bowls` on GitHub; GitHub Pages serves the HTML files.
- Telegram bot token and chat ID are currently hardcoded at the top of `scraper_mac.py` — worth moving to environment variables or a local config file before sharing the repo more widely.

## Season

2026 Hinckley season opens in early May; South Leicestershire Triples starts 28 April 2026. Before those dates, fixture/result pages show "No data yet" placeholders.
