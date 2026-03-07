import re
from collections import defaultdict
from config import SIGNALS, MIN_SCORE
from extractor import extract_companies


# Funding size → score override (replaces the flat +40)
FUNDING_SIZE_SCORE = [
    (500,  85),  # $500M+
    (200,  75),  # $200M–$499M
    (100,  65),  # $100M–$199M
    (50,   55),  # $50M–$99M
    (20,   45),  # $20M–$49M
    (5,    35),  # $5M–$19M
    (0,    20),  # under $5M / seed
]


def extract_funding_amount(text: str) -> float | None:
    """
    Pull the largest dollar figure from the text (in millions AUD/USD).
    Returns amount in millions, or None if not found.
    """
    text_lower = text.lower()

    # Match patterns like: $75M, $75 million, A$30m, US$200M, $1.2B, $1.2 billion
    patterns = [
        r'[\$a-z]{0,3}\$?([\d,]+\.?\d*)\s*billion',   # X billion
        r'[\$a-z]{0,3}\$?([\d,]+\.?\d*)\s*bn',         # X bn
        r'[\$a-z]{0,3}\$?([\d,]+\.?\d*)\s*million',    # X million
        r'[\$a-z]{0,3}\$?([\d,]+\.?\d*)\s*m\b',        # $75m
        r'[\$a-z]{0,3}\$?([\d,]+\.?\d*)m\b',           # $75M (no space)
    ]

    amounts = []
    for pattern in patterns:
        for match in re.finditer(pattern, text_lower):
            try:
                val = float(match.group(1).replace(",", ""))
                if "billion" in pattern or "bn" in pattern:
                    val *= 1000  # convert to millions
                amounts.append(val)
            except ValueError:
                pass

    return max(amounts) if amounts else None


def funding_score(amount_millions: float | None) -> int:
    """Convert funding amount to a score."""
    if amount_millions is None:
        return SIGNALS["funding"]["score"]  # fallback to flat score

    for threshold, score in FUNDING_SIZE_SCORE:
        if amount_millions >= threshold:
            return score

    return 20  # floor


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
    company_map = defaultdict(lambda: {
        "signals": {}, "articles": [], "funding_amount": None
    })

    for article in articles:
        full_text = f"{article['title']} {article['summary']}"
        signals_found = detect_signals(full_text)

        if not signals_found:
            continue

        companies = extract_companies(full_text)

        # Extract funding amount once per article
        article_funding = None
        if "funding" in signals_found:
            article_funding = extract_funding_amount(full_text)

        for company in companies:
            key = company.lower().strip()
            entry = company_map[key]

            if not entry.get("name"):
                entry["name"] = company

            # Merge signals
            for sig_key, sig_data in signals_found.items():
                if sig_key not in entry["signals"]:
                    entry["signals"][sig_key] = sig_data

            # Keep the largest funding amount seen across articles
            if article_funding:
                if entry["funding_amount"] is None or article_funding > entry["funding_amount"]:
                    entry["funding_amount"] = article_funding

            # Add article if not already present
            article_links = {a["link"] for a in entry["articles"]}
            if article["link"] not in article_links:
                entry["articles"].append(article)

    # Calculate scores and filter
    results = []
    for key, data in company_map.items():
        if not data.get("name"):
            continue

        score = 0
        for sig_key, sig_data in data["signals"].items():
            if sig_key == "funding":
                score += funding_score(data["funding_amount"])
            else:
                score += sig_data["score"]

        score = min(score, 100)

        if score < MIN_SCORE:
            continue

        signal_labels = []
        for sig_key, sig_data in data["signals"].items():
            if sig_key == "funding" and data["funding_amount"]:
                amt = data["funding_amount"]
                if amt >= 1000:
                    label = f"Funding / IPO (${amt/1000:.1f}B)"
                else:
                    label = f"Funding / IPO (${amt:.0f}M)"
                signal_labels.append(label)
            else:
                signal_labels.append(sig_data["label"])

        results.append({
            "name": data["name"],
            "score": score,
            "signals": signal_labels,
            "articles": data["articles"],
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    print(f"[scorer] {len(results)} companies scored above threshold ({MIN_SCORE})")
    return results
