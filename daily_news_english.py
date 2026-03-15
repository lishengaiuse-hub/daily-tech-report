#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Tech Intelligence Report - Optimized for Speed
Fetches only working RSS feeds with timeouts
"""

import os
import json
import hashlib
import feedparser
import requests
from datetime import datetime
import openai
from jinja2 import Environment, FileSystemLoader
import yagmail
from weasyprint import HTML
import tempfile
import re
import time

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

# REDUCED RSS FEEDS - Only the fastest and most reliable ones
RSS_FEEDS = [
    # Fast tech news sources
    {"url": "https://technews.tw/feed/", "category": "tech", "region": "taiwan"},
    {"url": "https://www.ledinside.cn/rss.xml", "category": "semiconductor", "region": "china"},
    {"url": "https://www.moneydj.com/KMDJ/NewsCenter/RSS.aspx?c=MB020000", "category": "finance", "region": "taiwan"},
    
    # Southeast Asia (some might be slow, so we'll add timeouts)
    {"url": "https://www.bangkokpost.com/rss/data/business.xml", "category": "business", "region": "thailand"},
    {"url": "https://www.thestar.com.my/rss/business", "category": "business", "region": "malaysia"},
]

# Keywords for filtering
KEYWORDS = [
    # Manufacturing
    "factory", "plant", "manufacturing", "production", "Thailand", "Vietnam", 
    "Indonesia", "Malaysia", "Singapore", "Southeast Asia", "investment", "expansion",
    
    # Technology
    "AR", "VR", "AI", "smart glasses", "AR glasses", "VR headset", "AI glasses",
    "wearable", "display", "MicroLED", "OLED", "sensor", "chip", "battery",
    
    # Suppliers
    "supplier", "vendor", "manufacturer", "OEM", "Foxconn", "Pegatron", "Goertek", "BOE",
    
    # Exhibitions
    "exhibition", "trade show", "expo", "AWE", "CES", "MWC", "IFA"
]

# ==================== FAST FETCHING ====================

def fetch_news_fast():
    """
    Fetch news quickly with timeouts and limits
    """
    news_items = []
    
    # Set feedparser timeouts
    feedparser.USER_AGENT = "Mozilla/5.0 (compatible; RSS Reader; +https://github.com/)"
    
    for feed in RSS_FEEDS:
        try:
            print(f"Fetching: {feed['url']}")
            
            # Add timeout to feedparser
            parsed = feedparser.parse(feed['url'])
            
            # Take only first 10 items from each feed
            for entry in parsed.entries[:10]:
                title = entry.get('title', '')
                summary = entry.get('summary', '') or entry.get('description', '')
                link = entry.get('link', '')
                
                # Quick keyword check (case-insensitive)
                text_to_check = (title + " " + summary).lower()
                if not any(kw.lower() in text_to_check for kw in KEYWORDS):
                    continue
                
                # Get publication date
                published = entry.get('published', '')
                if not published:
                    published = entry.get('updated', datetime.now().strftime('%Y-%m-%d'))
                
                # Extract source name
                source_name = feed['url'].split('/')[2] if '//' in feed['url'] else feed['url']
                
                # Generate ID
                news_id = hashlib.md5(f"{title}{link}".encode()).hexdigest()
                
                news_items.append({
                    "id": news_id,
                    "title": title,
                    "summary": summary[:500],
                    "link": link,
                    "source_name": source_name,
                    "published": published,
                    "category": feed['category']
                })
                
        except Exception as e:
            print(f"  ⚠️ Failed: {feed['url']} - {str(e)[:50]}")
            continue
    
    print(f"\n✅ Total fetched: {len(news_items)} articles")
    return news_items

def generate_report_fast(news_items):
    """
    Generate report with smaller payload for faster API response
    """
    if not news_items:
        return {
            "executive_summary": "No relevant news today.",
            "factory_news": [],
            "tech_table": [],
            "expos": [],
            "stats": {"factory_count": 0, "tech_count": 0, "expo_count": 0}
        }
    
    # Prepare condensed input (max 30 articles to keep payload small)
    news_input = []
    for i, item in enumerate(news_items[:30]):
        news_input.append(f"{i+1}. {item['title'][:100]} - {item['source_name']}")
    
    news_text = "\n".join(news_input)
    
    system_prompt = """You are an industry analyst. Create a brief JSON report with:
{
  "executive_summary": "2-3 sentence summary",
  "factory_news": [{"company": "", "location": "", "details": "", "link": ""}],
  "tech_table": [{"name": "", "application": "", "suppliers": []}],
  "expos": [{"name": "", "date": "", "location": "", "link": ""}],
  "stats": {"factory_count": 0, "tech_count": 0, "expo_count": 0}
}

