import os

RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "jobhauntgithub@gmail.com")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# Target countries
TARGET_COUNTRIES = ["usa", "us", "united states", "uk", "united kingdom",
                    "england", "canada", "australia", "new zealand", "nz",
                    "british columbia", "ontario", "london", "toronto",
                    "sydney", "melbourne", "auckland", "glasgow", "manchester"]

# African countries to exclude
AFRICAN_COUNTRIES = ["nigeria", "ghana", "kenya", "south africa", "ethiopia",
                     "egypt", "tanzania", "uganda", "senegal", "cameroon",
                     "ivory coast", "mozambique", "zambia", "zimbabwe",
                     "rwanda", "niger", "mali", "angola", "africa"]

# Web development keywords to match
WEBDEV_KEYWORDS = [
    "web developer", "web development", "website developer", "website development",
    "wordpress developer", "wordpress website", "wordpress site",
    "landing page", "landing page developer", "build a website",
    "need a website", "looking for a website", "website builder",
    "ecommerce website", "e-commerce website", "shopify developer",
    "shopify store", "woocommerce", "squarespace", "webflow",
    "build my website", "create a website", "redesign my website",
    "website redesign", "web design", "frontend developer",
    "saas developer", "saas website", "web app", "web application",
    "portfolio website", "business website", "company website",
    "hire web developer", "hiring web developer", "need web developer",
    "looking for web developer", "web dev", "full stack developer",
    "fullstack developer", "react developer", "next.js developer",
]

# Subreddits to scrape
SUBREDDITS = [
    "forhire",
    "hiring",
    "startups",
    "smallbusiness",
    "entrepreneur",
    "webdev",
    "freelance",
    "web_design",
]

# Indie Hackers search terms
INDIEHACKERS_KEYWORDS = [
    "web developer", "website", "landing page", "wordpress"
]
