#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Tech Intelligence Report - Stable Version
Compatible with OpenAI v0.28.1
"""

import os
import json
import hashlib
import feedparser
import requests
from datetime import datetime, timedelta
import openai
from sentence_transformers import SentenceTransformer
from jinja2 import Environment, FileSystemLoader
import yagmail
from weasyprint import HTML
import tempfile
import re
from typing import Dict, List, Any
import time

# ==================== CONFIGURATION ====================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Configure OpenAI for DeepSeek (v0.28.1 style)
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

# Enhanced RSS Feeds
RSS_FEEDS = [
    # Major Tech News
    {"url": "https://technews.tw/feed/", "category": "tech", "region": "taiwan"},
    {"url": "https://www.digitimes.com.tw/rss/rptlist.asp", "category": "industry", "region": "taiwan"},
    {"url": "https://www.ledinside.cn/rss.xml", "category": "semiconductor", "region": "china"},
    {"url": "https://www.moneydj.com/KMDJ/NewsCenter/RSS.aspx?c=MB020000", "category": "finance", "region": "taiwan"},
    
    # Southeast Asia Focus
    {"url": "https://www.bangkokpost.com/rss/data/business.xml", "category": "business", "region": "thailand"},
    {"url": "https://www.thestar.com.my/rss/business", "category": "business", "region": "malaysia"},
    {"url": "https://www.straitstimes.com/news/business/rss.xml", "category": "business", "region": "singapore"},
    
    # Industry Publications
    {"url": "https://www.electronicproducts.com/feed/", "category": "components", "region": "global"},
    {"url": "https://www.eejournal.com/feed/", "category": "semiconductor", "region": "global"},
    {"url": "https://semiengineering.com/feed/", "category": "semiconductor", "region": "global"},
    
    # Exhibition News
    {"url": "https://www.awe.com.cn/rss/news.xml", "category": "exhibition", "region": "china"},
]

# Keywords for filtering
KEYWORDS = {
    "manufacturing": [
        "factory", "plant", "manufacturing", "production line", "mass production",
        "Thailand", "Vietnam", "Indonesia", "Malaysia", "Singapore", "Southeast Asia",
        "investment", "expansion", "groundbreaking", "facility", "assembly plant"
    ],
    "technology": [
        "AR", "VR", "AI", "smart glasses", "AR glasses", "VR headset",
        "AI glasses", "wearable", "display technology", "MicroLED", "OLED",
        "sensor", "chipset", "processor", "battery", "electrochromic", "waveguide"
    ],
    "suppliers": [
        "supplier", "vendor", "manufacturer", "OEM", "ODM", "component supplier",
        "Foxconn", "Pegatron", "Wistron", "Quanta", "Compal", "Luxshare", "Goertek",
        "BOE", "TCL CSOT"
    ],
    "exhibition": [
        "exhibition", "trade show", "conference", "expo", "summit",
        "AWE", "CES", "MWC", "IFA", "SEMICON", "展会", "博览会"
    ]
}

# ==================== INITIALIZATION ====================

# Simple in-memory cache for deduplication
news_cache = set()

# Jinja2 template engine
template_env = Environment(loader=FileSystemLoader('templates'))

# ==================== FUNCTIONS ====================

def fetch_detailed_news():
    """
    Fetch news with enhanced detail extraction
    """
    news_items = []
    
    for feed in RSS_FEEDS:
        try:
            print(f"Fetching: {feed['url']}")
            parsed = feedparser.parse(feed['url'])
            
            for entry in parsed.entries[:20]:
                title = entry.get('title', '')
                summary = entry.get('summary', '') or entry.get('description', '')
                link = entry.get('link', '')
                
                content = entry.get('content', [{'value': ''}])[0].get('value', '')
                full_text = f"{title} {summary} {content[:1000]}".lower()
                
                # Keyword filtering
                if not any(kw.lower() in full_text for kw in 
                          KEYWORDS['manufacturing'] + KEYWORDS['technology'] + 
                          KEYWORDS['suppliers'] + KEYWORDS['exhibition']):
                    continue
                
                published = entry.get('published', '')
                if not published:
                    published = entry.get('updated', datetime.now().strftime('%Y-%m-%d'))
                
                source_name = feed['url'].replace('https://', '').replace('www.', '').split('/')[0]
                
                # Generate unique ID for deduplication
                news_id = hashlib.md5(f"{title}{link}".encode()).hexdigest()
                
                # Simple deduplication
                if news_id in news_cache:
                    continue
                
                news_cache.add(news_id)
                if len(news_cache) > 1000:
                    news_cache.clear()
                
                # Extract company names
                company_matches = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:Corp|Inc|Ltd|Company|集团|公司)', title + " " + summary)
                
                news_items.append({
                    "id": news_id,
                    "title": title,
                    "summary": summary[:800],
                    "content": content[:2000],
                    "link": link,
                    "source": feed['url'],
                    "source_name": source_name,
                    "published": published,
                    "category": feed['category'],
                    "region": feed.get('region', 'global'),
                    "extracted_companies": company_matches[:5]
                })
                
        except Exception as e:
            print(f"Failed to fetch {feed['url']}: {e}")
            continue
    
    print(f"Total fetched: {len(news_items)} relevant articles")
    return news_items

def generate_detailed_english_report(news_items):
    """
    Generate comprehensive English report using DeepSeek (OpenAI v0.28.1 compatible)
    """
    if not news_items:
        return {
            "executive_summary": "No relevant news today.",
            "factory_news": [],
            "tech_table": [],
            "tech_news": [],
            "expos": [],
            "manufacturing_trends": [],
            "tech_forecast": [],
            "stats": {
                "factory_count": 0,
                "tech_count": 0,
                "supplier_count": 0,
                "expo_count": 0,
                "factory_trend": 0,
                "tech_breakdown": "N/A",
                "new_suppliers": 0
            }
        }
    
    # Prepare news input
    news_input = []
    for i, item in enumerate(news_items[:40]):  # Limit to 40 articles
        news_input.append({
            "index": i+1,
            "title": item['title'],
            "summary": item['summary'][:300],
            "source": item['source_name'],
            "link": item['link'],
            "published": item['published'],
            "category": item['category'],
            "region": item['region']
        })
    
    system_prompt = """You are a senior industry analyst specializing in Southeast Asian manufacturing. Generate a detailed English intelligence report with this exact JSON format:

