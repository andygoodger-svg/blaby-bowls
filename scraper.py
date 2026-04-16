#!/usr/bin/env python3
"""
Blaby Bowls Scraper - scrapes fixtures, results & league tables for all Blaby teams.
"""
import requests
from bs4 import BeautifulSoup
import os, subprocess, sys
from datetime import datetime

OUTPUT_DIR = "/opt/blaby-bowls"
TEAM_KEYWORD = "blaby"
HINCKLEY_BASE = "https://www.bowlsresultstwo.co.uk/results24"
HINCKLEY_DIVISIONS = {1: {"name": "Division 1", "teams": ["Blaby A", "Blaby B"]}, 4: {"name": "Division 4", "teams": ["Blaby C"]}}
SOUTH_LEICS_BASE = "https://sites.google.com/view/southleicestershiretriples"
LEICESTER_BASE = "https://www.leicesterbowlsleague.co.uk/community/leicester-bowls-league-15027"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) BlabyScraper/1.0"}

CSS = """<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:transparent;color:#333;padding:10px}
h2{color:#1a5c2e;margin:15px 0 8px;font-size:1.2em;border-bottom:2px solid #1a5c2e;padding-bottom:4px}
h3{color:#2d7a45;margin:10px 0 6px;font-size:1em}
table{border-collapse:collapse;width:100%;margin-bottom:15px;font-size:.85em}
th{background:#1a5c2e;color:#fff;padding:6px 8px;text-align:left;font-weight:600}
td{padding:5px 8px;border-bottom:1px solid #e0e0e0}
tr:nth-child(even){background:#f5f9f6}
tr.blaby-row{background:#d4edda!important;font-weight:600}
tr.blaby-match{background:#e8f5e9}
.updated{font-size:.75em;color:#888;margin-top:10px;text-align:right}
.no-data{color:#888;font-style:italic;padding:10px}
.fixture-date{background:#1a5c2e;color:#fff;padding:4px 8px;margin-top:10px;font-weight:600;font-size:.9em}
.score{font-weight:700;color:#1a5c2e}
</style>"""

def html_wrapper(title, body):
    now = datetime.now().strftime("%d %b %Y %H:%M")
    return f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{title}</title>{CSS}</head><body>{body}<p class="updated">Last updated: {now}</p></body></html>'

def fetch_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"  [ERROR] {url}: {e}")
        return None

# --- HINCKLEY ---
def scrape_hinckley_fixtures(div_id):
    url = f"{HINCKLEY_BASE}/fixtures.php?res=1&d=0&yearid=2026&web=hinckley&leagueid={div_id}"
    print(f"  Hinckley Div {div_id} fixtures: {url}")
    soup = fetch_page(url)
    if not soup: return []
    fixtures = []
    current_date = ""
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            text = row.get_text(strip=True)
            if any(d in text for d in ["Mon ","Tue ","Wed ","Thu ","Fri ","Sat ","Sun "]):
                current_date = text.strip()
                continue
            if len(cells) >= 2:
                ct = [c.get_text(strip=True) for c in cells]
                if "V" in ct:
                    vi = ct.index("V")
                    if 0 < vi < len(ct)-1:
                        fixtures.append({"date":current_date,"home":ct[vi-1],"away":ct[vi+1],"score":None})
                elif len(ct) >= 3:
                    home, away = ct[0], ct[-1]
                    mid = " ".join(ct[1:-1])
                    if any(c.isdigit() for c in mid) and home and away:
                        fixtures.append({"date":current_date,"home":home,"away":away,"score":mid})
    return fixtures

def scrape_hinckley_table(div_id):
    url = f"{HINCKLEY_BASE}/tables.php?res=1&d=0&yearid=2026&web=hinckley&leagueid={div_id}"
    print(f"  Hinckley Div {div_id} table: {url}")
    soup = fetch_page(url)
    if not soup: return '<p class="no-data">No league table data available yet.</p>'
    for table in soup.find_all("table"):
        html = str(table)
        if TEAM_KEYWORD in html.lower():
            ns = BeautifulSoup(html, "html.parser")
            for row in ns.find_all("tr"):
                if TEAM_KEYWORD in row.get_text().lower():
                    row["class"] = row.get("class",[]) + ["blaby-row"]
            return str(ns)
    for table in soup.find_all("table"):
        if len(table.find_all("tr")) > 3:
            return str(table)
    return '<p class="no-data">No league table data available yet.</p>'

