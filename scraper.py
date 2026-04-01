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

# ─────────────────────────────────────────
# SOURCE 1: Craigslist
# Real local business owners, no competition
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
                        "preview": f"A business in {city_name} is looking for web development help. Click to view full post and contact them directly — no middleman.",
                        "contact": link or f"https://{city_code}.craigslist.org"
                    })
                time.sleep(2)
            except Exception as e:
                print(f"[Craigslist] {city_name} error: {e}")
                time.sleep(1)

    print(f"[Craigslist] {len(leads)} leads found")
    return leads


# ─────────────────────────────────────────
# SOURCE 2: Indie Hackers
# Startup founders looking for developers
# Very serious buyers with real budgets
# ─────────────────────────────────────────
def fetch_indiehackers():
    leads = []
    try:
        # Indie Hackers posts endpoint
        url = "https://www.indiehackers.com/api/posts?order=newest&limit=50"
        res = requests.get(url, headers=HEADERS, timeout=20)

        if res.status_code != 200:
            # Fallback: scrape the page directly
            url2 = "https://www.indiehackers.com/posts?sort=newest"
            res2 = requests.get(url2, headers=HEADERS, timeout=20)
            if res2.status_code == 200:
                soup = BeautifulSoup(res2.text, "html.parser")
                posts = soup.select("a.post-preview__title, .content-card__title a")
                for post in posts:
                    title = post.get_text(strip=True)
                    link = "https://www.indiehackers.com" + post.get("href", "")
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
            print(f"[IndieHackers] {len(leads)} leads found via scraping")
            return leads

        posts = res.json() if isinstance(res.json(), list) else res.json().get("posts", [])
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=3)

        for post in posts:
            title = post.get("title", "") or post.get("name", "")
            body = post.get("body", "") or post.get("content", "")
            full_text = f"{title} {body}"

            if not is_webdev_related(full_text):
                continue
            if is_african(full_text):
                continue

            slug = post.get("slug", "") or post.get("id", "")
            link = f"https://www.indiehackers.com/post/{slug}" if slug else "https://www.indiehackers.com"
            author = post.get("userDisplayName", "") or post.get("username", "Founder")
            budget = extract_budget(full_text)
            preview = body[:250].strip() + "..." if len(body) > 250 else body

            leads.append({
                "title": title,
                "source": "Indie Hackers",
                "platform": "IndieHackers",
                "author": author,
                "budget": budget,
                "posted": "Recent",
                "link": link,
                "preview": preview or "Startup founder looking for web development help.",
                "contact": f"https://www.indiehackers.com/{author}"
            })

        print(f"[IndieHackers] {len(leads)} leads found")
    except Exception as e:
        print(f"[IndieHackers] Error: {e}")
    return leads


# ─────────────────────────────────────────
# SOURCE 3: Product Hunt Discussions
# Startups launching products, needing dev help
# USA/Canada/UK founders, very low competition
# ─────────────────────────────────────────
def fetch_producthunt():
    leads = []
    try:
        # Product Hunt discussions page
        url = "https://www.producthunt.com/discussions"
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200:
            print(f"[ProductHunt] Status: {res.status_code}")
            return leads

        soup = BeautifulSoup(res.text, "html.parser")

        # Find discussion links
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
            budget = extract_budget(title)

            leads.append({
                "title": title,
                "source": "Product Hunt",
                "platform": "ProductHunt",
                "author": "Tech Founder",
                "budget": budget,
                "posted": "Recent",
                "link": link,
                "preview": "A tech founder on Product Hunt is discussing web development needs. Product Hunt users are serious entrepreneurs with real budgets.",
                "contact": link
            })

        print(f"[ProductHunt] {len(leads)} leads found")
    except Exception as e:
        print(f"[ProductHunt] Error: {e}")
    return leads


