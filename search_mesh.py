#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path
from urllib.request import Request, urlopen

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"

SOURCES = {
    "duckduckgo": "https://html.duckduckgo.com/html/?q={q}",
    "reddit": "https://www.reddit.com/search/?q={q}",
    "github": "https://github.com/search?q={q}&type=repositories",
    "youtube": "https://www.youtube.com/results?search_query={q}",
    "hackernews": "https://hn.algolia.com/?q={q}",
}


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def strip_tags(text: str) -> str:
    text = re.sub(r"<script[\\s\\S]*?</script>", "", text, flags=re.I)
    text = re.sub(r"<style[\\s\\S]*?</style>", "", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\\s+", " ", text)
    return text.strip()


def parse_ddg(html: str, limit: int):
    results = []
    pattern = re.compile(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    snippets = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html, re.I | re.S)
    for i, m in enumerate(pattern.finditer(html)):
        url = strip_tags(m.group(1))
        title = strip_tags(m.group(2))
        snippet = strip_tags(snippets[i]) if i < len(snippets) else ""
        results.append({"title": title, "url": url, "snippet": snippet, "source": "duckduckgo"})
        if len(results) >= limit:
            break
    return results


def parse_github(html: str, limit: int):
    results = []
    for m in re.finditer(r'href="(/[^\"]+/[^\"]+)"[^>]*>\\s*<em>(.*?)</em>', html, re.I | re.S):
        repo = m.group(1)
        title = strip_tags(m.group(2))
        results.append({"title": title or repo.strip('/'), "url": f"https://github.com{repo}", "snippet": "", "source": "github"})
        if len(results) >= limit:
            break
    return results


def parse_reddit(html: str, limit: int):
    results = []
    for m in re.finditer(r'href="(/r/[^"]+/comments/[^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
        url = f"https://www.reddit.com{m.group(1)}"
        title = strip_tags(m.group(2))
        if title:
            results.append({"title": title, "url": url, "snippet": "", "source": "reddit"})
        if len(results) >= limit:
            break
    return results


def parse_youtube(html: str, limit: int):
    results = []
    for m in re.finditer(r'"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)"', html, re.S):
        vid, title = m.group(1), m.group(2)
        results.append({"title": title, "url": f"https://www.youtube.com/watch?v={vid}", "snippet": "", "source": "youtube"})
        if len(results) >= limit:
            break
    return results


def parse_hn(html: str, limit: int):
    results = []
    for m in re.finditer(r'"title":"([^"]+)".*?"url":"([^"]+)"', html, re.S):
        title, url = m.group(1), m.group(2).replace('\\u002F', '/').replace('\\/', '/')
        results.append({"title": title, "url": url, "snippet": "", "source": "hackernews"})
        if len(results) >= limit:
            break
    return results


def run_source(source: str, query: str, limit: int):
    url = SOURCES[source].format(q=urllib.parse.quote(query))
    html = fetch(url)
    if source == "duckduckgo":
        return parse_ddg(html, limit)
    if source == "github":
        return parse_github(html, limit)
    if source == "reddit":
        return parse_reddit(html, limit)
    if source == "youtube":
        return parse_youtube(html, limit)
    if source == "hackernews":
        return parse_hn(html, limit)
    return []


def dedupe(results):
    seen = set()
    out = []
    for r in results:
        key = r["url"]
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def save(results, out_base: Path):
    out_base.parent.mkdir(parents=True, exist_ok=True)
    with open(str(out_base) + ".json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    with open(str(out_base) + ".csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["title", "url", "snippet", "source"])
        w.writeheader()
        w.writerows(results)
    with open(str(out_base) + ".md", "w", encoding="utf-8") as f:
        f.write(f"# Search Mesh Results\n\n")
        for i, r in enumerate(results, 1):
            f.write(f"## {i}. {r['title']}\n- Source: {r['source']}\n- URL: {r['url']}\n- Snippet: {r['snippet']}\n\n")


def main():
    ap = argparse.ArgumentParser(description="Local fallback multi-source search")
    ap.add_argument("query")
    ap.add_argument("--sources", default="duckduckgo,reddit,github,youtube,hackernews")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--out", default="output/research-cache/search-results")
    args = ap.parse_args()

    all_results = []
    for src in [s.strip() for s in args.sources.split(",") if s.strip()]:
        try:
            all_results.extend(run_source(src, args.query, args.limit))
            time.sleep(1)
        except Exception as e:
            all_results.append({"title": f"ERROR: {src}", "url": "", "snippet": str(e), "source": src})
    all_results = dedupe(all_results)
    save(all_results, Path(args.out))
    print(json.dumps({"count": len(all_results), "out": args.out, "sources": args.sources.split(",")}, indent=2))


if __name__ == "__main__":
    main()