def scrape_hinckley_results(div_id):
    url = f"{HINCKLEY_BASE}/results.php?res=1&d=0&yearid=2026&web=hinckley&leagueid={div_id}"
    print(f"  Hinckley Div {div_id} results: {url}")
    soup = fetch_page(url)
    if not soup: return []
    results = []
    current_date = ""
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            text = row.get_text(strip=True)
            cells = row.find_all("td")
            if any(d in text for d in ["Mon ","Tue ","Wed ","Thu ","Fri ","Sat ","Sun "]):
                current_date = text.strip()
                continue
            if len(cells) >= 2:
                ct = [c.get_text(strip=True) for c in cells]
                if TEAM_KEYWORD in " ".join(ct).lower():
                    results.append({"date":current_date,"raw":ct})
    return results

# --- SOUTH LEICS ---
def scrape_south_leics_page(page):
    url = f"{SOUTH_LEICS_BASE}/{page}"
    print(f"  South Leics {page}: {url}")
    soup = fetch_page(url)
    if not soup: return []
    data = []
    for table in soup.find_all("table"):
        if TEAM_KEYWORD in table.get_text().lower():
            for row in table.find_all("tr"):
                if TEAM_KEYWORD in row.get_text().lower():
                    data.append([c.get_text(strip=True) for c in row.find_all(["td","th"])])
    iframes = soup.find_all("iframe")
    for iframe in iframes:
        src = iframe.get("src","")
        if src:
            ss = fetch_page(src)
            if ss:
                for table in ss.find_all("table"):
                    if TEAM_KEYWORD in table.get_text().lower():
                        for row in table.find_all("tr"):
                            if TEAM_KEYWORD in row.get_text().lower():
                                data.append([c.get_text(strip=True) for c in row.find_all(["td","th"])])
    return data

def scrape_south_leics_tables():
    url = f"{SOUTH_LEICS_BASE}/tables"
    print(f"  South Leics tables: {url}")
    soup = fetch_page(url)
    if not soup: return '<p class="no-data">No data yet.</p>'
    parts = []
    for table in soup.find_all("table"):
        if TEAM_KEYWORD in table.get_text().lower():
            ns = BeautifulSoup(str(table), "html.parser")
            for row in ns.find_all("tr"):
                if TEAM_KEYWORD in row.get_text().lower():
                    row["class"] = row.get("class",[]) + ["blaby-row"]
            parts.append(str(ns))
    iframes = soup.find_all("iframe")
    for iframe in iframes:
        src = iframe.get("src","")
        if src:
            ss = fetch_page(src)
            if ss:
                for table in ss.find_all("table"):
                    if TEAM_KEYWORD in table.get_text().lower():
                        ns = BeautifulSoup(str(table), "html.parser")
                        for row in ns.find_all("tr"):
                            if TEAM_KEYWORD in row.get_text().lower():
                                row["class"] = row.get("class",[]) + ["blaby-row"]
                        parts.append(str(ns))
    return "\n".join(parts) if parts else '<p class="no-data">No South Leics table data yet.</p>'

# --- LEICESTER ---
def scrape_leicester_page(page):
    url = f"{LEICESTER_BASE}/{page}"
    print(f"  Leicester {page}: {url}")
    soup = fetch_page(url)
    if not soup: return [], []
    docx_links = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if ".docx" in h.lower():
            full = h if h.startswith("http") else f"https://www.leicesterbowlsleague.co.uk{h}"
            docx_links.append({"url":full,"text":a.get_text(strip=True)})
    html_data = []
    for table in soup.find_all("table"):
        if TEAM_KEYWORD in table.get_text().lower():
            for row in table.find_all("tr"):
                if TEAM_KEYWORD in row.get_text().lower():
                    html_data.append([c.get_text(strip=True) for c in row.find_all(["td","th"])])
    return html_data, docx_links

def parse_docx(url, label):
    try:
        from docx import Document
        import tempfile
        print(f"  Downloading docx: {label}")
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        tmp = os.path.join(tempfile.gettempdir(), "temp_bowls.docx")
        with open(tmp,"wb") as f: f.write(r.content)
        doc = Document(tmp)
        tables = []
        for t in doc.tables:
            for row in t.rows:
                rt = [c.text.strip() for c in row.cells]
                if TEAM_KEYWORD in " ".join(rt).lower():
                    tables.append(rt)
        paras = [p.text.strip() for p in doc.paragraphs if TEAM_KEYWORD in p.text.lower()]
        os.remove(tmp)
        return {"tables":tables,"paragraphs":paras}
    except Exception as e:
        print(f"  [ERROR] docx: {e}")
        return None

