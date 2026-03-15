#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Tech Intelligence Report - Ultra Debug Version
Logs every step to find email issues
"""

import os
import sys
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
import smtplib
import socket

# ==================== LOGGING SETUP ====================
def log(msg, level="INFO"):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {level}: {msg}")
    sys.stdout.flush()  # Force print to appear immediately

log("=" * 60)
log("SCRIPT STARTED")
log(f"Python version: {sys.version}")
log(f"Working directory: {os.getcwd()}")
log("=" * 60)

# ==================== CONFIGURATION ====================
log("Loading environment variables...")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
log(f"DEEPSEEK_API_KEY set: {'Yes' if DEEPSEEK_API_KEY else 'No'}")

# Email Configuration
EMAIL_CONFIG = {
    "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", 587)),
    "sender_email": os.getenv("SENDER_EMAIL"),
    "sender_password": os.getenv("SENDER_PASSWORD"),
    "receiver_email": os.getenv("RECEIVER_EMAIL")
}

log(f"SMTP_HOST: {EMAIL_CONFIG['smtp_host']}")
log(f"SMTP_PORT: {EMAIL_CONFIG['smtp_port']}")
log(f"SENDER_EMAIL: {EMAIL_CONFIG['sender_email']}")
log(f"SENDER_PASSWORD set: {'Yes' if EMAIL_CONFIG['sender_password'] else 'No'}")
log(f"RECEIVER_EMAIL raw: {EMAIL_CONFIG['receiver_email']}")

# Configure OpenAI for DeepSeek
if DEEPSEEK_API_KEY:
    openai.api_key = DEEPSEEK_API_KEY
    openai.api_base = "https://api.deepseek.com/v1"
    log("OpenAI configured for DeepSeek")
else:
    log("❌ No DeepSeek API key found!", "ERROR")

# RSS FEEDS
RSS_FEEDS = [
    {"url": "https://technews.tw/feed/", "category": "tech"},
    {"url": "https://www.ledinside.cn/rss.xml", "category": "semiconductor"},
    {"url": "https://www.moneydj.com/KMDJ/NewsCenter/RSS.aspx?c=MB020000", "category": "finance"},
    {"url": "https://www.bangkokpost.com/rss/data/business.xml", "category": "business"},
    {"url": "https://www.thestar.com.my/rss/business", "category": "business"},
]
log(f"RSS feeds configured: {len(RSS_FEEDS)}")

# Keywords
KEYWORDS = [
    "factory", "plant", "manufacturing", "Thailand", "Vietnam", "Indonesia", 
    "Malaysia", "Singapore", "AR", "VR", "AI", "smart glasses", "wearable",
    "supplier", "exhibition", "expo", "AWE", "CES"
]
log(f"Keywords: {len(KEYWORDS)}")

# ==================== TEST FUNCTIONS ====================

def test_smtp_connection():
    """Test SMTP connection without sending email"""
    log("Testing SMTP connection...")
    try:
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"], timeout=10)
        server.starttls()
        server.ehlo()
        log(f"✅ SMTP connection successful to {EMAIL_CONFIG['smtp_host']}")
        server.quit()
        return True
    except Exception as e:
        log(f"❌ SMTP connection failed: {e}", "ERROR")
        traceback.print_exc()
        return False

def test_smtp_login():
    """Test SMTP login"""
    log("Testing SMTP login...")
    try:
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"], timeout=10)
        server.starttls()
        server.ehlo()
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        log(f"✅ SMTP login successful for {EMAIL_CONFIG['sender_email']}")
        server.quit()
        return True
    except Exception as e:
        log(f"❌ SMTP login failed: {e}", "ERROR")
        traceback.print_exc()
        return False

# ==================== FUNCTIONS ====================

def fetch_news_fast():
    """Fetch news quickly"""
    log("Starting news fetch...")
    news_items = []
    feedparser.USER_AGENT = "Mozilla/5.0 (compatible; RSS Reader)"
    
    for feed in RSS_FEEDS:
        try:
            log(f"Fetching: {feed['url']}")
            parsed = feedparser.parse(feed['url'])
            log(f"  Got {len(parsed.entries)} entries")
            
            for i, entry in enumerate(parsed.entries[:10]):
                title = entry.get('title', 'No title')
                summary = entry.get('summary', '') or entry.get('description', '')
                link = entry.get('link', '')
                
                # Keyword check
                text = (title + " " + summary).lower()
                if not any(kw.lower() in text for kw in KEYWORDS):
                    continue
                
                log(f"  ✅ Match found: {title[:50]}...")
                
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
            log(f"  ❌ Error fetching {feed['url']}: {e}", "ERROR")
            continue
    
    log(f"✅ Total articles found: {len(news_items)}")
    return news_items

def generate_report(news_items):
    """Generate report with DeepSeek"""
    log("Starting report generation...")
    
    if not news_items:
        log("❌ No news items to generate report", "ERROR")
        return None
    
    # Prepare input
    news_text = "\n".join([f"- {item['title']} ({item['source']})" for item in news_items[:20]])
    log(f"Prepared {len(news_items[:20])} items for API")
    
    prompt = """You are an industry analyst. Create a brief JSON report with:
{
  "executive_summary": "2-3 sentence summary",
  "factory_news": [{"company": "", "location": "", "details": "", "link": ""}],
  "tech_table": [{"name": "", "application": "", "suppliers": []}],
  "expos": [{"name": "", "date": "", "location": "", "link": ""}]
}"""
    
    try:
        log("Calling DeepSeek API...")
        start_time = time.time()
        
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
        
        api_time = time.time() - start_time
        log(f"✅ API response in {api_time:.1f} seconds")
        
        result = json.loads(response.choices[0].message.content)
        log(f"Report generated with: factory={len(result.get('factory_news', []))}, tech={len(result.get('tech_table', []))}, expos={len(result.get('expos', []))}")
        
        return result
    except Exception as e:
        log(f"❌ API error: {e}", "ERROR")
        traceback.print_exc()
        return None

def create_html_report(report_data, news_items):
    """Create HTML report"""
    log("Creating HTML report...")
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
    
    html = f"""<!DOCTYPE html>
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
    
    # Save HTML to file
    try:
        with open("report.html", "w", encoding='utf-8') as f:
            f.write(html)
        log("✅ Saved report.html")
    except Exception as e:
        log(f"❌ Failed to save HTML: {e}", "ERROR")
    
    return html

