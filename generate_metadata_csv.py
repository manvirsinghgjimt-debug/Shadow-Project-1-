"""
generate_metadata_csv.py
========================
GJIMT MCA – Mini Google Search Engine Project
Week 2 Helper: Auto-generates metadata.csv from your pages/ folder.

HOW TO USE
----------
1. Make sure your project folder looks like this:
       mini-google-project/
       ├── pages/
       │   ├── site01.html
       │   ├── site02.html
       │   └── ...
       └── generate_metadata_csv.py   ← this file

2. Open a terminal in mini-google-project/ and run:
       python generate_metadata_csv.py

3. metadata.csv will be created automatically in mini-google-project/

WHAT IT EXTRACTS FROM EACH HTML PAGE
--------------------------------------
  page_id    → auto-numbered (1, 2, 3 …)
  title      → <title> tag  OR  first <h1> tag
  filename   → e.g. site01.html
  category   → <meta name="category"> tag  (edit your HTML to add this)
  keywords   → <meta name="keywords"> tag
  popularity → <meta name="popularity"> tag  (0–100, default = 50)
  updated    → <meta name="updated"> tag  OR  file modification date
  links      → all href values that point to other siteXX.html files
"""

import os
import csv
import re
import glob
from datetime import datetime
from html.parser import HTMLParser

# ── Configuration ─────────────────────────────────────────────────────────────
PAGES_FOLDER = "pages"          # folder containing your HTML files
OUTPUT_CSV   = "metadata.csv"  # output file (written next to this script)
# ──────────────────────────────────────────────────────────────────────────────


class PageParser(HTMLParser):
    """Lightweight HTML parser – no external libraries needed."""

    def __init__(self):
        super().__init__()
        self.title       = ""
        self.category    = ""
        self.keywords    = ""
        self.popularity  = "50"
        self.updated     = ""
        self.h1          = ""
        self.links       = []
        self._in_title   = False
        self._in_h1      = False

    # ── tag open ──────────────────────────────────────────────────────────────
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "title":
            self._in_title = True

        elif tag in ("h1",):
            self._in_h1 = True

        elif tag == "meta":
            name    = (attrs.get("name") or "").lower()
            content = attrs.get("content") or ""
            if name == "keywords":
                self.keywords   = content
            elif name == "category":
                self.category   = content
            elif name == "popularity":
                self.popularity = content
            elif name == "updated":
                self.updated    = content

        elif tag == "a":
            href = attrs.get("href") or ""
            # Keep only links to other site pages (e.g. site23.html)
            if re.match(r"site\d+\.html", href, re.IGNORECASE):
                self.links.append(href.strip())

    # ── tag close ─────────────────────────────────────────────────────────────
    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False

    # ── text data ─────────────────────────────────────────────────────────────
    def handle_data(self, data):
        if self._in_title and not self.title:
            self.title = data.strip()
        if self._in_h1 and not self.h1:
            self.h1 = data.strip()


def file_mod_date(filepath):
    """Return file's last-modified date as YYYY-MM-DD."""
    ts = os.path.getmtime(filepath)
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def parse_html_file(filepath):
    """Parse one HTML file and return a dict of extracted metadata."""
    with open(filepath, encoding="utf-8", errors="replace") as f:
        html = f.read()

    parser = PageParser()
    parser.feed(html)

    # Prefer <title>, fall back to first <h1>
    title = parser.title or parser.h1 or os.path.basename(filepath)

    # If <meta name="updated"> is missing, use file modification date
    updated = parser.updated or file_mod_date(filepath)

    # Links as semicolon-separated string (matches the manual's format)
    links = ";".join(sorted(set(parser.links)))

    return {
        "title"      : title,
        "category"   : parser.category,
        "keywords"   : parser.keywords,
        "popularity" : parser.popularity,
        "updated"    : updated,
        "links"      : links,
    }


def natural_sort_key(filename):
    """Sort site1.html, site2.html … site100.html in numeric order."""
    nums = re.findall(r"\d+", filename)
    return int(nums[0]) if nums else 0


def generate_csv():
    # ── find HTML files ───────────────────────────────────────────────────────
    pattern = os.path.join(PAGES_FOLDER, "site*.html")
    html_files = sorted(glob.glob(pattern), key=lambda p: natural_sort_key(os.path.basename(p)))

    if not html_files:
        print(f"[ERROR] No HTML files found in '{PAGES_FOLDER}/'.")
        print("        Make sure this script is in mini-google-project/ and")
        print("        your pages are named site01.html, site02.html, …")
        return

    print(f"Found {len(html_files)} HTML file(s) in '{PAGES_FOLDER}/'.\n")

    # ── parse each file ───────────────────────────────────────────────────────
    rows = []
    for page_id, filepath in enumerate(html_files, start=1):
        filename = os.path.basename(filepath)
        print(f"  [{page_id:>3}] Parsing {filename} …", end=" ")
        try:
            meta = parse_html_file(filepath)
            rows.append({
                "page_id"   : page_id,
                "title"     : meta["title"],
                "filename"  : filename,
                "category"  : meta["category"],
                "keywords"  : meta["keywords"],
                "popularity": meta["popularity"],
                "updated"   : meta["updated"],
                "links"     : meta["links"],
            })
            print("OK")
        except Exception as e:
            print(f"SKIPPED ({e})")

    # ── write CSV ─────────────────────────────────────────────────────────────
    fieldnames = ["page_id", "title", "filename", "category",
                  "keywords", "popularity", "updated", "links"]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅  metadata.csv written with {len(rows)} row(s).")
    print(f"    Location: {os.path.abspath(OUTPUT_CSV)}\n")

    # ── preview ───────────────────────────────────────────────────────────────
    print("─" * 70)
    print(f"{'ID':<4} {'Filename':<14} {'Title':<35} {'Category'}")
    print("─" * 70)
    for r in rows[:10]:
        print(f"{r['page_id']:<4} {r['filename']:<14} {r['title'][:34]:<35} {r['category']}")
    if len(rows) > 10:
        print(f"  … and {len(rows) - 10} more rows.")
    print("─" * 70)


if __name__ == "__main__":
    generate_csv()