# ─────────────────────────────────────────
# SOURCE 4: DEV.to
# Developers and founders posting help requests
# Free API, no auth needed
# ─────────────────────────────────────────
def fetch_devto():
    leads = []
    try:
        search_terms = [
            "need web developer",
            "looking for developer",
            "hire developer",
            "need website",
            "build website",
        ]

        for term in search_terms:
            url = f"https://dev.to/api/articles?per_page=20&tag=hiring"
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                continue

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
                budget = extract_budget(full_text)

                leads.append({
                    "title": title,
                    "source": "DEV.to",
                    "platform": "DEVto",
                    "author": author,
                    "budget": budget,
                    "posted": published[:10] if published else "Recent",
                    "link": link,
                    "preview": description[:250] + "..." if len(description) > 250 else description,
                    "contact": link
                })

            time.sleep(1)

        print(f"[DEV.to] {len(leads)} leads found")
    except Exception as e:
        print(f"[DEV.to] Error: {e}")
    return leads


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def fetch_all_leads():
    print("[INFO] Starting WebDev Lead Scraper...")
    all_leads = []

    all_leads += fetch_craigslist()
    all_leads += fetch_indiehackers()
    all_leads += fetch_producthunt()
    all_leads += fetch_devto()

    # Deduplicate
    seen = set()
    unique = []
    for lead in all_leads:
        key = lead["title"].lower().strip()[:80]
        if key not in seen:
            seen.add(key)
            unique.append(lead)

    print(f"[TOTAL] {len(unique)} unique webdev leads found")
    return unique# Locals posting "need website" with real budgets
# Very low competition — most devs ignore Craigslist
# ─────────────────────────────────────────────
def fetch_craigslist():
    leads = []

    # Major USA + Canada cities
    cities = [
        "newyork", "losangeles", "chicago", "houston", "phoenix",
        "philadelphia", "sanantonio", "dallas", "austin", "seattle",
        "boston", "miami", "denver", "atlanta", "toronto",
        "vancouver", "calgary", "montreal", "sfbay", "portland"
    ]

    for city in cities:
        url = f"https://{city}.craigslist.org/search/web?format=json"
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                # Try alternate URL format
                url2 = f"https://{city}.craigslist.org/search/cpg?query=web+developer&format=json"
                res = requests.get(url2, headers=HEADERS, timeout=15)
                if res.status_code != 200:
                    continue

            data = res.json()
            items = data.get("data", {}).get("items", []) if isinstance(data, dict) else []

            if not items:
                # Try parsing as list
                if isinstance(data, list):
                    items = data

            for item in items:
                if isinstance(item, list) and len(item) > 2:
                    title = str(item[2]) if len(item) > 2 else ""
                    post_id = str(item[0]) if item else ""
                    link = f"https://{city}.craigslist.org/cpg/{post_id}.html"
                elif isinstance(item, dict):
                    title = item.get("title", "")
                    link = item.get("url", f"https://{city}.craigslist.org")
                else:
                    continue

                if not title:
                    continue
                if not is_webdev_related(title):
                    continue
                if is_african(title):
                    continue

                budget = extract_budget(title)
                leads.append({
                    "title": title,
                    "source": f"Craigslist ({city})",
                    "platform": "Craigslist",
                    "author": "Local Business Owner",
                    "budget": budget,
                    "posted": "Recent",
                    "link": link,
                    "preview": f"Local business in {city.title()} looking for web development help.",
                    "contact": link
                })

            time.sleep(2)

        except Exception as e:
            print(f"[Craigslist] {city} error: {e}")
            time.sleep(1)
            continue

    print(f"[Craigslist] {len(leads)} leads found")
    return leads


