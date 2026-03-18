# Web Scraper Tools

Two Python scripts for web scraping and multi‑source search.

## Scripts

### `fetch_and_extract.py`
- Fetches HTML from a URL and extracts clean text
- Outputs JSON with title, excerpt, and length
- Command‑line: `python fetch_and_extract.py <url> --out output.json`

### `search_mesh.py`
- Searches multiple sources (DuckDuckGo, Reddit, GitHub, YouTube, Hacker News)
- Returns structured results in JSON, CSV, and Markdown formats
- Command‑line: `python search_mesh.py "query" --sources duckduckgo,reddit,github`

## Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/AustyVoankark/web-scraper-tools.git
   cd web-scraper-tools
   ```

2. Install dependencies (none required – uses standard library)

3. Run a script:
   ```bash
   python fetch_and_extract.py https://example.com
   ```

## Features
- No external dependencies (pure Python)
- Respectful rate‑limiting (1‑second delays between sources)
- Outputs in multiple formats (JSON, CSV, Markdown)
- User‑agent spoofing to avoid blocks

## License
MIT