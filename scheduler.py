#!/usr/bin/env python3
"""
Blaby Bowls Scheduler
Runs the scraper every day at 7:00am.
Designed to start at login and run continuously.
"""

import time
import subprocess
import datetime
import os

PYTHON     = '/Volumes/SSD_1/blaby-venv/bin/python3'
SCRAPER    = '/Volumes/SSD_1/blaby-bowls/scraper_mac.py'
LOG        = '/Volumes/SSD_1/blaby-bowls/scraper.log'
SCHED_LOG  = '/Volumes/SSD_1/blaby-bowls/scheduler.log'
RUN_HOUR   = 11
RUN_MINUTE = 27

def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}\n"
    with open(SCHED_LOG, 'a') as f:
        f.write(line)
    print(line, end='')

def run_scraper():
    log("Running scraper...")
    with open(LOG, 'a') as logfile:
        result = subprocess.run(
            [PYTHON, SCRAPER],
            stdout=logfile,
            stderr=logfile
        )
    log(f"Scraper finished with exit code {result.returncode}")

last_run_date = None

log("Blaby Bowls Scheduler started")

while True:
    now = datetime.datetime.now()
    today = now.date()

    if now.hour == RUN_HOUR and now.minute == RUN_MINUTE and last_run_date != today:
        last_run_date = today
        run_scraper()

    time.sleep(30)
