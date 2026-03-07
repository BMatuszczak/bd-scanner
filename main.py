#!/usr/bin/env python3
"""
Latitude IT — BD Signal Scanner
Scans Google News + AU publications for hiring signals, scores companies
using news signals + Adzuna job counts, and sends a weekly email digest.

Usage:
    python main.py              # run scan + send email
    python main.py --preview    # run scan + print results (no email)
"""

import sys
from scanner import fetch_articles
from scorer import score_articles
from jobs_scanner import fetch_job_counts
from emailer import send_digest, build_html


def print_preview(companies: list[dict]):
    print("\n" + "=" * 60)
    print(f"  BD SIGNAL REPORT — {len(companies)} companies found")
    print("=" * 60)

    if not companies:
        print("  No companies found above the minimum score threshold.")
        return

    for co in companies:
        print(f"\n  [{co['score']:>3}/100]  {co['name']}")
        print(f"           Signals: {', '.join(co['signals'])}")
        if co.get("job_titles"):
            print(f"           Roles:   {', '.join(co['job_titles'])}")
        for a in co["articles"][:2]:
            print(f"           - {a['title'][:80]}")

    print("\n" + "=" * 60)


def main():
    preview_mode = "--preview" in sys.argv

    print("[main] Starting BD Signal Scanner...")

    # 1. Fetch news articles
    articles = fetch_articles()
    if not articles:
        print("[main] No articles fetched. Check your internet connection.")
        return

    # 2. Fetch Adzuna job counts (skips gracefully if no API key)
    job_counts = fetch_job_counts()

    # 3. Score companies
    companies = score_articles(articles, job_counts)

    # 4. Output
    if preview_mode:
        print_preview(companies)
        print("\n[main] Preview mode — no email sent.")
    else:
        send_digest(companies)
        print(f"[main] Done. {len(companies)} companies in today's digest.")


if __name__ == "__main__":
    main()
