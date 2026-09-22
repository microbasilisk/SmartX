#!/usr/bin/env python3
"""
Writes sitemap.xml with a lastmod taken from the page, not typed by hand.

## Plain version

A sitemap tells a search engine when a page last changed. Ours said 14 September while the page
had changed on the 22nd. A stale date is worse than no date: it is an instruction to a crawler
NOT to bother re-reading, so a week of changes stays invisible.

It went stale for the ordinary reason a typed fact goes stale. Somebody has to remember to
change it in a second place, and nobody does. So the date is read from the file itself: the last
commit that touched index.html, falling back to the file's own modified time outside a git
checkout. Run it and commit the result.

  python3 tools/make-sitemap.py

Standard library and git only, so it runs anywhere this site is checked out. The same reasoning
as tools/make-favicon.py: a build step that needs tools a machine may not have is a build step
that quietly stops being run.
"""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = [("index.html", "https://smartx.finance/")]


def last_changed(path: Path) -> str:
    """The date the page last really changed, as YYYY-MM-DD."""
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "log", "-1", "--format=%cs", "--", path.name],
            capture_output=True, text=True, timeout=10, check=False,
        )
        stamp = out.stdout.strip()
        # A file staged but never committed has no log line. Its own timestamp is the honest
        # answer then, and is never in the future, which a typed date can be.
        if out.returncode == 0 and len(stamp) == 10:
            return stamp
    except (OSError, subprocess.SubprocessError):
        pass
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")


def main() -> int:
    entries = []
    for name, loc in PAGES:
        page = ROOT / name
        if not page.exists():
            print(f"  missing: {name}", file=sys.stderr)
            return 1
        entries.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{last_changed(page)}</lastmod>\n  </url>")

    body = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(entries) + "\n</urlset>\n")
    (ROOT / "sitemap.xml").write_text(body)
    for line in entries:
        print("  " + line.strip().replace("\n", " "))
    print("  wrote sitemap.xml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
