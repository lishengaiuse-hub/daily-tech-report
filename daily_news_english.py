#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Tech Intelligence Report - Complete Fixed Version
With proper error handling and JSON parsing
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
    sys.stdout.flush()

log("=" * 60)
log("DAILY TECH REPORT - FIXED VERSION")
log(f"Python version: {sys.version}")
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
    "factory", "plant", "manufacturing", "production", "Thailand", "Vietnam", 
    "Indonesia", "Malaysia", "Singapore", "Southeast Asia", "investment", "expansion",
    "AR", "VR", "AI", "smart glasses", "AR glasses", "VR headset", "AI glasses",
    "wearable", "display", "MicroLED", "OLED", "sensor", "chip", "battery",
    "supplier", "vendor", "manufacturer", "OEM", "Foxconn", "Pegatron", "Goertek", "BOE",
    "exhibition", "trade show", "expo", "AWE", "CES", "MWC", "IFA"
]
log(f"Keywords loaded: {len(KEYWORDS)}")

# ==================== HELPER FUNCTIONS ====================

def parse_recipients(recipients_string):
    """
    Parse email recipients from string, handling various formats
    Removes asterisks, line breaks, and splits by common delimiters
    """
    if not recipients_string:
        return []
    
    log(f"Parsing recipients from: '{recipients_string}'")
    
    # Remove asterisks (common in GitHub Secrets display)
    cleaned = recipients_string.replace('*', '')
    
    # Replace various delimiters with commas
    for delimiter in ['\n', '\r', ';', '|', ' ']:
        cleaned = cleaned.replace(delimiter, ',')
    
    log(f"After delimiter replacement: '{cleaned}'")
    
    # Split by comma and clean each part
    raw_emails = [email.strip() for email in cleaned.split(',') if email.strip()]
    log(f"Raw split emails: {raw_emails}")
    
    # Validate email format (basic check)
    valid_emails = []
    for email in raw_emails:
        # Remove any remaining invalid characters
        email = re.sub(r'[^\w\.@\-_]', '', email)
        if '@' in email and '.' in email.split('@')[-1]:
            valid_emails.append(email)
        else:
            log(f"Skipping invalid email: {email}", "WARNING")
    
    log(f"Valid recipients: {valid_emails}")
    return valid_emails

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
        return False

# ==================== CORE FUNCTIONS ====================

def fetch_news():
    """Fetch news from RSS feeds"""
    log("Starting news fetch...")
    news_items = []
    feedparser.USER_AGENT = "Mozilla/5.0 (compatible; RSS Reader; +https://github.com/)"
    
    for feed in RSS_FEEDS:
        try:
            log(f"Fetching: {feed['url']}")
            parsed = feedparser.parse(feed['url'])
            log(f"  Got {len(parsed.entries)} entries")
            
            for entry in parsed.entries[:10]:  # Limit to 10 per feed
                title = entry.get('title', 'No title')
                summary = entry.get('summary', '') or entry.get('description', '')
                link = entry.get('link', '')
                
                # Quick keyword check
                text_to_check = (title + " " + summary).lower()
                if not any(kw.lower() in text_to_check for kw in KEYWORDS):
                    continue
                
                log(f"  ✅ Match: {title[:50]}...")
                
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
            log(f"  ⚠️ Error fetching {feed['url']}: {e}", "WARNING")
            continue
    
    log(f"✅ Total articles fetched: {len(news_items)}")
    return news_items

