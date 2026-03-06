from collections import defaultdict
from config import SIGNALS, MIN_SCORE
from extractor import extract_companies


def detect_signals(text: str) -> dict:
    """Return which signals are present in the text."""
    text_lower = text.lower()
    found = {}
    for signal_key, signal_data in SIGNALS.items():
        for keyword in signal_data["keywords"]:
            if keyword in text_lower:
                found[signal_key] = signal_data
                break
    return found


def score_articles(articles: list[dict]) -> list[dict]:
    """
    For each article, extract companies and detected signals.
    Aggregate by company name across all articles.
    Returns a sorted list of company dicts with scores.
    """
    # company_name -> { signals: {signal_key: data}, articles: [...], score: int }
    company_map = defaultdict(lambda: {"signals": {}, "articles": [], "score": 0})

    for article in articles:
        full_text = f"{article['title']} {article['summary']}"
        signals_found = detect_signals(full_text)

        if not signals_found:
            continue  # skip articles with no relevant signals

        companies = extract_companies(full_text)

        for company in companies:
            key = company.lower().strip()
            entry = company_map[key]

            # Use the most common capitalisation seen
            if not entry.get("name"):
                entry["name"] = company

            # Merge signals (don't double-count same signal type)
            for sig_key, sig_data in signals_found.items():
                if sig_key not in entry["signals"]:
                    entry["signals"][sig_key] = sig_data

            # Add article if not already present
            article_links = {a["link"] for a in entry["articles"]}
            if article["link"] not in article_links:
                entry["articles"].append(article)

    # Calculate scores and filter
    results = []
    for key, data in company_map.items():
        if not data.get("name"):
            continue

        score = sum(s["score"] for s in data["signals"].values())
        score = min(score, 100)  # cap at 100

        if score < MIN_SCORE:
            continue

        signal_labels = [s["label"] for s in data["signals"].values()]

        results.append({
            "name": data["name"],
            "score": score,
            "signals": signal_labels,
            "articles": data["articles"],
        })

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    print(f"[scorer] {len(results)} companies scored above threshold ({MIN_SCORE})")
    return results
