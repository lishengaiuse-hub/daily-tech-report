#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Tech Intelligence Report - Debug Version
"""

import os
import json
import hashlib
import feedparser
import requests
from datetime import datetime
import openai
import yagmail
import tempfile
import re
import time
import traceback

# ==================== CONFIGURATION ====================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Configure OpenAI for DeepSeek
openai.api_key = DEEPSEEK_API_KEY
openai.api_base = "https://api.deepseek.com/v1"

# Email Configuration
EMAIL_CONFIG = {
    "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", 587)),
    "sender_email": os.getenv("SENDER_EMAIL"),
    "sender_password": os.getenv("SENDER_PASSWORD"),
    "receiver_email": os.getenv("RECEIVER_EMAIL")
}

# Print config for debugging (hiding sensitive info)
print(f"\n📧 Email Configuration:")
print(f"   Sender: {EMAIL_CONFIG['sender_email']}")
print(f"   SMTP: {EMAIL_CONFIG['smtp_host']}:{EMAIL_CONFIG['smtp_port']}")
print(f"   Password set: {'Yes' if EMAIL_CONFIG['sender_password'] else 'No'}")
print(f"   Recipients raw: {EMAIL_CONFIG['receiver_email']}")

# RSS FEEDS
RSS_FEEDS = [
    {"url": "https://technews.tw/feed/", "category": "tech"},
    {"url": "https://www.ledinside.cn/rss.xml", "category": "semiconductor"},
    {"url": "https://www.moneydj.com/KMDJ/NewsCenter/RSS.aspx?c=MB020000", "category": "finance"},
    {"url": "https://www.bangkokpost.com/rss/data/business.xml", "category": "business"},
    {"url": "https://www.thestar.com.my/rss/business", "category": "business"},
]

# Keywords
KEYWORDS = [
    "factory", "plant", "manufacturing", "Thailand", "Vietnam", "Indonesia", 
    "Malaysia", "Singapore", "AR", "VR", "AI", "smart glasses", "wearable",
    "supplier", "exhibition", "expo", "AWE", "CES"
]

# ==================== FUNCTIONS ====================

def fetch_news_fast():
    """Fetch news quickly"""
    news_items = []
    feedparser.USER_AGENT = "Mozilla/5.0 (compatible; RSS Reader)"
    
    for feed in RSS_FEEDS:
        try:
            print(f"Fetching: {feed['url']}")
            parsed = feedparser.parse(feed['url'])
            
            for entry in parsed.entries[:10]:
                title = entry.get('title', '')
                summary = entry.get('summary', '') or entry.get('description', '')
                link = entry.get('link', '')
                
                # Keyword check
                text = (title + " " + summary).lower()
                if not any(kw.lower() in text for kw in KEYWORDS):
                    continue
                
                published = entry.get('published', datetime.now().strftime('%Y-%m-%d'))
                source = feed['url'].split('/')[2] if '//' in feed['url'] else feed['url']
                
                news_items.append({
                    "title": title,
                    "summary": summary[:500],
                    "link": link,
                    "source": source,
                    "published": published
                })
                
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
            continue
    
    print(f"✅ Total: {len(news_items)} articles")
    return news_items

def generate_report(news_items):
    """Generate report with DeepSeek"""
    if not news_items:
        return None
    
    # Prepare input
    news_text = "\n".join([f"- {item['title']} ({item['source']})" for item in news_items[:20]])
    
    prompt = """You are an industry analyst. Create a brief JSON report with:
{
  "executive_summary": "2-3 sentence summary",
  "factory_news": [{"company": "", "location": "", "details": "", "link": ""}],
  "tech_table": [{"name": "", "application": "", "suppliers": []}],
  "expos": [{"name": "", "date": "", "location": "", "link": ""}]
}"""
    
    try:
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"News:\n{news_text}"}
            ],
            temperature=0.2,
            max_tokens=1000,
            timeout=30
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ API error: {e}")
        return None

def create_html_report(report_data, news_items):
    """Create HTML report"""
    date = datetime.now().strftime('%B %d, %Y')
    
    # Factory news HTML
    factory_html = ""
    for item in report_data.get("factory_news", []):
        factory_html += f"""
        <div style="margin:10px 0; padding:10px; border-left:3px solid #0066cc;">
            <strong>{item.get('company', '')}</strong> - {item.get('location', '')}<br>
            {item.get('details', '')}<br>
            <small><a href="{item.get('link', '#')}">Source</a></small>
        </div>
        """
    
    # Tech table HTML
    tech_html = ""
    for item in report_data.get("tech_table", []):
        suppliers = ", ".join(item.get('suppliers', [])) if isinstance(item.get('suppliers'), list) else ""
        tech_html += f"<tr><td>{item.get('name', '')}</td><td>{item.get('application', '')}</td><td>{suppliers}</td></tr>"
    
    # Expos HTML
    expos_html = ""
    for item in report_data.get("expos", []):
        expos_html += f"""
        <div style="margin:10px 0;">
            <strong>{item.get('name', '')}</strong><br>
            📅 {item.get('date', '')} | 📍 {item.get('location', '')}<br>
            <a href="{item.get('link', '#')}">Website</a>
        </div>
        """
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Tech Report {date}</title>
    <style>
        body {{ font-family: Arial; margin: 30px; }}
        h1 {{ color: #333; border-bottom: 2px solid #0066cc; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f5f5f5; padding: 20px; border-radius: 8px; flex:1; }}
        .stat-number {{ font-size: 32px; font-weight: bold; color: #0066cc; }}
        table {{ width:100%; border-collapse: collapse; }}
        th {{ background: #0066cc; color: white; padding: 10px; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
    </style>
</head>
<body>
    <h1>📊 SEA Tech Report - {date}</h1>
    
    <div class="stats">
        <div class="stat-card"><div class="stat-number">{len(report_data.get('factory_news', []))}</div>Factory Projects</div>
        <div class="stat-card"><div class="stat-number">{len(report_data.get('tech_table', []))}</div>Technologies</div>
        <div class="stat-card"><div class="stat-number">{len(report_data.get('expos', []))}</div>Exhibitions</div>
    </div>
    
    <h2>📋 Summary</h2>
    <p>{report_data.get('executive_summary', '')}</p>
    
    <h2>🏭 Factory News</h2>
    {factory_html or '<p>No factory news</p>'}
    
    <h2>🔬 New Technologies</h2>
    <table>
        <tr><th>Technology</th><th>Application</th><th>Suppliers</th></tr>
        {tech_html or '<tr><td colspan="3">No tech news</td></tr>'}
    </table>
    
    <h2>🎪 Exhibitions</h2>
    {expos_html or '<p>No exhibitions</p>'}
    
    <div class="footer">Generated: {datetime.now()} | Articles: {len(news_items)}</div>
</body>
</html>"""

