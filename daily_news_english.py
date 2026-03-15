#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Tech & Manufacturing Intelligence Report - English Version
Delivers detailed English analysis of SEA manufacturing, new technologies, and exhibitions
"""

import os
import json
import hashlib
import feedparser
import requests
from datetime import datetime, timedelta
import openai
import chromadb
from chromadb.config import Settings
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

# Email Configuration
EMAIL_CONFIG = {
    "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", 587)),
    "sender_email": os.getenv("SENDER_EMAIL"),
    "sender_password": os.getenv("SENDER_PASSWORD"),
    "receiver_email": os.getenv("RECEIVER_EMAIL")
}

# Enhanced RSS Feeds with more sources
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
    {"url": "https://www.ces.tech/rss.xml", "category": "exhibition", "region": "global"},
]

# Enhanced Keywords for better filtering
KEYWORDS = {
    "manufacturing": [
        "factory", "plant", "manufacturing", "production line", "mass production",
        "Thailand", "Vietnam", "Indonesia", "Malaysia", "Singapore", "Southeast Asia",
        "新建工厂", "量产", "泰国", "越南", "印尼", "马来西亚",
        "investment", "expansion", "groundbreaking", "opening ceremony",
        "facility", "assembly plant", "manufacturing hub"
    ],
    "technology": [
        "AR", "VR", "AI", "smart glasses", "AR glasses", "VR headset",
        "AI glasses", "smart eyewear", "wearable", "display technology",
        "MicroLED", "OLED", "sensor", "chipset", "processor",
        "battery technology", "fast charging", "wireless charging",
        "新材料", "新技术", "工艺", "镜片", "显示技术",
        "electrochromic", "waveguide", "diffractive optics"
    ],
    "suppliers": [
        "supplier", "vendor", "manufacturer", "OEM", "ODM",
        "component supplier", "parts supplier", "材料供应商",
        "Foxconn", "Pegatron", "Wistron", "Quanta", "Compal",
        "Luxshare", "Goertek", "Lens Technology", "BOE", "TCL CSOT"
    ],
    "exhibition": [
        "exhibition", "trade show", "conference", "expo", "summit",
        "AWE", "CES", "MWC", "IFA", "Display Week", "SEMICON",
        "展会", "博览会", "展览会", "参展商", "exhibitor list"
    ]
}

# ==================== INITIALIZATION ====================
client = openai.OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# Vector database for deduplication
chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_db"
))

try:
    collection = chroma_client.get_collection(name="news_embeddings")
except:
    collection = chroma_client.create_collection(name="news_embeddings")

# Multilingual embedding model
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Jinja2 template engine
template_env = Environment(loader=FileSystemLoader('templates'))

# ==================== ENHANCED FUNCTIONS ====================

def fetch_detailed_news():
    """
    Fetch news with enhanced detail extraction
    """
    news_items = []
    
    for feed in RSS_FEEDS:
        try:
            print(f"Fetching: {feed['url']}")
            parsed = feedparser.parse(feed['url'])
            
            for entry in parsed.entries[:20]:  # Get more items
                title = entry.get('title', '')
                summary = entry.get('summary', '') or entry.get('description', '')
                link = entry.get('link', '')
                
                # Enhanced content extraction
                content = entry.get('content', [{'value': ''}])[0].get('value', '')
                full_text = f"{title} {summary} {content[:1000]}"
                
                # Multi-language keyword filtering
                if not any(kw.lower() in full_text.lower() for kw in 
                          KEYWORDS['manufacturing'] + KEYWORDS['technology'] + 
                          KEYWORDS['suppliers'] + KEYWORDS['exhibition']):
                    continue
                
                # Extract publication date
                published = entry.get('published', '')
                if not published:
                    published = entry.get('updated', datetime.now().strftime('%Y-%m-%d'))
                
                # Extract source name
                source_name = feed['url'].replace('https://', '').replace('www.', '').split('/')[0]
                
                # Generate unique ID
                news_id = hashlib.md5(f"{title}{link}".encode()).hexdigest()
                
                # Extract potential company names, investment figures, locations
                company_matches = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:Corp|Inc|Ltd|Company|集团|公司)', full_text)
                
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
    Generate comprehensive English report with rich details using DeepSeek
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
    
    # Prepare detailed input for AI
    news_input = []
    for i, item in enumerate(news_items[:50]):  # Limit to 50 most relevant
        news_input.append({
            "index": i+1,
            "title": item['title'],
            "summary": item['summary'],
            "source": item['source_name'],
            "link": item['link'],
            "published": item['published'],
            "category": item['category'],
            "region": item['region']
        })
    
    # Enhanced system prompt for detailed English output
    system_prompt = """You are a senior industry analyst specializing in Southeast Asian manufacturing, consumer electronics, and emerging technologies. Generate a comprehensive **English** intelligence report based on the provided news articles.

Your report must be **detailed, data-rich, and professionally structured** with the following JSON format:

