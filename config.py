import os
from dotenv import load_dotenv

load_dotenv()

# --- Email Settings ---
EMAIL_SENDER = os.getenv("EMAIL_SENDER")       # your Gmail address
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")   # Gmail App Password
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT") # where to send the digest

# --- Google News RSS queries (AU-focused, no API key needed) ---
SEARCH_QUERIES = [
    'australia funding "series A"',
    'australia funding "series B"',
    'australia funding "series C"',
    'australia startup raises million',
    'australia technology hiring',
    'australia tech company expanding',
    'australia "new office" technology',
    'australia CTO appointed',
    'australia CIO appointed',
    'australia tech IPO ASX',
    'australia startup headcount growth',
    'australia venture capital investment',
]

# --- Signals: keywords to detect + score weight ---
SIGNALS = {
    "funding": {
        "keywords": [
            "series a", "series b", "series c", "series d", "series e",
            "funding round", "raises", "raised", "secures funding",
            "venture capital", "vc funding", "investment round",
            "ipo", "asx listed", "public offering", "backed by",
        ],
        "score": 40,
        "label": "Funding / IPO",
    },
    "hiring": {
        "keywords": [
            "hiring", "headcount", "growing team", "new roles",
            "expanding team", "recruitment drive", "job openings",
            "hundreds of jobs", "creating jobs", "new positions",
            "workforce expansion", "talent acquisition",
        ],
        "score": 25,
        "label": "Hiring Surge",
    },
    "expansion": {
        "keywords": [
            "new office", "opening office", "expanding to", "new location",
            "new headquarters", "sydney office", "melbourne office",
            "brisbane office", "perth office", "australian office",
            "opens in australia", "launches in australia", "expands to australia",
        ],
        "score": 20,
        "label": "Office / Expansion",
    },
    "leadership": {
        "keywords": [
            "new cto", "new cio", "new cpo", "appoints cto", "appoints cio",
            "chief technology officer", "chief information officer",
            "chief product officer", "vp of engineering", "head of technology",
            "tech lead appointed", "new chief", "joins as cto", "joins as cio",
        ],
        "score": 15,
        "label": "New Tech Leadership",
    },
}

# Minimum score to include a company in the digest
MIN_SCORE = 15

# Max articles to process per query
MAX_ARTICLES_PER_QUERY = 20

# How many days back to consider articles (keep fresh)
MAX_ARTICLE_AGE_DAYS = 7
