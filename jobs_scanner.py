import time
from collections import defaultdict

try:
    from jobspy import scrape_jobs
except ImportError:
    scrape_jobs = None

# Tech roles to search — broad enough to catch all IT hiring
TECH_QUERIES = [
    "software engineer",
    "software developer",
    "devops engineer",
    "data engineer",
    "cloud engineer",
    "IT manager",
    "cybersecurity analyst",
    "product manager technology",
    "infrastructure engineer",
    "tech lead",
]

# Jobs posted in the last 7 days
HOURS_OLD = 168

# Results per query
RESULTS_PER_QUERY = 50

# Minimum postings to count as a hiring signal
MIN_JOBS = 3

# Score bonuses by job count
JOB_COUNT_SCORE = [
    (20, 35),
    (10, 25),
    (3,  15),
]

# Companies to ignore (big tech not relevant for IT recruitment BD)
EXCLUDE_COMPANIES = {
    # Big tech
    "microsoft", "google", "amazon", "apple", "meta", "facebook",
    "ibm", "oracle", "salesforce", "sap",
    # Global consulting / outsourcing (compete with IT recruitment)
    "deloitte", "accenture", "capgemini", "wipro", "infosys", "tcs",
    "tata consultancy", "cognizant", "hcl", "ey", "kpmg", "pwc",
    "itc infotech", "e-solutions",
    # Recruitment agencies (not BD targets)
    "hays", "talenza", "experis", "experis australia", "itbility",
    "talent", "careerus solutions", "vivanti consulting", "whizdom",
    "nuage technology group", "isg", "paxus", "finite recruitment",
    "robert half", "hudson", "randstad", "manpower", "adecco",
    "jobgether", "alignerr", "mindrift", "crossing hurdles",
    # Government
    "australian taxation office", "queensland government",
    "australian government", "department of",
    # Job boards
    "targetjobs", "seek", "indeed", "linkedin",
    # Overseas-only roles
    "agoda",
}


def _job_score(count: int) -> int:
    for threshold, score in JOB_COUNT_SCORE:
        if count >= threshold:
            return score
    return 0


def fetch_job_counts() -> dict:
    """
    Scrape LinkedIn for AU tech job postings via JobSpy.
    Returns {company_key: {name, count, score, titles}}
    """
    if scrape_jobs is None:
        print("[jobs] python-jobspy not installed — skipping job scan.")
        return {}

    company_jobs = defaultdict(lambda: {"count": 0, "titles": [], "name": ""})

    for query in TECH_QUERIES:
        try:
            df = scrape_jobs(
                site_name=["linkedin"],
                search_term=query,
                location="Australia",
                results_wanted=RESULTS_PER_QUERY,
                hours_old=HOURS_OLD,
                verbose=0,
            )

            if df is None or df.empty:
                continue

            for _, row in df.iterrows():
                company = str(row.get("company") or "").strip()
                title = str(row.get("title") or "").strip()
                location = str(row.get("location") or "").lower()

                if not company or company.lower() in EXCLUDE_COMPANIES:
                    continue

                # Filter companies that are clearly recruiters/staffing firms
                company_lower = company.lower()
                recruitment_words = [
                    "recruitment", "recruiter", "staffing", "resourcing",
                    "talent solutions", "talent group", "consulting group",
                    "labour hire", "labor hire", "contracting",
                ]
                if any(w in company_lower for w in recruitment_words):
                    continue

                # Skip jobs clearly not based in Australia
                au_terms = ["australia", "sydney", "melbourne", "brisbane",
                            "perth", "adelaide", "canberra", "remote"]
                if location and not any(t in location for t in au_terms):
                    continue

                key = company.lower()
                company_jobs[key]["name"] = company
                company_jobs[key]["count"] += 1
                if title and title not in company_jobs[key]["titles"]:
                    company_jobs[key]["titles"].append(title)

            time.sleep(1)  # polite delay between queries

        except Exception as e:
            print(f"[jobs] Error for query '{query}': {e}")

    # Filter and score
    results = {}
    for key, data in company_jobs.items():
        if data["count"] < MIN_JOBS:
            continue
        results[key] = {
            "name": data["name"],
            "count": data["count"],
            "score": _job_score(data["count"]),
            "titles": data["titles"][:3],
        }

    print(f"[jobs] {len(results)} companies with {MIN_JOBS}+ open tech roles on LinkedIn AU")
    return results
