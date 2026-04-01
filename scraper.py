import requests
import time
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from config import WEBDEV_KEYWORDS, AFRICAN_COUNTRIES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def is_webdev_related(text):
    return any(kw in text.lower() for kw in WEBDEV_KEYWORDS)

def is_african(text):
    return any(c in text.lower() for c in AFRICAN_COUNTRIES)

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
        for cat in ["web", "cpg"]:
            url = f"https://{city_code}.craigslist.org/search/{cat}?query=web+developer+website&sort=date"
            try:
                res = requests.get(url, headers=HEADERS, timeout=20)
                if res.status_code != 200:
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
                    if not title or not is_webdev_related(title):
                        continue
                    if is_african(title):
                        continue
                    if link and not link.startswith("http"):
                        link = f"https://{city_code}.craigslist.org{link}"
                    leads.append({
                        "title": title,
                        "source": f"Craigslist — {city_name}",
                        "platform": "Craigslist",
                        "author": "Local Business Owner",
                        "budget": price if price else extract_budget(title),
                        "posted": "Today",
                        "link": link or f"https://{city_code}.craigslist.org",
                        "preview": f"A business in {city_name} is looking for web development help. Click to view full post and contact them directly.",
                        "contact": link or f"https://{city_code}.craigslist.org"
                    })
                time.sleep(2)
            except Exception as e:
                print(f"[Craigslist] {city_name} error: {e}")
                time.sleep(1)
    print(f"[Craigslist] {len(leads)} leads found")
    return leads

def fetch_indiehackers():
    leads = []
    try:
        url = "https://www.indiehackers.com/posts?sort=newest"
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            posts = soup.select("a.post-preview__title, .content-card__title a, a[href*='/post/']")
            for post in posts:
                title = post.get_text(strip=True)
                href = post.get("href", "")
                link = f"https://www.indiehackers.com{href}" if href.startswith("/") else href
                if not title or not is_webdev_related(title):
                    continue
                if is_african(title):
                    continue
                leads.append({
                    "title": title,
                    "source": "Indie Hackers",
                    "platform": "IndieHackers",
                    "author": "Startup Founder",
                    "budget": extract_budget(title),
                    "posted": "Recent",
                    "link": link,
                    "preview": "A startup founder on Indie Hackers is looking for web development help. These are serious buyers with real products.",
                    "contact": link
                })
        print(f"[IndieHackers] {len(leads)} leads found")
    except Exception as e:
        print(f"[IndieHackers] Error: {e}")
    return leads

def fetch_producthunt():
    leads = []
    try:
        url = "https://www.producthunt.com/discussions"
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200:
            print(f"[ProductHunt] Status: {res.status_code}")
            return leads
        soup = BeautifulSoup(res.text, "html.parser")
        posts = soup.select("a[href*='/discussions/']")
        seen_links = set()
        for post in posts:
            title = post.get_text(strip=True)
            link = post.get("href", "")
            if not link.startswith("http"):
                link = f"https://www.producthunt.com{link}"
            if not title or link in seen_links:
                continue
            if not is_webdev_related(title):
                continue
            if is_african(title):
                continue
            seen_links.add(link)
            leads.append({
                "title": title,
                "source": "Product Hunt",
                "platform": "ProductHunt",
                "author": "Tech Founder",
                "budget": extract_budget(title),
                "posted": "Recent",
                "link": link,
                "preview": "A tech founder on Product Hunt is discussing web development needs. These are serious entrepreneurs with real budgets.",
                "contact": link
            })
        print(f"[ProductHunt] {len(leads)} leads found")
    except Exception as e:
        print(f"[ProductHunt] Error: {e}")
    return leads

def fetch_devto():
    leads = []
    try:
        url = "https://dev.to/api/articles?per_page=50&tag=hiring"
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"[DEV.to] Status: {res.status_code}")
            return leads
        articles = res.json()
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=7)
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "") or ""
            full_text = f"{title} {description}"
            if not is_webdev_related(full_text):
                continue
            if is_african(full_text):
                continue
            if not any(w in full_text.lower() for w in [
                "hiring", "looking for", "need", "want", "seeking", "budget"
            ]):
                continue
            published = article.get("published_at", "")
            if published:
                try:
                    pub_date = datetime.strptime(published[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if pub_date < cutoff:
                        continue
                except Exception:
                    pass
            author = article.get("user", {}).get("name", "Developer")
            link = article.get("url", "https://dev.to")
            leads.append({
                "title": title,
                "source": "DEV.to",
                "platform": "DEVto",
                "author": author,
                "budget": extract_budget(full_text),
                "posted": published[:10] if published else "Recent",
                "link": link,
                "preview": description[:250] + "..." if len(description) > 250 else description,
                "contact": link
            })
        print(f"[DEV.to] {len(leads)} leads found")
    except Exception as e:
        print(f"[DEV.to] Error: {e}")
    return leads

def fetch_all_leads():
    print("[INFO] Starting WebDev Lead Scraper...")
    all_leads = []
    all_leads += fetch_craigslist()
    all_leads += fetch_indiehackers()
    all_leads += fetch_producthunt()
    all_leads += fetch_devto()
    seen = set()
    unique = []
    for lead in all_leads:
        key = lead["title"].lower().strip()[:80]
        if key not in seen:
            seen.add(key)
            unique.append(lead)
    print(f"[TOTAL] {len(unique)} unique webdev leads found")
    return unique