{
  "executive_summary": "2-3 paragraph summary of key developments",
  "factory_news": [
    {
      "company": "Company name",
      "location": "Specific location",
      "facility_type": "Type of facility",
      "production_details": "What they're making",
      "investment_amount": "Investment amount if available",
      "production_start": "Start date",
      "link": "Source URL",
      "source_name": "Source name"
    }
  ],
  "tech_table": [
    {
      "name": "Technology name",
      "application": "Application area",
      "suppliers": [{"name": "Supplier name"}],
      "readiness": "Mass Production/Prototype/R&D"
    }
  ],
  "tech_news": [
    {
      "title": "News title",
      "summary": "Brief summary",
      "link": "URL",
      "source_name": "Source"
    }
  ],
  "expos": [
    {
      "name": "Exhibition name",
      "date": "Date range",
      "location": "Venue",
      "exhibitors": ["Exhibitor names"],
      "link": "Official website"
    }
  ],
  "stats": {
    "factory_count": 0,
    "tech_count": 0,
    "supplier_count": 0,
    "expo_count": 0
  }
}

Base everything ONLY on the provided news. Use English only."""

    try:
        # OpenAI v0.28.1 compatible call
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate report from these news articles:\n{json.dumps(news_input, indent=2)}"}
            ],
            temperature=0.2,
            max_tokens=3000
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Ensure stats exist
        if "stats" not in result:
            result["stats"] = {
                "factory_count": len(result.get("factory_news", [])),
                "tech_count": len(result.get("tech_table", [])),
                "supplier_count": sum(len(item.get("suppliers", [])) for item in result.get("tech_table", [])),
                "expo_count": len(result.get("expos", []))
            }
        
        return result
        
    except Exception as e:
        print(f"API call failed: {e}")
        return {
            "executive_summary": f"Report generation temporarily unavailable.",
            "factory_news": [],
            "tech_table": [],
            "tech_news": [],
            "expos": [],
            "manufacturing_trends": [],
            "tech_forecast": [],
            "stats": {
                "factory_count": 0,
                "tech_count": 0,
                "supplier_count": 0,
                "expo_count": 0
            }
        }

def render_english_report(report_data):
    """
    Render HTML report using English template
    """
    try:
        template = template_env.get_template('english_report_template.html')
    except:
        # If template not found, use simple HTML
        html = f"""
        <html>
        <head><title>Tech Report {datetime.now().strftime('%Y-%m-%d')}</title></head>
        <body>
            <h1>Tech Report {datetime.now().strftime('%Y-%m-%d')}</h1>
            <h2>Executive Summary</h2>
            <p>{report_data.get('executive_summary', 'No summary')}</p>
            <h2>Factory News ({report_data['stats']['factory_count']})</h2>
            {''.join([f"<h3>{f.get('company', 'Unknown')}</h3><p>{f.get('location', '')} - {f.get('production_details', '')}</p>" for f in report_data.get('factory_news', [])])}
        </body>
        </html>
        """
        return html
    
    template_data = {
        "date": datetime.now().strftime('%B %d, %Y'),
        "generate_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        "news_count": len(news_cache),
        "executive_summary": report_data.get("executive_summary", "No summary available."),
        "stats": report_data.get("stats", {}),
        "factory_news": report_data.get("factory_news", []),
        "tech_table": report_data.get("tech_table", []),
        "tech_news": report_data.get("tech_news", []),
        "expos": report_data.get("expos", [])
    }
    
    return template.render(**template_data)

def generate_pdf(html_content):
    """Generate PDF from HTML"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = tmp.name
        
        HTML(string=html_content).write_pdf(pdf_path)
        return pdf_path
        
    except Exception as e:
        print(f"PDF generation failed: {e}")
        return None