def generate_report(news_items):
    """Generate report using DeepSeek API with better error handling"""
    log("Starting report generation...")
    
    if not news_items:
        log("❌ No news items to generate report", "ERROR")
        return None
    
    # Prepare input (limit to 20 items for API)
    news_summary = []
    for i, item in enumerate(news_items[:20]):
        news_summary.append(f"{i+1}. {item['title']} - {item['source']}")
    
    news_text = "\n".join(news_summary)
    log(f"Prepared {len(news_summary)} items for API")
    
    # Simpler prompt that's more likely to return valid JSON
    system_prompt = """You are an industry analyst. Return ONLY a valid JSON object with no other text.
The JSON must have this exact structure:
{
  "executive_summary": "2-3 sentence summary",
  "factory_news": [],
  "tech_table": [],
  "expos": []
}

For factory_news, each item should have: company, location, details, link
For tech_table, each item should have: name, application, suppliers (array)
For expos, each item should have: name, date, location, link

If no news for a category, return empty array."""
    
    try:
        log("Calling DeepSeek API...")
        start_time = time.time()
        
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Based on these news articles, create a JSON report:\n{news_text}"}
            ],
            temperature=0.2,
            max_tokens=1500,
            timeout=30
        )
        
        api_time = time.time() - start_time
        log(f"✅ API response received in {api_time:.1f} seconds")
        
        # Get the response content
        content = response.choices[0].message.content
        log(f"Raw response length: {len(content)} characters")
        log(f"Raw response preview: {content[:200]}...")
        
        # Try to parse JSON
        try:
            result = json.loads(content)
            log("✅ Successfully parsed JSON response")
        except json.JSONDecodeError as e:
            log(f"❌ JSON parse error: {e}", "ERROR")
            log("Attempting to extract JSON from response...")
            
            # Try to find JSON in the response (in case there's extra text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    log("✅ Extracted and parsed JSON from response")
                except:
                    log("❌ Could not parse extracted JSON", "ERROR")
                    result = None
            else:
                result = None
        
        if result:
            # Ensure all required fields exist
            if "executive_summary" not in result:
                result["executive_summary"] = "Summary not available"
            if "factory_news" not in result:
                result["factory_news"] = []
            if "tech_table" not in result:
                result["tech_table"] = []
            if "expos" not in result:
                result["expos"] = []
            
            log(f"Report generated: factory={len(result['factory_news'])}, tech={len(result['tech_table'])}, expos={len(result['expos'])}")
            return result
        else:
            # Return fallback report
            log("Using fallback report template", "WARNING")
            return {
                "executive_summary": "Based on today's news, several developments in Southeast Asian manufacturing and technology sectors were identified.",
                "factory_news": [],
                "tech_table": [],
                "expos": []
            }
        
    except Exception as e:
        log(f"❌ API error: {e}", "ERROR")
        traceback.print_exc()
        # Return fallback report
        return {
            "executive_summary": "Technical issue generating full report. Please check back later.",
            "factory_news": [],
            "tech_table": [],
            "expos": []
        }

