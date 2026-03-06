#!/usr/bin/env python3
"""
Latitude IT — BD Signal Scanner
Scans Google News for Australian companies showing hiring signals,
scores them, and sends a daily email digest.

Usage:
    python main.py              # run scan + send email
    python main.py --preview    # run scan + print results (no email)
"""

import sys
from scanner import fetch_articles
from scorer import score_articles
from emailer import send_digest, build_html


def print_preview(companies: list[dict]):
    """Print results to terminal for testing."""
    print("\n" + "=" * 60)
    print(f"  BD SIGNAL REPORT — {len(companies)} companies found")
    print("=" * 60)

    if not companies:
        print("  No companies found above the minimum score threshold.")
        return

    for co in companies:
        print(f"\n  [{co['score']:>3}/100]  {co['name']}")
        print(f"           Signals: {', '.join(co['signals'])}")
        for a in co["articles"][:2]:
            print(f"           - {a['title'][:80]}")

    print("\n" + "=" * 60)


def main():
    preview_mode = "--preview" in sys.argv

    print("[main] Starting BD Signal Scanner...")

    # 1. Fetch articles from Google News
    articles = fetch_articles()

    if not articles:
        print("[main] No articles fetched. Check your internet connection.")
        return

    # 2. Score companies
    companies = score_articles(articles)

    # 3. Output
    if preview_mode:
        print_preview(companies)
        print("\n[main] Preview mode — no email sent.")
        print("[main] Run without --preview to send the email digest.")
    else:
        send_digest(companies)
        print(f"[main] Done. {len(companies)} companies in today's digest.")


if __name__ == "__main__":
    main()
