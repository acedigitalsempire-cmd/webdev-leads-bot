import requests
import time
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from config import WEBDEV_KEYWORDS, AFRICAN_COUNTRIES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Words that indicate employment not freelance gigs
EMPLOYMENT_WORDS = [
    "full-time", "full time", "part-time", "part time", "internship",
    "intern", "salary", "in-person", "in person", "on-site", "onsite",
    "employee", "employment", "office", "w2", "benefits", "401k",
    "annual", "per year", "per annum", "hours per week", "weekly pay",
    "bi-weekly", "hired staff", "permanent", "long term employee",
    "join our team", "join our company", "we are hiring", "we're hiring",
    "apply now", "send resume", "send cv", "submit resume"
]

# Words that confirm it's a freelance gig/project
FREELANCE_WORDS = [
    "freelance", "freelancer", "gig", "project", "one-time", "one time",
    "contract", "contractor", "need someone to build", "need a website",
    "build my website", "create my website", "design my website",
    "looking for someone to", "need help with", "budget", "quote",
    "fixed price", "milestone", "deliverable", "remote only",
    "work from anywhere", "independent contractor"
]

def is_webdev_related(text):
    return any(kw in text.lower() for kw in WEBDEV_KEYWORDS)

def is_african(text):
    return any(c in text.lower() for c in AFRICAN_COUNTRIES)

def is_employment(text):
    text_lower = text.lower()
    return any(word in text_lower for word in EMPLOYMENT_WORDS)

def is_freelance_gig(text):
    text_lower = text.lower()
    return any(word in text_lower for word in FREELANCE_WORDS)

