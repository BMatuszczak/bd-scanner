import spacy
import re
from html.parser import HTMLParser

# Load spaCy model (run: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise RuntimeError(
        "spaCy model not found. Run: python -m spacy download en_core_web_sm"
    )

# Words to exclude from company extraction (too generic or false positives)
EXCLUDE_ORGS = {
    # Big tech (not BD targets for IT recruitment)
    "google", "facebook", "meta", "microsoft", "apple", "amazon", "aws",
    "linkedin", "twitter", "x", "tiktok", "uber", "airbnb",
    # Australian geography
    "australia", "australian", "sydney", "melbourne", "brisbane", "perth",
    "adelaide", "canberra", "hobart", "darwin", "victoria", "queensland",
    "nsw", "new south wales", "western australia", "south australia",
    "tasmania", "northern territory", "act",
    # Regions / blocs
    "anz", "apac", "asia pacific", "emea", "americas",
    # Govt / finance bodies
    "government", "parliament", "asx", "abn", "ato", "rba",
    # Days / months
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    # Generic suffixes
    "inc", "ltd", "pty", "llc", "corp", "the", "new",
    # Job titles used as ORG entities
    "cto", "cio", "ceo", "cfo", "coo", "cpo", "cco",
    "chief", "vp", "svp", "evp",
    # News sources
    "financeasia", "afr", "australian financial review", "reuters", "bloomberg",
    "techcrunch", "smartcompany", "itnews", "zdnet", "crunchbase",
    "business insider", "the guardian", "abc", "nine", "news.com.au",
    "igrow news", "startup daily", "mirage news", "asia gaming brief",
    "apdr", "asia pacific defence", "finsmes", "saas news", "the saas news",
    "asia digest", "channel", "series",
}

# Patterns that indicate a fragment, not a company name
FRAGMENT_PATTERNS = [
    r"^https?://",           # URLs
    r"^href=",               # HTML attributes
    r"\bsecures?\b",         # "Technologies Secures" fragments
    r"\bfunding\b",
    r"\blaunches?\b",
    r"\bappoints?\b",
    r"^\d",                  # starts with a number
]


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return " ".join(self.fed)


def strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    s = _HTMLStripper()
    s.feed(text)
    return s.get_data()


def extract_companies(text: str) -> list[str]:
    """Extract organisation names from text using spaCy NER."""
    clean_text = strip_html(text)
    doc = nlp(clean_text[:1000])  # limit to avoid slow processing on large texts
    companies = []

    for ent in doc.ents:
        if ent.label_ == "ORG":
            name = ent.text.strip()
            # Clean up common noise
            name = re.sub(r"\s+", " ", name)
            name = name.strip("'\".,;:")

            # Filter out low-quality extractions
            if len(name) < 3:
                continue
            if name.lower() in EXCLUDE_ORGS:
                continue
            # Check each word in the name against exclusion list
            words = name.lower().split()
            if words[0] in EXCLUDE_ORGS:
                continue
            if re.match(r"^\d+$", name):
                continue
            # Filter URL/HTML artifacts and sentence fragments
            if any(re.search(p, name, re.IGNORECASE) for p in FRAGMENT_PATTERNS):
                continue
            # Require at least one proper-cased word (real company names are capitalised)
            if not any(w[0].isupper() for w in name.split() if w):
                continue
            # Drop pure acronyms (all caps, 4 chars or fewer) like "EMEA", "CCO"
            if re.match(r'^[A-Z]{2,4}$', name):
                continue
            # Drop anything that looks like a news source suffix e.g. "- Mirage News"
            if name.startswith("- "):
                continue

            companies.append(name)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in companies:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique
