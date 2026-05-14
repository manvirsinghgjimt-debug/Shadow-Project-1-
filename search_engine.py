# ─────────────────────────────────────────────────────────────
# FILE: search_engine.py
# PROJECT: Mini Google Search Engine — GJIMT MCA AI Integration
# AUTHOR: [Your Name] | TEAM: [Team Name] | DATE: [Date]
# WEEK: 3 — Baseline Search Engine (Student-Written)
# ─────────────────────────────────────────────────────────────

import csv          # Built-in Python library for reading CSV files.
                    # No pip install needed — it comes with Python.

# ── CONSTANTS (safety limits) ──────────────────────────────────
MAX_PAGES  = 100    # We will never load more than 100 pages.
                    # Prevents crashes if metadata.csv has extra rows.

MAX_QTERMS = 10     # We only process the first 10 words of any query.
                    # Prevents slowdowns from very long search strings.


# ── PAGE CLASS ────────────────────────────────────────────────
class Page:
    """
    Represents one webpage from our mini corpus.
    Every row in metadata.csv becomes one Page object.
    """

    def __init__(self):           # __init__ runs automatically when we
                                  # create a new Page object.
        self.page_id    = 0       # Unique number: 1 to 100
        self.title      = ""      # Page heading (e.g. "Best Biryani in Mohali")
        self.filename   = ""      # HTML file name (e.g. "site04.html")
        self.category   = ""      # Theme: Education, Food, Technology, etc.
        self.keywords   = ""      # Semicolon-separated tags from metadata.csv
        self.content    = ""      # Body text (loaded separately from .html file)
        self.popularity = 0       # Score from 0–100 assigned by your team
        self.updated    = ""      # Date last edited: YYYY-MM-DD format
        self.links      = ""      # Other pages this page links to
        self.score      = 0       # SEARCH SCORE — computed fresh for each query
                                  # Starts at 0, increases based on keyword matches


# ── HELPER: CASE-INSENSITIVE SEARCH ───────────────────────────
def contains_ignore_case(text: str, word: str) -> bool:
    """
    Returns True if 'word' is found anywhere inside 'text',
    ignoring uppercase/lowercase differences.

    WHY: "AI" and "ai" and "Ai" should all be treated as the same word.

    EXAMPLE:
        contains_ignore_case("AI Tools for Students", "ai")  → True
        contains_ignore_case("Python Coding Guide",   "ai")  → False
    """
    return word.lower() in text.lower()
    #      ──────────── ──  ───────────
    #      Converts word    Converts text to lowercase first,
    #      to lowercase     then checks if word is inside it.


# ── SCORING FUNCTION ──────────────────────────────────────────
def score_page(page: Page, query_terms: list) -> None:
    """
    Calculates a relevance score for one page against all query words.
    Modifies page.score directly (returns nothing — that's what None means).

    SCORING RULES:
        Title match    → +10  (title is the clearest relevance signal)
        Keyword match  → + 5  (keywords are handpicked — strong signal)
        Content match  → + 2  (content is long and noisy — weaker signal)
        Popularity     → +popularity // 10  (a small boost for popular pages)

    WORKED EXAMPLE:
        Query: "AI tools"   →   query_terms = ["AI", "tools"]
        Page title: "AI Tools for Beginners"   popularity: 88
        "AI"    found in title    → +10
        "tools" found in title    → +10
        "AI"    found in keywords → + 5
        "tools" found in keywords → + 5
        Popularity bonus: 88 // 10 → + 8
        ─────────────────────────────────
        TOTAL SCORE = 38
    """
    page.score = 0              # Always reset to 0 before scoring.
                                # Without this, scores would keep adding up
                                # across multiple searches!
    keyword_score = 0           # Tracks ONLY keyword/title/content matches.
                                # We use this to decide if the page is relevant at all.

    for term in query_terms:    # Loop through each word in the search query.
        if contains_ignore_case(page.title, term):
            keyword_score += 10    # Title match: highest weight.

        if contains_ignore_case(page.keywords, term):
            keyword_score += 5     # Keyword match: medium weight.

        if contains_ignore_case(page.content, term):
            keyword_score += 2     # Content match: lowest weight.

    # Only add the popularity bonus if the page actually matched the query.
    # FIX: Without this check, EVERY page gets a score (popularity // 10),
    #      so even "Education" pages appear when you search "food".
    if keyword_score > 0:
        page.score = keyword_score + page.popularity // 10
        # '//' is integer division in Python: 88 // 10 = 8  (drops the remainder)
        # This means a page with popularity=88 gets +8 bonus points.
    else:
        page.score = 0          # No keyword match → score stays 0. Page won't show.