def create_html_report(report_data, news_items):
    """Create HTML report from data"""
    log("Creating HTML report...")
    date = datetime.now().strftime('%B %d, %Y')
    
    # Factory news HTML
    factory_html = ""
    for item in report_data.get("factory_news", []):
        company = item.get('company', 'Unknown')
        location = item.get('location', '')
        details = item.get('details', '')
        link = item.get('link', '#')
        factory_html += f"""
        <div style="margin:15px 0; padding:15px; border-left:4px solid #0066cc; background:#f8f9fa;">
            <strong style="font-size:1.1em;">{company}</strong> - {location}<br>
            <p style="margin:8px 0;">{details}</p>
            <small><a href="{link}" style="color:#0066cc;">Source</a></small>
        </div>
        """
    
    # Tech table HTML
    tech_html = ""
    for item in report_data.get("tech_table", []):
        name = item.get('name', '')
        application = item.get('application', '')
        suppliers = item.get('suppliers', [])
        if isinstance(suppliers, list):
            suppliers_text = ", ".join(suppliers)
        else:
            suppliers_text = str(suppliers)
        tech_html += f"<tr><td><strong>{name}</strong></td><td>{application}</td><td>{suppliers_text}</td></tr>"
    
    # Expos HTML
    expos_html = ""
    for item in report_data.get("expos", []):
        name = item.get('name', '')
        date_val = item.get('date', '')
        location = item.get('location', '')
        link = item.get('link', '#')
        expos_html += f"""
        <div style="margin:15px 0; padding:15px; background:#f8f9fa; border-radius:5px;">
            <strong style="font-size:1.1em;">{name}</strong><br>
            📅 {date_val} | 📍 {location}<br>
            <a href="{link}" style="color:#0066cc;">Official Website</a>
        </div>
        """
    
    # Stats
    factory_count = len(report_data.get("factory_news", []))
    tech_count = len(report_data.get("tech_table", []))
    expo_count = len(report_data.get("expos", []))
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SEA Tech Report - {date}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            margin: 30px;
            line-height: 1.6;
            color: #333;
            background: #fff;
        }}
        h1 {{
            color: #1a1a1a;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #0066cc;
            margin: 30px 0 20px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin: 30px 0;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            flex: 1;
            min-width: 150px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: #0066cc;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 12px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>📊 Southeast Asia Tech Report - {date}</h1>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{factory_count}</div>
            <div class="stat-label">Factory Projects</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{tech_count}</div>
            <div class="stat-label">New Technologies</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{expo_count}</div>
            <div class="stat-label">Exhibitions</div>
        </div>
    </div>
    
    <h2>📋 Executive Summary</h2>
    <p style="background:#f8f9fa; padding:20px; border-radius:8px;">{report_data.get('executive_summary', 'No summary available.')}</p>
    
    <h2>🏭 Factory News</h2>
    {factory_html if factory_html else '<p style="color:#666;">No factory news today.</p>'}
    
    <h2>🔬 New Technologies</h2>
    <table>
        <tr>
            <th>Technology</th>
            <th>Application</th>
            <th>Suppliers</th>
        </tr>
        {tech_html if tech_html else '<tr><td colspan="3" style="text-align:center; color:#666;">No technology news today.</td></tr>'}
    </table>
    
    <h2>🎪 Exhibitions</h2>
    {expos_html if expos_html else '<p style="color:#666;">No exhibition news today.</p>'}
    
    <div class="footer">
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Articles analyzed: {len(news_items)}<br>
        Source: Tech News RSS | Daily Report
    </div>
</body>
</html>"""
    
    # Save HTML locally for debugging
    try:
        with open("report.html", "w", encoding='utf-8') as f:
            f.write(html)
        log("✅ Saved report.html")
    except Exception as e:
        log(f"⚠️ Could not save HTML: {e}", "WARNING")
    
    return html

def send_email(subject, html_content):
    """Send email with report"""
    log("\n" + "="*40)
    log("SENDING EMAIL")
    log("="*40)
    
    try:
        # Validate configuration
        if not EMAIL_CONFIG["sender_email"]:
            log("❌ SENDER_EMAIL is missing", "ERROR")
            return False
        if not EMAIL_CONFIG["sender_password"]:
            log("❌ SENDER_PASSWORD is missing", "ERROR")
            return False
        if not EMAIL_CONFIG["receiver_email"]:
            log("❌ RECEIVER_EMAIL is missing", "ERROR")
            return False
        
        # Parse recipients using our fixed function
        recipients = parse_recipients(EMAIL_CONFIG["receiver_email"])
        
        if not recipients:
            log("❌ No valid email recipients found", "ERROR")
            return False
        
        # Test SMTP connection first
        if not test_smtp_connection():
            log("❌ SMTP connection test failed", "ERROR")
            return False
        
        # Test login
        if not test_smtp_login():
            log("❌ SMTP login test failed", "ERROR")
            return False
        
        # Initialize yagmail
        log("Initializing yagmail...")
        yag = yagmail.SMTP(
            user=EMAIL_CONFIG["sender_email"],
            password=EMAIL_CONFIG["sender_password"],
            host=EMAIL_CONFIG["smtp_host"],
            port=EMAIL_CONFIG["smtp_port"],
            smtp_starttls=True,
            smtp_ssl=False
        )
        log("✅ yagmail initialized")
        
        # Send email
        log(f"Sending to: {recipients}")
        log(f"Subject: {subject}")
        log(f"Content length: {len(html_content)} chars")
        
        yag.send(
            to=recipients,
            subject=subject,
            contents=html_content
        )
        
        log("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        log(f"❌ Email failed: {e}", "ERROR")
        traceback.print_exc()
        return False

# ==================== MAIN ====================

def main():
    log("\n" + "="*60)
    log("MAIN FUNCTION STARTED")
    log("="*60)
    
    start_time = time.time()
    
    # Step 1: Fetch news
    log("\n📡 STEP 1: Fetching news...")
    news_items = fetch_news()
    
    if not news_items:
        log("❌ No news found, exiting", "ERROR")
        return
    
    # Step 2: Generate report
    log("\n🤖 STEP 2: Generating report...")
    report_data = generate_report(news_items)
    
    # Even if report generation partially fails, continue
    if not report_data:
        log("⚠️ Report generation returned None, creating minimal report", "WARNING")
        report_data = {
            "executive_summary": "Today's news summary based on fetched articles.",
            "factory_news": [],
            "tech_table": [],
            "expos": []
        }
    
    # Step 3: Create HTML
    log("\n🎨 STEP 3: Creating HTML...")
    html_content = create_html_report(report_data, news_items)
    
    # Step 4: Send email
    log("\n📧 STEP 4: Sending email...")
    subject = f"📊 SEA Tech Report {datetime.now().strftime('%Y-%m-%d')}"
    
    email_sent = send_email(subject, html_content)
    
    # Final status
    elapsed = time.time() - start_time
    log("\n" + "="*60)
    log(f"SCRIPT COMPLETED in {elapsed:.1f} seconds")
    log(f"Email sent: {'✅ YES' if email_sent else '❌ NO'}")
    log("="*60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ Unhandled exception: {e}", "ERROR")
        traceback.print_exc()