# ─────────────────────────────────────────────
# SOURCE 3: GitHub Discussions & Issues
# Startups posting "looking for developer" publicly
# Very low competition — only developers see these
# ─────────────────────────────────────────────
def fetch_github():
    leads = []

    search_queries = [
        "need web developer",
        "looking for web developer",
        "hire wordpress developer",
        "need website built",
        "looking for frontend developer",
        "need landing page built",
    ]

    for query in search_queries:
        url = f"https://api.github.com/search/issues?q={requests.utils.quote(query)}&sort=created&order=desc&per_page=10"
        try:
            res = requests.get(url, headers={
                **HEADERS,
                "Accept": "application/vnd.github.v3+json"
            }, timeout=15)

            if res.status_code == 403:
                print(f"[GitHub] Rate limited — waiting 30s")
                time.sleep(30)
                continue
            if res.status_code != 200:
                continue

            data = res.json()
            items = data.get("items", [])

            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(days=7)

            for item in items:
                title = item.get("title", "")
                body = item.get("body", "") or ""
                full_text = f"{title} {body}"
                created_at = item.get("created_at", "")

                if created_at:
                    try:
                        created = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        if created < cutoff:
                            continue
                    except Exception:
                        pass

                if not is_webdev_related(full_text):
                    continue
                if is_african(full_text):
                    continue

                # Only include if it looks like a hiring/request post
                if not any(word in full_text.lower() for word in [
                    "looking for", "hiring", "need", "budget", "paid",
                    "freelance", "contract", "project"
                ]):
                    continue

                budget = extract_budget(full_text)
                author = item.get("user", {}).get("login", "Unknown")
                link = item.get("html_url", "https://github.com")
                display_body = body[:300].strip()
                if len(body) > 300:
                    display_body += "..."

                leads.append({
                    "title": title,
                    "source": "GitHub Issues",
                    "platform": "GitHub",
                    "author": f"@{author}",
                    "budget": budget,
                    "posted": created_at[:10] if created_at else "Recent",
                    "link": link,
                    "preview": display_body or title,
                    "contact": f"https://github.com/{author}"
                })

            time.sleep(3)

        except Exception as e:
            print(f"[GitHub] Error for '{query}': {e}")
            time.sleep(2)
            continue

    print(f"[GitHub] {len(leads)} leads found")
    return leads


# ─────────────────────────────────────────────
# SOURCE 4: Hacker News "Who is hiring" monthly thread
# Top quality — YC founders and serious startups only
# ─────────────────────────────────────────────
def fetch_hn_hiring_thread():
    leads = []
    try:
        # Search for the latest "Who is hiring" thread
        url = "https://hn.algolia.com/api/v1/search?query=Ask+HN+Who+is+hiring&tags=story&numericFilters=points>100"
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return leads

        data = res.json()
        hits = data.get("hits", [])

        if not hits:
            return leads

        # Get the most recent hiring thread
        latest = hits[0]
        thread_id = latest.get("objectID")
        if not thread_id:
            return leads

        # Fetch comments from the thread
        comments_url = f"https://hn.algolia.com/api/v1/items/{thread_id}"
        res2 = requests.get(comments_url, headers=HEADERS, timeout=15)
        if res2.status_code != 200:
            return leads

        thread_data = res2.json()
        children = thread_data.get("children", [])

        for comment in children[:100]:  # Check first 100 comments
            text = comment.get("text", "") or ""
            if not text:
                continue
            if not is_webdev_related(text):
                continue
            if is_african(text):
                continue

            author = comment.get("author", "Unknown")
            comment_id = comment.get("id", "")
            budget = extract_budget(text)
            display_text = text[:300].strip()
            if len(text) > 300:
                display_text += "..."

            leads.append({
                "title": f"HN Hiring: {text[:70]}...",
                "source": "HN Who's Hiring",
                "platform": "HackerNews",
                "author": author,
                "budget": budget,
                "posted": "This month",
                "link": f"https://news.ycombinator.com/item?id={comment_id}",
                "preview": display_text,
                "contact": f"https://news.ycombinator.com/user?id={author}"
            })

        print(f"[HN Hiring Thread] {len(leads)} leads found")

    except Exception as e:
        print(f"[HN Hiring Thread] Error: {e}")

    return leads


# ─────────────────────────────────────────────
# MAIN — combine all sources
# ─────────────────────────────────────────────
def fetch_all_leads():
    print("[INFO] Starting WebDev Lead Scraper...")
    all_leads = []

    all_leads += fetch_hackernews()
    all_leads += fetch_craigslist()
    all_leads += fetch_github()
    all_leads += fetch_hn_hiring_thread()

    # Deduplicate by title
    seen = set()
    unique = []
    for lead in all_leads:
        key = lead["title"].lower().strip()[:80]
        if key not in seen:
            seen.add(key)
            unique.append(lead)

    print(f"[TOTAL] {len(unique)} unique webdev leads found")
    return unique
