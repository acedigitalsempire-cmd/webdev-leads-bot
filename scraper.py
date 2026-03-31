import requests
import time
from datetime import datetime, timedelta, timezone
from config import SUBREDDITS, WEBDEV_KEYWORDS, TARGET_COUNTRIES, AFRICAN_COUNTRIES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WebDevLeadBot/1.0; +https://acedigitalsempire.com)"
}


def is_webdev_related(text):
    text_lower = text.lower()
    return any(kw in text_lower for kw in WEBDEV_KEYWORDS)


def is_target_country(text):
    text_lower = text.lower()
    # Exclude African countries first
    if any(country in text_lower for country in AFRICAN_COUNTRIES):
        return False
    # Check if target country mentioned OR no location specified (assume global)
    has_target = any(country in text_lower for country in TARGET_COUNTRIES)
    return has_target


def is_hiring_post(title):
    title_lower = title.lower()
    hiring_signals = [
        "hiring", "looking for", "need a", "need someone", "seeking",
        "wanted", "want to hire", "want someone", "budget", "paid",
        "paying", "project", "freelancer wanted", "help with",
        "building", "create", "develop", "design"
    ]
    return any(signal in title_lower for signal in hiring_signals)


def extract_budget(text):
    import re
    # Find budget mentions like $500, $1000, $2,000
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


def fetch_reddit_leads():
    leads = []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=48)

    for subreddit in SUBREDDITS:
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=50"
        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
            if res.status_code != 200:
                print(f"[Reddit] r/{subreddit} returned {res.status_code}")
                time.sleep(2)
                continue

            data = res.json()
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                p = post.get("data", {})
                title = p.get("title", "")
                body = p.get("selftext", "")
                full_text = f"{title} {body}"
                created = datetime.fromtimestamp(p.get("created_utc", 0), tz=timezone.utc)

                # Only last 48 hours
                if created < cutoff:
                    continue

                # Must be web dev related
                if not is_webdev_related(full_text):
                    continue

                # Must be hiring/looking
                if not is_hiring_post(title):
                    continue

                # Must be target country OR no location specified
                # For r/forhire and r/hiring, location is usually in title
                # For others, we include if no African country mentioned
                if subreddit in ["forhire", "hiring"]:
                    if not is_target_country(full_text):
                        continue
                else:
                    # For startup/business subs, exclude only African countries
                    if any(c in full_text.lower() for c in AFRICAN_COUNTRIES):
                        continue

                budget = extract_budget(full_text)
                post_url = f"https://reddit.com{p.get('permalink', '')}"
                author = p.get("author", "Unknown")
                posted_time = created.strftime("%b %d, %Y %I:%M %p UTC")

                # Trim body for display
                display_body = body[:300].strip()
                if len(body) > 300:
                    display_body += "..."

                leads.append({
                    "title": title,
                    "source": f"r/{subreddit}",
                    "platform": "Reddit",
                    "author": f"u/{author}",
                    "budget": budget,
                    "posted": posted_time,
                    "link": post_url,
                    "preview": display_body or title,
                    "contact": f"https://reddit.com/u/{author}"
                })

            print(f"[Reddit] r/{subreddit}: scraped successfully")
            time.sleep(2)  # Rate limit between subreddits

        except Exception as e:
            print(f"[Reddit] r/{subreddit} error: {e}")
            time.sleep(3)

    return leads


def fetch_indiehackers_leads():
    """Scrape Indie Hackers for web dev requests"""
    leads = []
    url = "https://www.indiehackers.com/posts.json?order=latest&limit=50"

    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200:
            print(f"[IndieHackers] Status: {res.status_code}")
            return leads

        posts = res.json()
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=48)

        for post in posts:
            title = post.get("title", "")
            body = post.get("body", "")
            full_text = f"{title} {body}"

            # Check recency
            created_at = post.get("createdAt", 0)
            if created_at:
                created = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)
                if created < cutoff:
                    continue

            if not is_webdev_related(full_text):
                continue

            if any(c in full_text.lower() for c in AFRICAN_COUNTRIES):
                continue

            budget = extract_budget(full_text)
            author = post.get("username", "Unknown")
            slug = post.get("slug", "")
            post_url = f"https://www.indiehackers.com/post/{slug}" if slug else "https://www.indiehackers.com"

            display_body = body[:300].strip()
            if len(body) > 300:
                display_body += "..."

            leads.append({
                "title": title,
                "source": "Indie Hackers",
                "platform": "IndieHackers",
                "author": author,
                "budget": budget,
                "posted": "Recent",
                "link": post_url,
                "preview": display_body or title,
                "contact": f"https://www.indiehackers.com/{author}"
            })

        print(f"[IndieHackers] {len(leads)} leads found")

    except Exception as e:
        print(f"[IndieHackers] Error: {e}")

    return leads


def fetch_all_leads():
    print("[INFO] Starting WebDev Lead Scraper...")
    all_leads = []
    all_leads += fetch_reddit_leads()
    all_leads += fetch_indiehackers_leads()

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