def parse_recipients(recipients_string):
    """Parse multiple email addresses"""
    # Replace common delimiters
    for delimiter in [';', '\n', '\r', '|']:
        recipients_string = recipients_string.replace(delimiter, ',')
    
    # Split and clean
    emails = [email.strip() for email in recipients_string.split(',') if email.strip()]
    
    # Basic validation
    valid = [e for e in emails if '@' in e and '.' in e]
    
    return valid

def send_email(subject, html_content, pdf_path=None):
    """Send email with report"""
    try:
        yag = yagmail.SMTP(
            user=EMAIL_CONFIG["sender_email"],
            password=EMAIL_CONFIG["sender_password"],
            host=EMAIL_CONFIG["smtp_host"],
            port=EMAIL_CONFIG["smtp_port"]
        )
        
        recipients = parse_recipients(EMAIL_CONFIG["receiver_email"])
        
        if not recipients:
            print("❌ No valid email recipients found")
            return False
        
        attachments = [pdf_path] if pdf_path else []
        
        yag.send(
            to=recipients,
            subject=subject,
            contents=html_content,
            attachments=attachments
        )
        
        print(f"✅ Email sent to {len(recipients)} recipients")
        
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

# ==================== MAIN ====================

def main():
    print(f"\n{'='*60}")
    print(f"Daily Tech Intelligence Report")
    print(f"Start time: {datetime.now()}")
    print(f"{'='*60}\n")
    
    # Step 1: Fetch news
    print("📡 Step 1/4: Fetching news...")
    all_news = fetch_detailed_news()
    print(f"   → {len(all_news)} articles collected")
    
    if not all_news:
        print("⚠️ No articles today. Skipping.")
        return
    
    # Step 2: Generate report
    print(f"\n🤖 Step 2/4: Generating report with DeepSeek...")
    report_data = generate_detailed_english_report(all_news)
    report_data["news_count"] = len(all_news)
    
    print(f"   ✓ Report generated")
    print(f"   ├─ Factory news: {report_data['stats']['factory_count']}")
    print(f"   ├─ Technologies: {report_data['stats']['tech_count']}")
    print(f"   └─ Exhibitions: {report_data['stats']['expo_count']}")
    
    # Step 3: Render HTML
    print(f"\n🎨 Step 3/4: Rendering HTML...")
    html_report = render_english_report(report_data)
    
    # Step 4: Send email
    print(f"\n📧 Step 4/4: Sending email...")
    pdf_path = generate_pdf(html_report)
    
    subject = f"📊 SEA Tech Report {datetime.now().strftime('%Y-%m-%d')}"
    send_email(subject, html_report, pdf_path)
    
    print(f"\n{'='*60}")
    print(f"✅ Complete!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