def send_email(subject, html_content):
    """Send email with ultra debugging"""
    log("\n" + "="*40)
    log("EMAIL SENDING ATTEMPT")
    log("="*40)
    
    try:
        # Check config
        log("Checking email configuration...")
        if not EMAIL_CONFIG["sender_email"]:
            log("❌ SENDER_EMAIL is missing", "ERROR")
            return False
        if not EMAIL_CONFIG["sender_password"]:
            log("❌ SENDER_PASSWORD is missing", "ERROR")
            return False
        if not EMAIL_CONFIG["receiver_email"]:
            log("❌ RECEIVER_EMAIL is missing", "ERROR")
            return False
        
        log(f"Sender: {EMAIL_CONFIG['sender_email']}")
        log(f"Password length: {len(EMAIL_CONFIG['sender_password'])} characters")
        
        # Parse recipients
        recipients_str = EMAIL_CONFIG["receiver_email"]
        log(f"Raw recipients string: '{recipients_str}'")
        
        # Replace delimiters
        for d in [';', '\n', '|']:
            recipients_str = recipients_str.replace(d, ',')
        log(f"After delimiter replacement: '{recipients_str}'")
        
        # Split and clean
        raw_emails = [e.strip() for e in recipients_str.split(',') if e.strip()]
        log(f"Raw split emails: {raw_emails}")
        
        # Validate emails
        recipients = [e for e in raw_emails if '@' in e and '.' in e.split('@')[-1]]
        log(f"Valid recipients after validation: {recipients}")
        
        if not recipients:
            log("❌ No valid email recipients after validation", "ERROR")
            return False
        
        # Try direct SMTP connection first
        log("Testing direct SMTP connection...")
        try:
            server = smtplib.SMTP(EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"], timeout=10)
            server.starttls()
            server.ehlo()
            log("✅ Basic SMTP connection successful")
            server.quit()
        except Exception as e:
            log(f"❌ Basic SMTP connection failed: {e}", "ERROR")
            # Continue anyway, yagmail might work
        
        # Try yagmail
        log("Initializing yagmail...")
        try:
            yag = yagmail.SMTP(
                user=EMAIL_CONFIG["sender_email"],
                password=EMAIL_CONFIG["sender_password"],
                host=EMAIL_CONFIG["smtp_host"],
                port=EMAIL_CONFIG["smtp_port"],
                smtp_starttls=True,
                smtp_ssl=False
            )
            log("✅ yagmail SMTP object created")
        except Exception as e:
            log(f"❌ yagmail initialization failed: {e}", "ERROR")
            traceback.print_exc()
            return False
        
        # Send email
        log(f"Sending email to {len(recipients)} recipients...")
        log(f"Subject: {subject}")
        log(f"Content length: {len(html_content)} chars")
        
        try:
            yag.send(
                to=recipients,
                subject=subject,
                contents=html_content
            )
            log("✅ yagmail.send() completed successfully")
        except Exception as e:
            log(f"❌ yagmail.send() failed: {e}", "ERROR")
            traceback.print_exc()
            return False
        
        log("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        log(f"❌ Unexpected error in send_email: {e}", "ERROR")
        traceback.print_exc()
        return False

# ==================== MAIN ====================

def main():
    log("\n" + "="*60)
    log("MAIN FUNCTION STARTED")
    log("="*60)
    
    start = time.time()
    
    # Test SMTP first
    log("\n--- SMTP PRE-TESTS ---")
    test_smtp_connection()
    test_smtp_login()
    
    # Fetch news
    log("\n--- FETCHING NEWS ---")
    news = fetch_news_fast()
    if not news:
        log("❌ No news found, exiting", "ERROR")
        return
    
    # Generate report
    log("\n--- GENERATING REPORT ---")
    report = generate_report(news)
    if not report:
        log("❌ Report generation failed, exiting", "ERROR")
        return
    
    # Create HTML
    log("\n--- CREATING HTML ---")
    html = create_html_report(report, news)
    
    # Send email
    log("\n--- SENDING EMAIL ---")
    subject = f"SEA Tech Report {datetime.now().strftime('%Y-%m-%d')}"
    email_result = send_email(subject, html)
    
    if email_result:
        log("✅ Email function returned True")
    else:
        log("❌ Email function returned False", "ERROR")
    
    # Final status
    elapsed = time.time() - start
    log("\n" + "="*60)
    log(f"SCRIPT COMPLETED in {elapsed:.1f} seconds")
    log(f"Final email status: {'SUCCESS' if email_result else 'FAILED'}")
    log("="*60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ Unhandled exception in main: {e}", "ERROR")
        traceback.print_exc()
    
    log("\nSCRIPT FINISHED")
    sys.stdout.flush()