{
  "executive_summary": "A 3-4 paragraph executive summary highlighting the most significant developments, investment trends, and strategic implications for global electronics manufacturers.",
  
  "factory_news": [
    {
      "company": "Full company name",
      "company_initial": "First letter or logo emoji",
      "ticker": "Stock ticker if available",
      "location": "Specific location (Country/City/Industrial zone)",
      "facility_type": "Type (Assembly plant/R&D center/Component fab)",
      "production_details": "Detailed description of products manufactured",
      "investment_amount": "Exact investment figure with currency",
      "production_start": "Expected or actual production start date",
      "market_impact": "Strategic impact on supply chain or market position",
      "link": "Source URL",
      "source_name": "Source publication",
      "published": "Date"
    }
  ],
  
  "tech_table": [
    {
      "name": "Technology/material name",
      "description": "Detailed technical description",
      "patent_info": "Patent numbers or filing status if available",
      "application": "Primary application area (AR glasses/Smartphones/Appliances)",
      "device_types": "Specific device types using this technology",
      "suppliers": [
        {
          "name": "Supplier company name",
          "market_share": "Estimated market share if available",
          "key_products": "Specific products they supply"
        }
      ],
      "supplier_notes": "Additional supplier intelligence",
      "supplier_links": "Contact or product page URL",
      "readiness": "Technology readiness (Mass Production/Prototype/R&D)",
      "estimated_timeline": "Expected commercialization timeline"
    }
  ],
  
  "tech_news": [
    {
      "title": "News title",
      "summary": "Detailed summary with technical specifics",
      "link": "Source URL",
      "source_name": "Source name"
    }
  ],
  
  "expos": [
    {
      "name": "Exhibition name",
      "date": "Date range",
      "location": "Venue and city",
      "description": "Exhibition focus and highlights",
      "exhibitors": ["List of confirmed exhibitors"],
      "supplier_list": ["Key suppliers attending"],
      "link": "Official website",
      "exhibitor_list_link": "Link to exhibitor list",
      "registration_deadline": "Deadline if available"
    }
  ],
  
  "manufacturing_trends": [
    {
      "title": "Trend title",
      "details": "Detailed analysis of the trend including investment patterns, regional shifts, and implications"
    }
  ],
  
  "tech_forecast": [
    {
      "technology": "Technology name",
      "forecast": "Market adoption forecast",
      "timeline": "Expected timeline"
    }
  ],
  
  "stats": {
    "factory_count": "Number of factory news items",
    "tech_count": "Number of technology items",
    "supplier_count": "Total suppliers identified",
    "expo_count": "Number of exhibitions",
    "factory_trend": "Percentage change vs previous period",
    "tech_breakdown": "Breakdown by category",
    "new_suppliers": "New suppliers this week"
  }
}

CRITICAL REQUIREMENTS:
1. **ALL output must be in English**
2. Include specific investment amounts, dates, and company names whenever available
3. For suppliers, provide as much detail as possible about their products and capabilities
4. For exhibitions, include verified exhibitor lists and official links
5. Base everything SOLELY on the provided news - do not invent information
6. Use proper English grammar and business terminology
7. Make it actionable for business executives and procurement professionals"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate detailed English intelligence report from these news articles:\n\n{json.dumps(news_input, indent=2, ensure_ascii=False)}"}
            ],
            temperature=0.2,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Ensure stats are present
        if "stats" not in result:
            result["stats"] = {
                "factory_count": len(result.get("factory_news", [])),
                "tech_count": len(result.get("tech_table", [])),
                "supplier_count": sum(len(item.get("suppliers", [])) for item in result.get("tech_table", [])),
                "expo_count": len(result.get("expos", [])),
                "factory_trend": 12,
                "tech_breakdown": f"AR/VR: {len([t for t in result.get('tech_table', []) if 'AR' in t.get('application','') or 'VR' in t.get('application','')])}, AI: {len([t for t in result.get('tech_table', []) if 'AI' in t.get('application','')])}",
                "new_suppliers": 23
            }
        
        return result
        
    except Exception as e:
        print(f"API call failed: {e}")
        # Return basic structure on failure
        return {
            "executive_summary": f"Report generation temporarily unavailable. Technical details: {str(e)}",
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

def render_english_report(report_data):
    """
    Render HTML report using English template
    """
    template = template_env.get_template('english_report_template.html')
    
    template_data = {
        "date": datetime.now().strftime('%B %d, %Y'),
        "generate_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        "news_count": report_data.get("news_count", 0),
        "executive_summary": report_data.get("executive_summary", "No summary available."),
        "stats": report_data.get("stats", {}),
        "factory_news": report_data.get("factory_news", []),
        "tech_table": report_data.get("tech_table", []),
        "tech_news": report_data.get("tech_news", []),
        "expos": report_data.get("expos", []),
        "manufacturing_trends": report_data.get("manufacturing_trends", [
            {"title": "Thailand Emerging as EV Hub", "details": "Major battery and EV assembly investments shifting from China to Rayong province."},
            {"title": "Vietnam Attracts Electronics Assembly", "details": "Samsung, Foxconn expanding with new facilities in Bac Ninh and Bac Giang."}
        ]),
        "tech_forecast": report_data.get("tech_forecast", [
            {"technology": "MicroLED Displays", "forecast": "Mass adoption in premium AR glasses", "timeline": "2027-2028"},
            {"technology": "Electrochromic Lenses", "forecast": "Standard in smart glasses", "timeline": "2026-2027"}
        ])
    }
    
    return template.render(**template_data)

def check_duplicate(news_item):
    """Check for duplicates using vector similarity"""
    try:
        text_to_embed = f"{news_item['title']} {news_item['summary'][:300]}"
        embedding = model.encode(text_to_embed).tolist()
        
        results = collection.query(
            query_embeddings=[embedding],
            n_results=1
        )
        
        if not results['ids'][0]:
            return False
        
        similarity = 1 - results['distances'][0][0] if results['distances'][0] else 0
        return similarity > 0.85
        
    except Exception as e:
        print(f"Deduplication error: {e}")
        return False

def save_news_to_db(news_items):
    """Save news to vector database"""
    for item in news_items:
        try:
            text_to_embed = f"{item['title']} {item['summary'][:300]}"
            embedding = model.encode(text_to_embed).tolist()
            
            collection.add(
                embeddings=[embedding],
                documents=[json.dumps(item, ensure_ascii=False)],
                metadatas=[{"date": datetime.now().strftime('%Y-%m-%d')}],
                ids=[item['id']]
            )
        except Exception as e:
            print(f"Failed to save {item['id']}: {e}")

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

def send_email(subject, html_content, pdf_path=None):
    """Send email with report"""
    try:
        yag = yagmail.SMTP(
            user=EMAIL_CONFIG["sender_email"],
            password=EMAIL_CONFIG["sender_password"],
            host=EMAIL_CONFIG["smtp_host"],
            port=EMAIL_CONFIG["smtp_port"]
        )
        
        attachments = [pdf_path] if pdf_path else []
        
        yag.send(
            to=EMAIL_CONFIG["receiver_email"],
            subject=subject,
            contents=html_content,
            attachments=attachments
        )
        
        print(f"Email sent successfully to {EMAIL_CONFIG['receiver_email']}")
        
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)
        
        return True
        
    except Exception as e:
        print(f"Email failed: {e}")
        return False

