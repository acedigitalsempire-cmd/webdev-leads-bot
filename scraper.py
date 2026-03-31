import requests
import time
from datetime import datetime, timedelta, timezone
from config import WEBDEV_KEYWORDS, AFRICAN_COUNTRIES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def is_webdev_related(text):
    text_lower = text.lower()
    return any(kw in text_lower for kw in WEBDEV_KEYWORDS)

def is_african(text):
    text_lower = text.lower()
    return any(c in text_lower for c in AFRICAN_COUNTRIES)

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

# ─────────────────────────────────────────────
# SOURCE 1: Hacker News "Who wants to be hired"
# and "Freelancer? Seeking Freelancer?" threads
# Free API, no auth needed, very low competition
# ─────────────────────────────────────────────
def fetch_hackernews():
    leads = []
    try:
        # Search HN for web dev related posts
        search_terms = [
            "web developer", "website developer", "wordpress",
            "landing page", "web design", "frontend developer"
        ]

        for term in search_terms:
            url = f"https://hn.algolia.com/api/v1/search_by_date?query={term}&tags=comment&numericFilters=created_at_i>{int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp())}"
            try:
                res = requests.get(url, headers=HEADERS, timeout=15)
                if res.status_code != 200:
                    continue
                data = res.json()
                hits = data.get("hits", [])

                for hit in hits:
                    text = hit.get("comment_text", "") or ""
                    story_title = hit.get("story_title", "") or ""
                    full_text = f"{story_title} {text}"

                    if not is_webdev_related(full_text):
                        continue
                    if is_african(full_text):
                        continue

                    # Focus on hiring/seeking posts
                    if not any(word in full_text.lower() for word in [
                        "looking for", "hiring", "need", "seeking", "want",
                        "budget", "project", "build", "create", "design"
                    ]):
                        continue

                    budget = extract_budget(full_text)
                    object_id = hit.get("objectID", "")
                    story_id = hit.get("story_id", "")
                    link = f"https://news.ycombinator.com/item?id={story_id}" if story_id else "https://news.ycombinator.com"
                    author = hit.get("author", "Unknown")
                    created = hit.get("created_at", "")

                    display_text = text[:300].strip()
                    if len(text) > 300:
                        display_text += "..."

                    leads.append({
                        "title": story_title or f"HN: {text[:80]}...",
                        "source": "Hacker News",
                        "platform": "HackerNews",
                        "author": author,
                        "budget": budget,
                        "posted": created[:10] if created else "Recent",
                        "link": link,
                        "preview": display_text,
                        "contact": f"https://news.ycombinator.com/user?id={author}"
                    })

                time.sleep(1)

            except Exception as e:
                print(f"[HN] Error for term '{term}': {e}")
                continue

        print(f"[HackerNews] {len(leads)} leads found")

    except Exception as e:
        print(f"[HackerNews] Error: {e}")

    return leads


# ─────────────────────────────────────────────
# SOURCE 2: Craigslist — USA/Canada cities
# Locals posting "need website" with real budgets
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
