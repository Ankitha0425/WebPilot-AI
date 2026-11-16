#!/usr/bin/env python3
"""Controlled website crawler CLI. Emits one JSON object to stdout."""
import argparse
import json
import re
import sys
import time
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

USER_AGENT = "WebPilotAI/1.0 (+educational demo)"
TIMEOUT = 15
MAX_TEXT_CHARS = 12000


def validate_url(raw):
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http:// and https:// URLs are allowed.")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing embedded credentials are not allowed.")
    # Reject localhost and common private/local hostnames to reduce SSRF risk.
    host = parsed.hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise ValueError("Localhost and local-network hostnames are not allowed.")
    return parsed


def robots_allowed(base_url, target_url):
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        response = requests.get(robots_url, headers={"User-Agent": USER_AGENT}, timeout=5)
        if response.status_code == 200:
            parser.parse(response.text.splitlines())
            return parser.can_fetch(USER_AGENT, target_url)
        # If robots.txt is unavailable, continue with conservative page limits.
        return True
    except requests.RequestException:
        return True


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def extract_page(url, response):
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
        tag.decompose()

    title = clean_text(soup.title.get_text(" ", strip=True)) if soup.title else ""
    headings = [clean_text(h.get_text(" ", strip=True)) for h in soup.find_all(["h1", "h2", "h3"])]
    headings = [h for h in headings if h][:20]
    description_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    description = clean_text(description_tag.get("content", "")) if description_tag else ""
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = clean_text(main.get_text(" ", strip=True))[:MAX_TEXT_CHARS]

    links = []
    for anchor in soup.find_all("a", href=True):
        absolute = urldefrag(urljoin(url, anchor["href"]))[0]
        p = urlparse(absolute)
        if p.scheme in ("http", "https"):
            links.append(absolute)

    return {
        "url": url,
        "status_code": response.status_code,
        "title": title,
        "meta_description": description,
        "headings": headings,
        "text": text,
        "links": list(dict.fromkeys(links))[:100],
    }


def make_summary(pages):
    snippets = []
    for page in pages:
        if page["title"]:
            snippets.append(page["title"])
        if page["meta_description"]:
            snippets.append(page["meta_description"])
        elif page["text"]:
            snippets.append(page["text"][:450])
        for heading in page["headings"][:3]:
            snippets.append(heading)
    # Remove duplicates while preserving order.
    unique = list(dict.fromkeys(s for s in snippets if s))
    if not unique:
        return "The pages were fetched, but no readable text could be extracted."
    return " ".join(unique[:12])[:1800]


def crawl(start_url, max_pages):
    parsed = validate_url(start_url)
    host = parsed.netloc.lower()
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    queue = deque([start_url])
    visited = set()
    pages = []
    errors = []

    while queue and len(pages) < max_pages:
        current = queue.popleft()
        current = urldefrag(current)[0]
        if current in visited:
            continue
        visited.add(current)

        p = urlparse(current)
        if p.netloc.lower() != host or p.scheme not in ("http", "https"):
            continue
        if not robots_allowed(start_url, current):
            errors.append({"url": current, "error": "Disallowed by robots.txt"})
            continue

        try:
            response = session.get(current, timeout=TIMEOUT, allow_redirects=True)
            final = urlparse(response.url)
            if final.netloc.lower() != host:
                errors.append({"url": current, "error": "Redirected outside the original host; skipped"})
                continue
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                errors.append({"url": current, "error": f"Skipped non-HTML content ({content_type or 'unknown'})"})
                continue

            page = extract_page(response.url, response)
            pages.append(page)
            for link in page["links"]:
                lp = urlparse(link)
                if lp.netloc.lower() == host and link not in visited and len(visited) + len(queue) < 100:
                    queue.append(link)
        except requests.RequestException as exc:
            errors.append({"url": current, "error": str(exc)[:300]})

    if not pages:
        raise RuntimeError("No pages could be crawled. Check the URL, network access, and robots.txt.")

    result = {
        "status": "success" if not errors else "partial_success",
        "source_url": start_url,
        "pages_crawled": len(pages),
        "summary": make_summary(pages),
        "pages": pages,
        "errors": errors,
        "execution": {
            "tool": "cli/crawler.py",
            "method": "Python CLI invoked by backend subprocess",
            "max_pages": max_pages,
            "same_host_only": True,
            "robots_txt_checked": True
        }
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="Crawl a public website and return structured JSON.")
    parser.add_argument("--url", required=True, help="Public website URL")
    parser.add_argument("--max-pages", type=int, default=5)
    args = parser.parse_args()

    if not 1 <= args.max_pages <= 5:
        print("max-pages must be between 1 and 5", file=sys.stderr)
        return 2

    try:
        validate_url(args.url)
        output = crawl(args.url, args.max_pages)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Crawler error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