# --- HTML GENERATION ---
def gen_fixtures(hfix, slfix, lfix, ldocx):
    b = "<h2>Blaby Bowls - Upcoming Fixtures 2026</h2>\n"
    b += "<h2>Hinckley &amp; District Triples League</h2>\n"
    for did, di in HINCKLEY_DIVISIONS.items():
        b += f'<h3>{di["name"]} ({", ".join(di["teams"])})</h3>\n'
        df = [f for f in hfix.get(did,[]) if f["score"] is None and TEAM_KEYWORD in (f["home"]+f["away"]).lower()]
        if df:
            b += '<table><tr><th>Date</th><th>Home</th><th></th><th>Away</th></tr>\n'
            cd = ""
            for f in df:
                if f["date"] != cd:
                    cd = f["date"]
                    b += f'<tr><td colspan="4" class="fixture-date">{cd}</td></tr>\n'
                b += f'<tr class="blaby-match"><td></td><td>{f["home"]}</td><td>V</td><td>{f["away"]}</td></tr>\n'
            b += '</table>\n'
        else:
            b += '<p class="no-data">No upcoming fixtures found.</p>\n'
    b += "<h2>South Leicestershire Triples League</h2>\n"
    if slfix:
        b += '<table><tr><th>Fixture Details</th></tr>\n'
        for f in slfix:
            b += f'<tr class="blaby-match"><td>{" | ".join(f)}</td></tr>\n'
        b += '</table>\n'
    else:
        b += '<p class="no-data">Season starts 28th April 2026. Fixtures will appear once available.</p>\n'
    b += "<h2>Leicester Bowls League</h2>\n"
    has = False
    if lfix:
        b += '<table><tr><th>Fixture Details</th></tr>\n'
        for f in lfix:
            b += f'<tr class="blaby-match"><td>{" | ".join(f)}</td></tr>\n'
        b += '</table>\n'
        has = True
    if ldocx:
        for d in ldocx:
            if d and d.get("tables"):
                if not has: b += '<table><tr><th>Details</th></tr>\n'
                for r in d["tables"]:
                    b += f'<tr class="blaby-match"><td>{" | ".join(r)}</td></tr>\n'
                if not has: b += '</table>\n'
                has = True
    if not has:
        b += '<p class="no-data">Leicester fixtures stored in downloadable documents. Check the website directly.</p>\n'
    return html_wrapper("Blaby Bowls - Fixtures 2026", b)

def gen_results(hfix, hres, slres, ldocx):
    b = "<h2>Blaby Bowls - Results &amp; Scores 2026</h2>\n"
    b += "<h2>Hinckley &amp; District Triples League</h2>\n"
    for did, di in HINCKLEY_DIVISIONS.items():
        b += f'<h3>{di["name"]} ({", ".join(di["teams"])})</h3>\n'
        dr = [f for f in hfix.get(did,[]) if f["score"] is not None and TEAM_KEYWORD in (f["home"]+f["away"]).lower()]
        er = hres.get(did,[])
        if dr:
            b += '<table><tr><th>Date</th><th>Home</th><th>Score</th><th>Away</th></tr>\n'
            cd = ""
            for f in dr:
                if f["date"] != cd:
                    cd = f["date"]
                    b += f'<tr><td colspan="4" class="fixture-date">{cd}</td></tr>\n'
                b += f'<tr class="blaby-match"><td></td><td>{f["home"]}</td><td class="score">{f["score"]}</td><td>{f["away"]}</td></tr>\n'
            b += '</table>\n'
        elif er:
            b += '<table><tr><th>Date</th><th>Details</th></tr>\n'
            for r in er:
                b += f'<tr class="blaby-match"><td>{r.get("date","")}</td><td>{" | ".join(r.get("raw",[]))}</td></tr>\n'
            b += '</table>\n'
        else:
            b += '<p class="no-data">No results yet - season starts May 2026.</p>\n'
    b += "<h2>South Leicestershire Triples League</h2>\n"
    if slres:
        b += '<table><tr><th>Result Details</th></tr>\n'
        for r in slres:
            b += f'<tr class="blaby-match"><td>{" | ".join(r)}</td></tr>\n'
        b += '</table>\n'
    else:
        b += '<p class="no-data">Season starts 28th April 2026. Results will appear once matches are played.</p>\n'
    b += "<h2>Leicester Bowls League</h2>\n"
    has = False
    if ldocx:
        for d in ldocx:
            if d and d.get("tables"):
                rr = [r for r in d["tables"] if any(any(c.isdigit() for c in cell) for cell in r)]
                if rr:
                    b += '<table><tr><th>Details</th></tr>\n'
                    for r in rr:
                        b += f'<tr class="blaby-match"><td>{" | ".join(r)}</td></tr>\n'
                    b += '</table>\n'
                    has = True
    if not has:
        b += '<p class="no-data">No results available yet for Leicester Bowls League.</p>\n'
    return html_wrapper("Blaby Bowls - Results 2026", b)