# ── LOAD PAGES FROM CSV ───────────────────────────────────────
def load_pages(filename: str) -> list:
    """
    Opens metadata.csv and returns a list of Page objects.
    Each row in the CSV becomes one Page object.

    WHAT IS csv.DictReader?
        It reads the CSV and gives us each row as a Python dictionary.
        Dictionary means: {'title': 'Best Biryani', 'popularity': '62', ...}

    HOW TO USE:
        pages = load_pages("metadata.csv")
        print(len(pages))   # → 100
    """
    pages = []                  # Start with an empty list.

    try:
        with open(filename, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # DictReader reads the first row as column headers automatically.

            for i, row in enumerate(reader):
                if i >= MAX_PAGES:
                    break       # Stop after MAX_PAGES rows (safety limit).

                pg = Page()     # Create a new empty Page object.

                # Fill in each field from the CSV row dictionary.
                pg.page_id    = int(row.get("page_id", 0))
                pg.title      = row.get("title", "")
                pg.filename   = row.get("filename", "")
                pg.category   = row.get("category", "")
                pg.keywords   = row.get("keywords", "")
                pg.popularity = int(row.get("popularity", 0))
                pg.updated    = row.get("updated", "")
                pg.links      = row.get("links", "")
                # .get("fieldname", default) safely gets the value.
                # If field is missing, it returns the default instead of crashing.

                pages.append(pg)    # Add the new Page to our list.

    except FileNotFoundError:
        print(f"ERROR: Could not find '{filename}'.")
        print("Make sure metadata.csv is in the same folder as this script.")

    return pages


# ── LOAD PAGE CONTENT FROM HTML ───────────────────────────────
def load_page_content(pages: list, pages_folder: str = "pages") -> None:
    """
    Opens each .html file and extracts the plain text content.
    Stores it in page.content so it can be searched.

    WHY: metadata.csv doesn't store the full body text.
         We need to open each HTML file to get the content.

    NOTE: We use a simple approach — we strip HTML tags by looking
          for text OUTSIDE of angle brackets < >.
    """
    for pg in pages:
        filepath = f"{pages_folder}/{pg.filename}"
        try:
            with open(filepath, encoding="utf-8") as f:
                raw_html = f.read()

            # Simple tag stripper: remove everything between < and >
            text = ""
            inside_tag = False
            for char in raw_html:
                if char == "<":
                    inside_tag = True
                elif char == ">":
                    inside_tag = False
                elif not inside_tag:
                    text += char

            pg.content = text.strip()

        except FileNotFoundError:
            pg.content = ""     # If file is missing, content stays empty.


# ── DISPLAY RESULTS ───────────────────────────────────────────
def display_results(results: list, top_n: int = 5) -> None:
    """
    Prints the top N search results in a readable format.

    'results' is a list of Page objects already sorted by score.
    We only print the first top_n items.
    """
    if not results:
        print("No results found.")
        return

    print(f"\n{'─'*60}")
    print(f"  TOP {top_n} RESULTS")
    print(f"{'─'*60}")

    shown = 0
    for pg in results:
        if pg.score == 0:
            break               # Stop once we hit pages with zero score.
                                # FIX: Now this actually works because irrelevant
                                #      pages have score=0, not popularity//10.
        if shown >= top_n:
            break

        shown += 1
        print(f"\n  #{shown}  {pg.title}")
        print(f"       File     : {pg.filename}")
        print(f"       Category : {pg.category}")
        print(f"       Score    : {pg.score}")
        print(f"       Popularity: {pg.popularity}")

    if shown == 0:
        print("  No pages matched your query.")

    print(f"\n{'─'*60}\n")


# ── MAIN FUNCTION ─────────────────────────────────────────────
def main():
    """
    The main loop of the search engine.
    1. Load pages from metadata.csv
    2. Load content from HTML files
    3. Accept user queries in a loop
    4. Score, sort, and display results
    5. Repeat until user types 'quit'
    """
    print("=" * 60)
    print("  MINI GOOGLE SEARCH ENGINE — GJIMT MCA AI Integration")
    print("  Baseline Version | search_engine.py")
    print("=" * 60)

    # ── STEP 1: Load metadata ────────────────────────────────
    print("\nLoading pages from metadata.csv ...")
    pages = load_pages("metadata.csv")
    print(f"Loaded {len(pages)} pages.")

    # ── STEP 2: Load HTML content ────────────────────────────
    print("Loading page content from HTML files ...")
    load_page_content(pages, pages_folder="pages")
    print("Content loaded.\n")

    # ── STEP 3: Search loop ──────────────────────────────────
    while True:
        query_input = input("Enter search query (or 'quit' to exit): ").strip()

        if query_input.lower() == "quit":
            print("Goodbye!")
            break

        if not query_input:
            print("Please enter at least one word.")
            continue

        # ── TOKENISE: Split query into individual words ──────
        all_terms = query_input.split()
        query_terms = all_terms[:MAX_QTERMS]   # Limit to MAX_QTERMS words.

        # ── SCORE: Calculate relevance for each page ─────────
        for pg in pages:
            score_page(pg, query_terms)

        # ── SORT: Highest score first ─────────────────────────
        sorted_pages = sorted(pages, key=lambda pg: pg.score, reverse=True)
        # key=lambda pg: pg.score  → sort by the .score attribute
        # reverse=True             → highest score first (descending)

        # ── DISPLAY: Show top 5 results ──────────────────────
        display_results(sorted_pages, top_n=5)


# ── ENTRY POINT ───────────────────────────────────────────────
if __name__ == "__main__":
    # This block only runs when you execute this file directly:
    #     python search_engine.py
    # It does NOT run if this file is imported by another script.
    main()