#!/usr/bin/env python3
"""Check every URL in a Markdown file and report the ones that do not work.

Python standard library only -- no pip install, no API keys, no network
dependencies beyond an HTTP client.

Usage:
    python3 tools/check_links.py                 # checks README.md
    python3 tools/check_links.py docs/notes.md
    python3 tools/check_links.py README.md -v    # list every URL, not just problems
    python3 tools/check_links.py --workers 8 README.md

Exit codes:
    0  every link resolved
    1  at least one link is dead (404/410/DNS failure/connection failure)
    2  misuse (file missing, bad arguments)

What counts as a problem:

* ``DEAD``     -- the URL returned a client/server error that means the page is
                 gone or unreachable: 400, 404, 410, 5xx, DNS failure, refused
                 connection, TLS failure, timeout. These must be fixed.
* ``BLOCKED``  -- the site answered, but refuses automated clients (401, 403,
                 405, 406, 429, the 999 status some sites return, or a
                 Cloudflare "Just a moment" interstitial). The URL is alive but
                 cannot be confirmed from a script; a human should open it once.

A link that is ``OK`` may have been redirected; the final URL is printed when it
differs from the one in the file, so stale redirects stay visible.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Status codes that mean "the site is up, it just does not want a robot".
BLOCKED_CODES = {401, 402, 403, 405, 406, 409, 429, 999}

URL_RE = re.compile(r"https?://[^\s<>\"'\)\]\}`,]+")

# Trailing characters that are punctuation in prose, not part of the URL.
TRAILING_JUNK = ".,;:!?*_~-"

# Hosts used in examples/wording rather than as real destinations.
SKIP_HOSTS = {"example.com", "localhost", "127.0.0.1", "your-domain.com"}


def extract_urls(text: str) -> list[str]:
    """Return the unique URLs in *text*, in the order they first appear."""
    seen: dict[str, None] = {}
    for raw in URL_RE.findall(text):
        url = raw.rstrip(TRAILING_JUNK)
        # Markdown sometimes wraps links in <...>; strip the leftovers.
        url = url.rstrip(">")
        host = urllib.parse.urlsplit(url).netloc.split("@")[-1].split(":")[0].lower()
        if host in SKIP_HOSTS or not host:
            continue
        seen.setdefault(url, None)
    return list(seen)


def check(url: str, timeout: float) -> tuple[str, int | None, str, str]:
    """Return (status, http_code, detail, final_url) for *url*."""
    request = urllib.request.Request(url, headers=BROWSER_HEADERS, method="GET")
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            body = response.read(2048)
            final = response.geturl()
            detail = ""
            low = body.lower()
            if response.status in BLOCKED_CODES:
                return "BLOCKED", response.status, "refused automated client", final
            if b"just a moment" in low or b"cf-browser-verification" in low:
                return "BLOCKED", response.status, "Cloudflare challenge", final
            return "OK", response.status, detail, final
    except urllib.error.HTTPError as exc:
        code = exc.code
        if code in BLOCKED_CODES:
            return "BLOCKED", code, "refused automated client", url
        if 300 <= code < 400:
            return "OK", code, "redirect", url
        return "DEAD", code, f"HTTP {code}", url
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, ssl.SSLError):
            return "DEAD", None, f"TLS failure: {reason}", url
        if isinstance(reason, socket.timeout):
            return "DEAD", None, "timeout", url
        text = str(reason)
        if "Name or service not known" in text or "nodename nor servname" in text:
            return "DEAD", None, "DNS failure", url
        return "DEAD", None, f"connection failure: {text}", url
    except (socket.timeout, TimeoutError):
        return "DEAD", None, "timeout", url
    except Exception as exc:  # noqa: BLE001 - report anything else as dead
        return "DEAD", None, f"{type(exc).__name__}: {exc}", url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", default=["README.md"],
                        help="Markdown files to scan (default: README.md)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print every URL, not just the problems")
    parser.add_argument("-t", "--timeout", type=float, default=20.0,
                        help="per-request timeout in seconds (default: 20)")
    parser.add_argument("-w", "--workers", type=int, default=10,
                        help="parallel requests (default: 10)")
    args = parser.parse_args(argv)

    paths = [Path(name) for name in args.files]
    missing = [p for p in paths if not p.is_file()]
    if missing:
        for path in missing:
            print(f"no such file: {path}", file=sys.stderr)
        return 2

    pairs: list[tuple[Path, str]] = []
    for path in paths:
        for url in extract_urls(path.read_text(encoding="utf-8")):
            pairs.append((path, url))

    unique = list(dict.fromkeys(url for _, url in pairs))
    print(f"Scanning {len(unique)} unique URL(s) from "
          f"{', '.join(str(p) for p in paths)} ...\n")

    results: dict[str, tuple[str, int | None, str, str]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(check, url, args.timeout): url for url in unique}
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            results[url] = future.result()

    ok = blocked = dead = 0
    problems: list[tuple[str, str, str, int | None, str, str]] = []
    for path, url in pairs:
        status, code, detail, final = results[url]
        if status == "OK":
            ok += 1
        elif status == "BLOCKED":
            blocked += 1
        else:
            dead += 1
        if status != "OK" or args.verbose:
            problems.append((str(path), url, status, code, detail, final))

    if problems:
        print(f"{'FILE':<24} {'STATUS':<8} {'CODE':<6} URL")
        for path, url, status, code, detail, final in problems:
            code_text = str(code) if code else "-"
            note = f"  ({detail})" if detail else ""
            print(f"{path:<24} {status:<8} {code_text:<6} {url}{note}")
            if final and final != url and status == "OK":
                print(f"{'':<24} {'':<8} {'':<6}   -> redirected to {final}")
        print()

    checked = ok + blocked + dead
    print(f"{checked} link check(s): {ok} OK, {blocked} blocked-by-site, {dead} dead")
    if dead:
        print("\nDead links must be fixed, replaced or removed.")
    if blocked:
        print("Blocked links are live but unverifiable from a script -- "
              "open them once by hand to confirm.")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
