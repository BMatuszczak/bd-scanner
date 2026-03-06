import feedparser
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus
import time

from config import SEARCH_QUERIES, MAX_ARTICLES_PER_QUERY, MAX_ARTICLE_AGE_DAYS

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-AU&gl=AU&ceid=AU:en"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BDScanner/1.0)"
}


def fetch_articles():
    """Fetch articles from Google News RSS for all configured queries."""
    all_articles = []
    seen_urls = set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_ARTICLE_AGE_DAYS)

    for query in SEARCH_QUERIES:
        url = GOOGLE_NEWS_RSS.format(query=quote_plus(query))
        try:
            # feedparser doesn't support custom headers natively, fetch manually
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)

            for entry in feed.entries[:MAX_ARTICLES_PER_QUERY]:
                link = entry.get("link", "")
                if link in seen_urls:
                    continue

                # Parse publish date
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                # Skip old articles
                if published and published < cutoff:
                    continue

                seen_urls.add(link)
                all_articles.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": link,
                    "published": published,
                    "source": entry.get("source", {}).get("title", "Unknown"),
                })

            time.sleep(0.5)  # polite delay between requests

        except Exception as e:
            print(f"[scanner] Error fetching query '{query}': {e}")

    print(f"[scanner] Fetched {len(all_articles)} unique articles")
    return all_articles