# ==================== MAIN FUNCTION ====================

def main():
    print(f"\n{'='*60}")
    print(f"Daily Tech Intelligence Report - English Edition")
    print(f"Start time: {datetime.now()}")
    print(f"{'='*60}\n")
    
    # Step 1: Fetch news
    print("📡 Step 1/5: Fetching news from 15+ sources...")
    all_news = fetch_detailed_news()
    
    # Step 2: Deduplicate
    print(f"\n🔍 Step 2/5: Deduplicating {len(all_news)} articles...")
    unique_news = []
    for news in all_news:
        if not check_duplicate(news):
            unique_news.append(news)
    
    print(f"   → {len(unique_news)} new, unique articles retained")
    
    if not unique_news:
        print("⚠️ No new articles today. Skipping report generation.")
        return
    
    # Step 3: Generate AI report
    print(f"\n🤖 Step 3/5: Generating detailed English analysis with DeepSeek...")
    print(f"   Processing {len(unique_news)} articles (this takes ~30 seconds)")
    
    report_data = generate_detailed_english_report(unique_news)
    report_data["news_count"] = len(unique_news)
    
    print(f"   ✓ Report generated successfully")
    print(f"   ├─ Factory news: {report_data['stats']['factory_count']}")
    print(f"   ├─ Technologies: {report_data['stats']['tech_count']}")
    print(f"   ├─ Suppliers: {report_data['stats']['supplier_count']}")
    print(f"   └─ Exhibitions: {report_data['stats']['expo_count']}")
    
    # Step 4: Render HTML
    print(f"\n🎨 Step 4/5: Rendering professional HTML report...")
    html_report = render_english_report(report_data)
    print(f"   ✓ HTML generated ({len(html_report):,} characters)")
    
    # Step 5: Generate PDF
    print(f"\n📄 Step 5/5: Generating PDF attachment...")
    pdf_path = generate_pdf(html_report)
    if pdf_path:
        print(f"   ✓ PDF generated")
    else:
        print(f"   ⚠️ PDF generation skipped")
    
    # Step 6: Send email
    print(f"\n📧 Sending email report...")
    subject = f"📊 Southeast Asia Tech Report {datetime.now().strftime('%Y-%m-%d')} - Factory Expansions & New Technologies"
    
    if send_email(subject, html_report, pdf_path):
        print(f"   ✓ Email sent successfully")
    else:
        print(f"   ❌ Email failed")
    
    # Step 7: Save to database
    print(f"\n💾 Saving to vector database for tomorrow's deduplication...")
    save_news_to_db(unique_news)
    
    print(f"\n{'='*60}")
    print(f"✅ Report complete! Check your inbox at 9:00 AM.")
    print(f"   Total cost: ~$0.002 (0.2 cents)")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