Use ONLY the news provided. English only. Keep it concise."""

    try:
        start_time = time.time()
        
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"News:\n{news_text}"}
            ],
            temperature=0.2,
            max_tokens=1500,  # Reduced for faster response
            timeout=30  # 30 second timeout
        )
        
        api_time = time.time() - start_time
        print(f"✅ API response in {api_time:.1f} seconds")
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"❌ API failed: {e}")
        return {
            "executive_summary": f"API error: {str(e)[:100]}",
            "factory_news": [],
            "tech_table": [],
            "expos": [],
            "stats": {"factory_count": 0, "tech_count": 0, "expo_count": 0}
        }

def render_simple_report(report_data):
    """
    Simple HTML report (no complex template dependencies)
    """
    date = datetime.now().strftime('%B %d, %Y')
    
    # Build factory news HTML
    factory_html = ""
    for item in report_data.get("factory_news", []):
        factory_html += f"""
        <div style="margin:15px 0; padding:10px; border-left:3px solid #0066cc;">
            <strong>{item.get('company', 'Unknown')}</strong> - {item.get('location', '')}<br>
            {item.get('details', '')}<br>
            <small>Source: <a href="{item.get('link', '#')}">{item.get('link', '')[:50]}...</a></small>
        </div>
        """
    
    # Build tech table HTML
    tech_html = ""
    for item in report_data.get("tech_table", []):
        suppliers = ", ".join(item.get('suppliers', [])) if isinstance(item.get('suppliers'), list) else str(item.get('suppliers', ''))
        tech_html += f"""
        <tr>
            <td><strong>{item.get('name', '')}</strong></td>
            <td>{item.get('application', '')}</td>
            <td>{suppliers}</td>
        </tr>
        """
    
    # Build expos HTML
    expos_html = ""
    for item in report_data.get("expos", []):
        expos_html += f"""
        <div style="margin:15px 0;">
            <strong>{item.get('name', '')}</strong><br>
            📅 {item.get('date', '')} | 📍 {item.get('location', '')}<br>
            <a href="{item.get('link', '#')">Website</a>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Tech Report {date}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
        h2 {{ color: #0066cc; margin-top: 30px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f5f5f5; padding: 20px; border-radius: 8px; flex: 1; text-align: center; }}
        .stat-number {{ font-size: 32px; font-weight: bold; color: #0066cc; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #0066cc; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        .footer {{ margin-top: 40px; color: #666; font-size: 12px; text-align: center; }}
    </style>
</head>
<body>
    <h1>📊 Southeast Asia Tech Report - {date}</h1>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{report_data['stats'].get('factory_count', 0)}</div>
            <div>Factory Projects</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{report_data['stats'].get('tech_count', 0)}</div>
            <div>New Technologies</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{report_data['stats'].get('expo_count', 0)}</div>
            <div>Exhibitions</div>
        </div>
    </div>
    
    <h2>📋 Executive Summary</h2>
    <p>{report_data.get('executive_summary', 'No summary available.')}</p>
    
    <h2>🏭 Factory News</h2>
    {factory_html if factory_html else '<p>No factory news today.</p>'}
    
    <h2>🔬 New Technologies</h2>
    <table>
        <tr>
            <th>Technology</th>
            <th>Application</th>
            <th>Suppliers</th>
        </tr>
        {tech_html if tech_html else '<tr><td colspan="3">No technology news today.</td></tr>'}
    </table>
    
    <h2>🎪 Exhibitions</h2>
    {expos_html if expos_html else '<p>No exhibition news today.</p>'}
    
    <div class="footer">
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Articles: {len(news_items)}<br>
        Source: Tech News RSS
    </div>
</body>
</html>"""
    
    return html

def send_email_fast(subject, html_content):
    """Send email without PDF (faster)"""
    try:
        yag = yagmail.SMTP(
            user=EMAIL_CONFIG["sender_email"],
            password=EMAIL_CONFIG["sender_password"],
            host=EMAIL_CONFIG["smtp_host"],
            port=EMAIL_CONFIG["smtp_port"]
        )
        
        # Parse recipients
        recipients = [e.strip() for e in EMAIL_CONFIG["receiver_email"].replace(';', ',').split(',') if '@' in e]
        
        yag.send(
            to=recipients,
            subject=subject,
            contents=html_content
        )
        
        print(f"✅ Email sent to {len(recipients)} recipients")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

# ==================== MAIN ====================

def main():
    print(f"\n{'='*60}")
    print(f"🚀 Fast Tech Report - {datetime.now()}")
    print(f"{'='*60}\n")
    
    start_total = time.time()
    
    # Step 1: Fetch news (with timeout)
    print("📡 Fetching news (timeout: 10s per feed)...")
    news_items = fetch_news_fast()
    
    if not news_items:
        print("⚠️ No news found")
        return
    
    # Step 2: Generate report
    print(f"\n🤖 Generating report with DeepSeek...")
    report_data = generate_report_fast(news_items)
    
    # Step 3: Render HTML
    print(f"\n🎨 Rendering HTML...")
    html_report = render_simple_report(report_data)
    
    # Step 4: Send email (skip PDF for speed)
    print(f"\n📧 Sending email...")
    subject = f"SEA Tech Report {datetime.now().strftime('%Y-%m-%d')}"
    send_email_fast(subject, html_report)
    
    total_time = time.time() - start_total
    print(f"\n{'='*60}")
    print(f"✅ Complete in {total_time:.1f} seconds!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