def gen_table(league, div, html):
    b = f"<h2>{league}</h2>\n<h3>{div}</h3>\n{html}"
    return html_wrapper(f"Blaby - {league} {div}", b)

def gen_index():
    b = """<h2>Blaby Bowls Club - 2026 Season</h2>
<p>Auto-updated fixtures, results, and league tables.</p>
<h3>Fixtures &amp; Results</h3>
<table><tr><th>Page</th><th>Description</th></tr>
<tr><td><a href="fixtures.html">All Fixtures</a></td><td>Upcoming matches</td></tr>
<tr><td><a href="results.html">All Results</a></td><td>Scores as they come in</td></tr></table>
<h3>League Tables</h3>
<table><tr><th>League</th><th>Division</th></tr>
<tr><td><a href="table-hinckley-div1.html">Hinckley &amp; District</a></td><td>Div 1 (Blaby A, B)</td></tr>
<tr><td><a href="table-hinckley-div4.html">Hinckley &amp; District</a></td><td>Div 4 (Blaby C)</td></tr>
<tr><td><a href="table-south-leics.html">South Leics Triples</a></td><td>League Table</td></tr>
<tr><td><a href="table-leicester.html">Leicester Bowls</a></td><td>League Table</td></tr></table>"""
    return html_wrapper("Blaby Bowls Club - 2026", b)

def git_push():
    try:
        os.chdir(OUTPUT_DIR)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(["git","add","-A"], check=True, capture_output=True)
        r = subprocess.run(["git","status","--porcelain"], capture_output=True, text=True)
        if not r.stdout.strip():
            print("  No changes to push.")
            return True
        subprocess.run(["git","commit","-m",f"Auto-update: {now}"], check=True, capture_output=True)
        subprocess.run(["git","push"], check=True, capture_output=True)
        print(f"  Pushed to GitHub at {now}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Git push failed: {e}")
        return False

def main():
    print("="*60)
    print(f"Blaby Bowls Scraper - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n[1/3] Hinckley & District Triples...")
    hfix, hres, htab = {}, {}, {}
    for did in HINCKLEY_DIVISIONS:
        hfix[did] = scrape_hinckley_fixtures(did)
        hres[did] = scrape_hinckley_results(did)
        htab[did] = scrape_hinckley_table(did)
        print(f"  Div {did}: {len(hfix[did])} fixtures, {len(hres[did])} results")

    print("\n[2/3] South Leicestershire Triples...")
    slfix = scrape_south_leics_page("league")
    slres = scrape_south_leics_page("results")
    sltab = scrape_south_leics_tables()
    print(f"  {len(slfix)} fixtures, {len(slres)} results")

    print("\n[3/3] Leicester Bowls League...")
    lfix, lfix_docs = scrape_leicester_page("league-fixtures--results/")
    ltab_html, ltab_docs = scrape_leicester_page("league-tables/")
    ldocx = []
    for d in lfix_docs + ltab_docs:
        data = parse_docx(d["url"], d["text"])
        if data: ldocx.append(data)
    print(f"  {len(lfix)} HTML fixtures, {len(lfix_docs+ltab_docs)} docx processed")

    print("\nGenerating HTML...")
    files = {
        "index.html": gen_index(),
        "fixtures.html": gen_fixtures(hfix, slfix, lfix, ldocx),
        "results.html": gen_results(hfix, hres, slres, ldocx),
        "table-hinckley-div1.html": gen_table("Hinckley & District Triples","Division 1", htab.get(1,'<p class="no-data">No data yet.</p>')),
        "table-hinckley-div4.html": gen_table("Hinckley & District Triples","Division 4", htab.get(4,'<p class="no-data">No data yet.</p>')),
        "table-south-leics.html": gen_table("South Leicestershire Triples","League Table", sltab),
        "table-leicester.html": gen_table("Leicester Bowls League","League Table", ltab_html if ltab_html else '<p class="no-data">Tables in downloadable docs on league website.</p>'),
    }
    for fn, content in files.items():
        with open(os.path.join(OUTPUT_DIR, fn), "w") as f: f.write(content)
        print(f"  Written: {fn}")

    print("\nPushing to GitHub...")
    if git_push():
        print("\nDone! Live at https://andygoodger-svg.github.io/blaby-bowls/")
    else:
        print("\n[WARN] Push failed - files saved locally only.")
    print("="*60)
    return True

if __name__ == "__main__":
    main()