def extract_budget(text):
    import re
    patterns = [
        r'\$[\d,]+(?:k)?(?:\s*-\s*\$[\d,]+(?:k)?)?',
        r'[\d,]+\s*(?:USD|usd|dollars)',
        r'budget[:\s]+\$?[\d,]+',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return "Not specified"


# ─────────────────────────────────────────
# SOURCE 1: Craigslist GIGS section only
# "cpg" = computer gigs (one-time projects)
# NOT jobs section
# ─────────────────────────────────────────
def fetch_craigslist():
    leads = []
    cities = [
        ("newyork", "New York, USA"),
        ("losangeles", "Los Angeles, USA"),
        ("chicago", "Chicago, USA"),
        ("houston", "Houston, USA"),
        ("austin", "Austin, USA"),
        ("seattle", "Seattle, USA"),
        ("boston", "Boston, USA"),
        ("sfbay", "San Francisco, USA"),
        ("dallas", "Dallas, USA"),
        ("miami", "Miami, USA"),
        ("toronto", "Toronto, Canada"),
        ("vancouver", "Vancouver, Canada"),
        ("london", "London, UK"),
    ]

    for city_code, city_name in cities:
        # Only search "cpg" = computer gigs (freelance projects)
        url = f"https://{city_code}.craigslist.org/search/cpg?sort=date"
        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
            if res.status_code != 200:
                time.sleep(1)
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            listings = soup.select("li.cl-static-search-result, .result-row")

            for listing in listings:
                title_el = listing.select_one(".label, .result-title, a")
                link_el = listing.select_one("a")
                price_el = listing.select_one(".priceinfo, .result-price")

                title = title_el.get_text(strip=True) if title_el else ""
                link = link_el.get("href", "") if link_el else ""
                price = price_el.get_text(strip=True) if price_el else ""

                if not title:
                    continue
                if not is_webdev_related(title):
                    continue
                if is_african(title):
                    continue
                if is_employment(title):
                    continue

                if link and not link.startswith("http"):
                    link = f"https://{city_code}.craigslist.org{link}"

                budget = price if price else extract_budget(title)

                leads.append({
                    "title": title,
                    "source": f"Craigslist Gigs — {city_name}",
                    "platform": "Craigslist",
                    "author": "Local Business Owner",
                    "budget": budget if budget else "Not specified",
                    "posted": "Today",
                    "link": link or f"https://{city_code}.craigslist.org/search/cpg",
                    "preview": f"A client in {city_name} posted a one-time web project on Craigslist Gigs. Direct contact, no middleman, no competition.",
                    "contact": link or f"https://{city_code}.craigslist.org/search/cpg"
                })

            print(f"[Craigslist] {city_name}: {len(listings)} scanned")
            time.sleep(2)

        except Exception as e:
            print(f"[Craigslist] {city_name} error: {e}")
            time.sleep(1)

    print(f"[Craigslist] Total leads: {len(leads)}")
    return leads


# ─────────────────────────────────────────
# SOURCE 2: PeoplePerHour Noticeboard
# Clients post projects BEFORE freelancers bid
# Very early access = very low competition
# ─────────────────────────────────────────
def fetch_peopleperhour():
    leads = []
    try:
        url = "https://www.peopleperhour.com/freelance-jobs/it-technical/web-development"
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200:
            print(f"[PeoplePerHour] Status: {res.status_code}")
            return leads

        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select("a[href*='/job/']")
        seen = set()

        for listing in listings:
            title = listing.get_text(strip=True)
            link = listing.get("href", "")
            if not link.startswith("http"):
                link = f"https://www.peopleperhour.com{link}"

            if not title or link in seen or len(title) < 10:
                continue
            if not is_webdev_related(title):
                continue
            if is_african(title):
                continue
            if is_employment(title):
                continue

            seen.add(link)
            leads.append({
                "title": title,
                "source": "PeoplePerHour",
                "platform": "PeoplePerHour",
                "author": "Client",
                "budget": extract_budget(title),
                "posted": "Recent",
                "link": link,
                "preview": "A client posted this web development project on PeoplePerHour before most freelancers have seen it. Low competition window.",
                "contact": link
            })

        print(f"[PeoplePerHour] {len(leads)} leads found")
    except Exception as e:
        print(f"[PeoplePerHour] Error: {e}")
    return leads


# ─────────────────────────────────────────
# SOURCE 3: Guru.com Job Board
# Clients post projects publicly
# Much less competition than Upwork/Fiverr
# ─────────────────────────────────────────
def fetch_guru():
    leads = []
    try:
        url = "https://www.guru.com/d/jobs/cat/it-programming/subcat/web-development/"
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200:
            print(f"[Guru] Status: {res.status_code}")
            return leads

        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select(".jobList .jobRecord, .serviceItem, a[href*='/d/jobs/id/']")
        seen = set()

        for listing in listings:
            title_el = listing.select_one("h2, h3, .jobTitle, a")
            link_el = listing if listing.name == "a" else listing.select_one("a")
            budget_el = listing.select_one(".jobBudget, .budget, .price")

            title = title_el.get_text(strip=True) if title_el else ""
            link = link_el.get("href", "") if link_el else ""
            budget_text = budget_el.get_text(strip=True) if budget_el else ""

            if not link.startswith("http"):
                link = f"https://www.guru.com{link}"

            if not title or link in seen or len(title) < 10:
                continue
            if not is_webdev_related(title):
                continue
            if is_african(title):
                continue
            if is_employment(title):
                continue

            seen.add(link)
            budget = budget_text if budget_text else extract_budget(title)

            leads.append({
                "title": title,
                "source": "Guru.com",
                "platform": "Guru",
                "author": "Client",
                "budget": budget if budget else "Not specified",
                "posted": "Recent",
                "link": link,
                "preview": "A client posted this web development project on Guru.com. Guru has far less competition than Upwork — most clients get only 2-5 proposals.",
                "contact": link
            })

        print(f"[Guru] {len(leads)} leads found")
    except Exception as e:
        print(f"[Guru] Error: {e}")
    return leads


# ─────────────────────────────────────────
# SOURCE 4: Workana
# USA + Latin America clients
# Much less saturated than Upwork
# Free to view projects without account
# ─────────────────────────────────────────
def fetch_workana():
    leads = []
    try:
        url = "https://www.workana.com/jobs?category=it-programming&subcategory=web-programming&language=en"
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200:
            print(f"[Workana] Status: {res.status_code}")
            return leads

        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select(".project-item, .job-item, a[href*='/job/']")
        seen = set()

        for listing in listings:
            title_el = listing.select_one("h2, h3, .title, a")
            link_el = listing if listing.name == "a" else listing.select_one("a")
            budget_el = listing.select_one(".budget, .price, .amount")

            title = title_el.get_text(strip=True) if title_el else ""
            link = link_el.get("href", "") if link_el else ""
            budget_text = budget_el.get_text(strip=True) if budget_el else ""

            if not link.startswith("http"):
                link = f"https://www.workana.com{link}"

            if not title or link in seen or len(title) < 10:
                continue
            if not is_webdev_related(title):
                continue
            if is_african(title):
                continue
            if is_employment(title):
                continue

            seen.add(link)
            budget = budget_text if budget_text else extract_budget(title)

            leads.append({
                "title": title,
                "source": "Workana",
                "platform": "Workana",
                "author": "Client",
                "budget": budget if budget else "Not specified",
                "posted": "Recent",
                "link": link,
                "preview": "A client posted this web project on Workana. This platform has significantly less competition than Upwork with real budgets.",
                "contact": link
            })

        print(f"[Workana] {len(leads)} leads found")
    except Exception as e:
        print(f"[Workana] Error: {e}")
    return leads


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def fetch_all_leads():
    print("[INFO] Starting WebDev Lead Scraper...")
    all_leads = []

    all_leads += fetch_craigslist()
    all_leads += fetch_peopleperhour()
    all_leads += fetch_guru()
    all_leads += fetch_workana()

    # Deduplicate by title
    seen = set()
    unique = []
    for lead in all_leads:
        key = lead["title"].lower().strip()[:80]
        if key not in seen:
            seen.add(key)
            unique.append(lead)

    print(f"[TOTAL] {len(unique)} unique freelance webdev leads found")
    return unique
