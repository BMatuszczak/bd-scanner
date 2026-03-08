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

# Direct RSS feeds from Australian tech & business publications
AU_RSS_FEEDS = [
    ("SmartCompany",        "https://www.smartcompany.com.au/feed/"),
    ("Startup Daily",       "https://www.startupdaily.net/feed/"),
    ("ZDNet",               "https://www.zdnet.com/topic/australia/rss.xml"),
    ("Dynamic Business",    "https://dynamicbusiness.com.au/feed/"),
    ("Which-50",            "https://which-50.com/feed/"),
    ("Innovation Aus",      "https://www.innovationaus.com/feed/"),
]


def _parse_entry(entry, source_name):
    """Parse a feed entry into a standard article dict."""
    link = entry.get("link", "")

    published = None
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass

    return {
        "title": entry.get("title", ""),
        "summary": entry.get("summary", entry.get("description", "")),
        "link": link,
        "published": published,
        "source": source_name,
    }


def fetch_articles():
    """Fetch articles from Google News RSS + direct AU publication feeds."""
    all_articles = []
    seen_urls = set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_ARTICLE_AGE_DAYS)

    # --- 1. Google News RSS queries ---
    for query in SEARCH_QUERIES:
        url = GOOGLE_NEWS_RSS.format(query=quote_plus(query))
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)

            for entry in feed.entries[:MAX_ARTICLES_PER_QUERY]:
                article = _parse_entry(
                    entry,
                    entry.get("source", {}).get("title", "Google News")
                )
                if not article["link"] or article["link"] in seen_urls:
                    continue
                if article["published"] and article["published"] < cutoff:
                    continue
                seen_urls.add(article["link"])
                all_articles.append(article)

            time.sleep(0.5)

        except Exception as e:
            print(f"[scanner] Google News error for '{query}': {e}")

    # --- 2. Direct AU publication RSS feeds ---
    for source_name, feed_url in AU_RSS_FEEDS:
        try:
            resp = requests.get(feed_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)

            added = 0
            for entry in feed.entries:
                article = _parse_entry(entry, source_name)
                if not article["link"] or article["link"] in seen_urls:
                    continue
                if article["published"] and article["published"] < cutoff:
                    continue
                seen_urls.add(article["link"])
                all_articles.append(article)
                added += 1

            print(f"[scanner] {source_name}: {added} articles")
            time.sleep(0.3)

        except Exception as e:
            print(f"[scanner] Feed error for {source_name}: {e}")

    print(f"[scanner] Total: {len(all_articles)} unique articles")
    return all_articles
