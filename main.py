from scraper import fetch_all_leads
from emailer import send_email
from datetime import datetime

PLATFORM_COLORS = {
    "Craigslist": "#6B4226",
    "IndieHackers": "#0e2439",
    "ProductHunt": "#DA552F",
    "DEVto": "#000000",
}

def generate_html(leads, date_str):
    if not leads:
        return f"""<html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
<div style="max-width:600px;margin:auto;background:white;border-radius:10px;padding:30px;text-align:center;">
<h2 style="color:#e74c3c;">No WebDev Leads Found Today</h2>
<p style="color:#555;">No relevant web development requests found. Check back tomorrow!</p>
<p style="color:#888;font-size:12px;">Date: {date_str}</p>
</div></body></html>"""

    platform_counts = {}
    for lead in leads:
        p = lead.get("platform", "Other")
        platform_counts[p] = platform_counts.get(p, 0) + 1

    platform_summary = " &nbsp;|&nbsp; ".join(
        [f'<span style="color:{PLATFORM_COLORS.get(p,"#555")}">⬤</span> {p}: <strong>{c}</strong>'
         for p, c in platform_counts.items()])

    cards = ""
    for lead in leads:
        platform = lead.get("platform", "Other")
        platform_color = PLATFORM_COLORS.get(platform, "#555")
        source = lead.get("source", "Unknown")
        budget = lead.get("budget", "Not specified")
        budget_color = "#27ae60" if budget != "Not specified" else "#888"
        cards += f"""
<div style="background:white;border-radius:10px;padding:20px;margin-bottom:16px;
box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid {platform_color};">
<div>
<span style="background:{platform_color};color:white;padding:3px 10px;border-radius:10px;
font-size:11px;font-weight:bold;">{source}</span>
<span style="background:{budget_color};color:white;padding:3px 10px;border-radius:10px;
font-size:11px;margin-left:6px;">💰 {budget}</span>
<span style="color:#888;font-size:11px;margin-left:8px;">{lead.get('posted','')}</span>
</div>
<h3 style="color:#2c3e50;margin:12px 0 8px;font-size:15px;line-height:1.4;">{lead['title']}</h3>
<p style="color:#666;font-size:13px;margin:0 0 12px;line-height:1.5;">{lead.get('preview','')}</p>
<div>
<a href="{lead['link']}" style="background:#2c3e50;color:white;padding:8px 16px;border-radius:6px;
text-decoration:none;font-size:13px;font-weight:bold;margin-right:8px;">📋 View Full Post</a>
<a href="{lead['contact']}" style="background:#27ae60;color:white;padding:8px 16px;border-radius:6px;
text-decoration:none;font-size:13px;font-weight:bold;">💬 Contact Client</a>
</div>
<p style="color:#aaa;font-size:11px;margin:10px 0 0;">Posted by: {lead.get('author','Unknown')}</p>
</div>"""

    return f"""<html>
<body style="font-family:Arial,sans-serif;background:#f0f2f5;padding:20px;margin:0;">
<div style="max-width:700px;margin:auto;">
<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;
padding:30px;text-align:center;margin-bottom:20px;">
<h1 style="color:#f1c40f;margin:0;font-size:24px;">🌍 WebDev Lead Report</h1>
<p style="color:#aaa;margin:8px 0 0;">{date_str}</p>
<p style="color:white;font-size:18px;margin:10px 0 4px;">
<strong>{len(leads)}</strong> Web Development Requests Found</p>
<p style="color:#ccc;font-size:13px;margin:4px 0 0;">{platform_summary}</p>
<p style="color:#f1c40f;font-size:12px;margin:10px 0 0;">
🎯 Targeting: USA • UK • Canada • Australia • New Zealand</p>
</div>
<div style="background:#fff3cd;border-radius:10px;padding:15px 20px;
margin-bottom:20px;border-left:4px solid #f1c40f;">
<p style="color:#856404;font-size:13px;margin:0;">
<strong>💡 Pro Tip:</strong> Reply within <strong>2 hours</strong> of a post going live
for the highest chance of landing the client. Leads with 💰 budget listed are highest priority!
</p>
</div>
{cards}
<div style="text-align:center;padding:20px;">
<p style="color:#aaa;font-size:12px;margin:0;">
Sourced from Craigslist 🟤 &nbsp; Indie Hackers 🔵 &nbsp; Product Hunt 🔴 &nbsp; DEV.to ⚫<br>
Generated automatically by your WebDev Lead Bot 🤖<br>
Runs daily at 9AM Nigeria Time — Ace Digitals Global
</p>
</div>
</div>
</body>
</html>"""

def main():
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    print(f"[INFO] Starting WebDev Lead Bot — {date_str}")
    leads = fetch_all_leads()
    html = generate_html(leads, date_str)
    send_email(html, lead_count=len(leads), date_str=date_str)
    print("[INFO] Done!")

if __name__ == "__main__":
    main()