def send_email(subject, html_content):
    """Send email with detailed debugging"""
    print(f"\n📧 Sending email...")
    
    try:
        # Check config
        if not EMAIL_CONFIG["sender_email"]:
            print("❌ SENDER_EMAIL missing")
            return False
        if not EMAIL_CONFIG["sender_password"]:
            print("❌ SENDER_PASSWORD missing")
            return False
        if not EMAIL_CONFIG["receiver_email"]:
            print("❌ RECEIVER_EMAIL missing")
            return False
        
        # Parse recipients
        recipients_str = EMAIL_CONFIG["receiver_email"]
        for d in [';', '\n', '|', ',']:
            recipients_str = recipients_str.replace(d, ',')
        
        recipients = [e.strip() for e in recipients_str.split(',') if e.strip() and '@' in e]
        print(f"   Recipients: {recipients}")
        
        if not recipients:
            print("❌ No valid recipients")
            return False
        
        # Connect and send
        print(f"   Connecting to {EMAIL_CONFIG['smtp_host']}:{EMAIL_CONFIG['smtp_port']}...")
        yag = yagmail.SMTP(
            user=EMAIL_CONFIG["sender_email"],
            password=EMAIL_CONFIG["sender_password"],
            host=EMAIL_CONFIG["smtp_host"],
            port=EMAIL_CONFIG["smtp_port"]
        )
        print("   Connected!")
        
        print("   Sending...")
        yag.send(
            to=recipients,
            subject=subject,
            contents=html_content
        )
        
        print(f"✅ Email sent!")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        traceback.print_exc()
        return False

# ==================== MAIN ====================

def main():
    print(f"\n{'='*60}")
    print(f"🚀 Tech Report - {datetime.now()}")
    print(f"{'='*60}\n")
    
    start = time.time()
    
    # Fetch news
    news = fetch_news_fast()
    if not news:
        print("❌ No news found")
        return
    
    # Generate report
    print(f"\n🤖 Generating report...")
    report = generate_report(news)
    if not report:
        print("❌ Report generation failed")
        return
    
    # Create HTML
    print(f"\n🎨 Creating HTML...")
    html = create_html_report(report, news)
    
    # Save HTML locally (for debugging)
    with open("report.html", "w") as f:
        f.write(html)
    print("   Saved report.html")
    
    # Send email
    subject = f"SEA Tech Report {datetime.now().strftime('%Y-%m-%d')}"
    send_email(subject, html)
    
    print(f"\n✅ Complete in {time.time()-start:.1f} seconds")

if __name__ == "__main__":
    main()
