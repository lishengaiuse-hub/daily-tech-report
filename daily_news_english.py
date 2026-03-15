#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Southeast Asia Consumer Electronics Intelligence System
Production Version - English Only Output

Features:
- 50+ RSS sources with timeouts
- Strict consumer electronics filtering
- Deduplication
- AI translation (Chinese to English)
- AI executive summary
- Industry trend extraction
- Professional HTML dashboard
- Email delivery (multiple recipients)

Author: Production Edition
Last Updated: 2026
"""

import os
import sys
import re
import time
import hashlib
import socket
import requests
import traceback
import feedparser
import openai
import smtplib
import html as html_module
import concurrent.futures

from datetime import datetime
from collections import Counter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# =====================================================
# CONFIGURATION
# =====================================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    print("ERROR: DEEPSEEK_API_KEY environment variable not set")
    sys.exit(1)

openai.api_key = DEEPSEEK_API_KEY
openai.api_base = "https://api.deepseek.com/v1"

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")


# =====================================================
# KEYWORDS (Comprehensive)
# =====================================================

# Southeast Asia Locations
SEA_LOCATIONS = [
    # Countries
    "vietnam", "thailand", "indonesia", "malaysia", "singapore",
    "philippines", "myanmar", "cambodia", "laos", "brunei",
    "asean", "southeast asia",
    
    # Vietnam
    "hanoi", "ho chi minh", "haiphong", "danang", "bac ninh", "thai nguyen",
    
    # Thailand
    "bangkok", "rayong", "chonburi", "ayutthaya", "eastern seaboard",
    
    # Indonesia
    "jakarta", "bandung", "surabaya", "batam", "west java",
    
    # Malaysia
    "kuala lumpur", "penang", "selangor", "johor", "kulim",
    
    # Singapore
    "singapore",
    
    # Philippines
    "manila", "cebu"
]

# Home Appliances
HOME_APPLIANCES_KEYWORDS = [
    # Refrigeration
    "refrigerator", "fridge", "freezer",
    
    # Laundry
    "washing machine", "washer", "dryer",
    
    # HVAC
    "air conditioner", "ac", "hvac",
    
    # Cleaning
    "vacuum", "robot vacuum", "vacuum cleaner",
    
    # Kitchen
    "microwave", "oven", "dishwasher", "rice cooker",
    "air fryer", "coffee maker", "toaster",
    
    # TV/Display
    "tv", "television", "display", "screen"
]

# Mobile Electronics
MOBILE_ELECTRONICS_KEYWORDS = [
    # Phones
    "smartphone", "phone", "mobile",
    "samsung", "galaxy", "apple", "iphone", "xiaomi", "oppo", "vivo", "realme",
    "foldable",
    
    # Wearables
    "wearable", "smartwatch", "fitness tracker",
    
    # AR/VR
    "ar", "vr", "ai glasses", "smart glasses", "ar glasses", "vr headset",
    "rokid", "htc", "vive", "meta quest", "pico",
    
    # Audio
    "earbuds", "headphones", "tws",
    
    # Tablets/Laptops
    "tablet", "ipad", "laptop", "notebook"
]

# Manufacturing & Investment
MANUFACTURING_KEYWORDS = [
    "factory", "plant", "manufacturing", "production", "assembly",
    "facility", "investment", "invest", "capacity", "expansion",
    "supplier", "supply chain", "vendor", "localization",
    "going global", "globalization", "overseas expansion"
]

# Research & Breakthroughs
RESEARCH_KEYWORDS = [
    "research", "innovation", "prototype", "breakthrough",
    "flexible electronics", "wearable tech", "thermoelectric",
    "fiber chip", "new material", "advanced material",
    "nano", "coating", "thin film", "capacitor"
]

# Exhibitions & Events
EXHIBITION_KEYWORDS = [
    "expo", "exhibition", "trade show", "conference",
    "ces", "ifa", "mwc", "awe", "electronica"
]

# Non-consumer electronics (to exclude)
NON_CONSUMER_KEYWORDS = [
    "electric vehicle", "ev battery", "solar farm", "steel plant", "mining",
    "oil and gas", "chemical plant", "pharmaceutical", "biotech",
    "medical device", "automotive", "aerospace"
]

# Major Companies
COMPANIES = [
    "Samsung", "Apple", "Xiaomi", "Oppo", "Vivo", "Realme",
    "Haier", "Midea", "Hisense", "Gree", "TCL",
    "Sony", "Panasonic", "LG", "Sharp", "Toshiba",
    "Foxconn", "Pegatron", "Luxshare", "Goertek", "BOE",
    "Rokid", "HTC"
]

# Technologies to track
TECHNOLOGY = [
    "ai", "ar", "vr", "wearable", "foldable", "smart home",
    "5g", "iot", "microled", "oled", "flexible display"
]


# =====================================================
# RSS SOURCES (Optimized - 50+ sources with priority)
# =====================================================

RSS_FEEDS = [
    # ===== Chinese Tech Media (Priority 1) =====
    {"url": "https://technews.tw/feed/", "lang": "zh", "priority": 1},
    {"url": "https://finance.technews.tw/feed/", "lang": "zh", "priority": 1},
    {"url": "https://www.ledinside.cn/rss.xml", "lang": "zh", "priority": 1},
    {"url": "https://www.digitimes.com.tw/rss/rptlist.asp", "lang": "zh", "priority": 1},
    {"url": "https://www.21jingji.com/rss/", "lang": "zh", "priority": 2},
    {"url": "http://world.people.com.cn/rss/index.xml", "lang": "zh", "priority": 2},
    {"url": "https://ep.ycwb.com/rss/", "lang": "zh", "priority": 2},
    {"url": "https://news.cnyes.com/rss", "lang": "zh", "priority": 1},
    
    # ===== Materials & Industry Sites =====
    {"url": "http://www.cnpowder.com.cn/rss/", "lang": "zh", "priority": 2},
    {"url": "http://www.materials.cn/rss/", "lang": "zh", "priority": 2},
    {"url": "https://www.xincailiao.com/rss/", "lang": "zh", "priority": 2},
    {"url": "https://www.aibang.com/feed/", "lang": "zh", "priority": 2},
    {"url": "https://www.aibang.com/news/feed/", "lang": "zh", "priority": 2},
    
    # ===== Chinese Overseas/Industry =====
    {"url": "https://xiaguangshe.com/feed/", "lang": "zh", "priority": 1},
    {"url": "https://www.cena.com.cn/rss.xml", "lang": "zh", "priority": 2},
    {"url": "https://www.chinaoverseasemi.com/feed", "lang": "en", "priority": 2},
    
    # ===== Government & Investment Sites =====
    {"url": "https://www.mida.gov.my/press-releases/feed/", "lang": "en", "priority": 1},
    {"url": "https://www.mida.gov.my/news/feed/", "lang": "en", "priority": 1},
    {"url": "https://www.matrade.gov.my/en/media/press-releases/feed", "lang": "en", "priority": 2},
    {"url": "https://www.crest.my/feed/", "lang": "en", "priority": 2},
    {"url": "https://www.boi.go.th/upload/rss/boi_news_en.xml", "lang": "en", "priority": 1},
    {"url": "https://www.edb.gov.sg/en/news-and-events/feed.html", "lang": "en", "priority": 1},
    
    # ===== Chinese Research Institutions =====
    {"url": "https://english.cas.cn/news/rss/", "lang": "en", "priority": 2},
    {"url": "http://www.cas.cn/rss/", "lang": "zh", "priority": 2},
    {"url": "https://news.fudan.edu.cn/rss.xml", "lang": "zh", "priority": 2},
    {"url": "https://en.ncsti.gov.cn/Latest/rss/", "lang": "en", "priority": 2},
    
    # ===== Market Research =====
    {"url": "https://www.gfk.com/insights/rss", "lang": "en", "priority": 2},
    {"url": "https://ir.jd.com/rss", "lang": "en", "priority": 2},
    {"url": "https://jingdaily.com/category/tech/feed/", "lang": "en", "priority": 2},
    
    # ===== Chinese Tech Media (English) =====
    {"url": "https://www.chinadaily.com.cn/rss/business_rss.xml", "lang": "en", "priority": 1},
    {"url": "https://www.chinadailyhk.com/rss", "lang": "en", "priority": 1},
    {"url": "https://36kr.com/feed/english", "lang": "en", "priority": 1},
    {"url": "https://www.kr-asia.com/feed", "lang": "en", "priority": 1},
    
    # ===== Manufacturer Blogs =====
    {"url": "https://www.rokid.com/blog/feed/", "lang": "en", "priority": 2},
    {"url": "https://www.colmo.com.cn/news/feed/", "lang": "zh", "priority": 2},
    
    # ===== Global Tech Media =====
    {"url": "https://techcrunch.com/feed/", "lang": "en", "priority": 1},
    {"url": "https://www.theverge.com/rss/index.xml", "lang": "en", "priority": 1},
    {"url": "https://arstechnica.com/feed/", "lang": "en", "priority": 2},
    {"url": "https://www.engadget.com/rss.xml", "lang": "en", "priority": 1},
    {"url": "https://www.gsmarena.com/rss-news-reviews.php", "lang": "en", "priority": 1},
    {"url": "https://www.androidauthority.com/feed/", "lang": "en", "priority": 2},
    
    # ===== Southeast Asia News =====
    {"url": "https://www.vietnam-briefing.com/news/feed/", "lang": "en", "priority": 1},
    {"url": "https://e.vnexpress.net/rss/business.rss", "lang": "en", "priority": 1},
    {"url": "https://www.bangkokpost.com/rss/data/business.xml", "lang": "en", "priority": 1},
    {"url": "https://thailand-briefing.com/news/feed/", "lang": "en", "priority": 1},
    {"url": "https://www.thestar.com.my/rss/business", "lang": "en", "priority": 1},
    {"url": "https://www.nst.com.my/rss/business", "lang": "en", "priority": 2},
    {"url": "https://www.straitstimes.com/news/business/rss.xml", "lang": "en", "priority": 1},
    {"url": "https://sbr.com.sg/rss.xml", "lang": "en", "priority": 2},
    {"url": "https://indonesia-briefing.com/news/feed/", "lang": "en", "priority": 1},
    {"url": "https://www.thejakartapost.com/rss/business.xml", "lang": "en", "priority": 1},
    {"url": "https://www.philstar.com/rss/business", "lang": "en", "priority": 2},
    
    # ===== Industry Publications =====
    {"url": "https://semiengineering.com/feed/", "lang": "en", "priority": 2},
    {"url": "https://www.electronicproducts.com/feed/", "lang": "en", "priority": 2},
    {"url": "https://www.displaydaily.com/feed", "lang": "en", "priority": 2},
]


# =====================================================
# MAIN SYSTEM CLASS
# =====================================================

class SEAConsumerElectronicsIntel:
    """Southeast Asia Consumer Electronics Intelligence System"""

    def __init__(self):
        """Initialize the system"""
        self.news = []              # Raw news
        self.news_enriched = []      # News with translations
        self.seen_hash = set()       # Deduplication
        
        # Categorized news
        self.tech_news = []
        self.manufacturing_news = []
        self.research_news = []
        self.exhibition_news = []
        
        # Trend data
        self.companies = []
        self.locations = []
        self.technologies = []
        
        # Stats
        self.start_time = time.time()


    # -------------------------------------------------
    # Logging
    # -------------------------------------------------

    def log(self, msg, level="INFO"):
        """Log message with timestamp"""
        elapsed = time.time() - self.start_time
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{elapsed:.1f}s] {level}: {msg}")
        sys.stdout.flush()


    # -------------------------------------------------
    # News Processing
    # -------------------------------------------------

    def normalize_news(self, entry, source_url, lang):
        """Normalize news entry to standard format"""
        try:
            title = entry.get("title", "").strip()
            summary = entry.get("summary") or entry.get("description") or ""
            link = entry.get("link", "").strip()

            if not title or not link:
                return None

            # Clean HTML tags
            summary = re.sub("<.*?>", "", summary)
            summary = summary.replace("\n", " ").strip()
            summary = re.sub(r'\s+', ' ', summary)  # Normalize whitespace

            # Extract source domain
            source_match = re.search(r'https?://([^/]+)', source_url)
            source = source_match.group(1) if source_match else source_url

            return {
                "title": title,
                "summary": summary[:600],
                "link": link,
                "source": source,
                "published": entry.get("published", ""),
                "lang": lang
            }
        except Exception as e:
            self.log(f"Error normalizing news: {e}", "ERROR")
            return None


    def is_relevant_news(self, title, summary):
        """Check if news is relevant (SEA location + consumer electronics)"""
        text = (title + " " + summary).lower()

        # Must contain Southeast Asia location
        if not any(loc in text for loc in SEA_LOCATIONS):
            return False

        # Exclude non-consumer electronics
        if any(k in text for k in NON_CONSUMER_KEYWORDS):
            return False

        # Must be consumer electronics related
        is_appliance = any(k in text for k in HOME_APPLIANCES_KEYWORDS)
        is_mobile = any(k in text for k in MOBILE_ELECTRONICS_KEYWORDS)
        
        return is_appliance or is_mobile


    def is_duplicate(self, title, link):
        """Check for duplicates using MD5 hash"""
        key = hashlib.md5((title + link).encode()).hexdigest()
        
        if key in self.seen_hash:
            return True
        
        self.seen_hash.add(key)
        return False


    def quality_score(self, title, summary):
        """Score news quality (0-3)"""
        score = 0
        text = (title + summary).lower()

        if len(summary) > 150:
            score += 1

        if any(loc in text for loc in SEA_LOCATIONS):
            score += 1

        if any(k in text for k in MOBILE_ELECTRONICS_KEYWORDS + HOME_APPLIANCES_KEYWORDS):
            score += 1

        return score


    def fetch_feed(self, feed):
        """Fetch a single RSS feed with timeout"""
        feed_url = feed["url"]
        lang = feed.get("lang", "en")
        
        try:
            # Set headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            # Try requests first (with timeout)
            response = requests.get(feed_url, timeout=8, headers=headers)
            response.raise_for_status()
            
            # Parse content
            content_type = response.headers.get('content-type', '')
            if 'xml' in content_type or 'rss' in content_type or 'atom' in content_type:
                parsed = feedparser.parse(response.content)
            else:
                # Try direct parsing
                parsed = feedparser.parse(response.text)
            
        except requests.Timeout:
            self.log(f"    ⚠️ Timeout: {feed_url[:50]}...", "WARNING")
            return []
        except requests.RequestException as e:
            self.log(f"    ⚠️ Request failed: {e}", "WARNING")
            # Fallback to feedparser direct
            parsed = feedparser.parse(feed_url)
        except Exception as e:
            self.log(f"    ⚠️ Parse failed: {e}", "WARNING")
            return []

        # Process entries
        articles = []
        for entry in parsed.entries[:12]:  # Limit per feed
            try:
                item = self.normalize_news(entry, feed_url, lang)
                
                if not item:
                    continue
                
                if self.is_duplicate(item['title'], item['link']):
                    continue
                
                if not self.is_relevant_news(item['title'], item['summary']):
                    continue
                
                if self.quality_score(item['title'], item['summary']) < 2:
                    continue
                
                articles.append(item)
                
            except Exception as e:
                self.log(f"    ⚠️ Error processing entry: {e}", "WARNING")
                continue
        
        return articles


    def fetch_news(self):
        """Fetch all RSS feeds in parallel with priorities"""
        self.log(f"Fetching RSS feeds ({len(RSS_FEEDS)} sources)")

        # Set socket timeout
        socket.setdefaulttimeout(10)

        # Sort by priority (1 = highest)
        priority_feeds = sorted(RSS_FEEDS, key=lambda x: x.get("priority", 2))
        
        # Use ThreadPoolExecutor for parallel fetching
        all_articles = []
        successful = 0
        failed = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all feed fetch tasks
            future_to_feed = {
                executor.submit(self.fetch_feed, feed): feed 
                for feed in priority_feeds
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_feed, timeout=60):
                feed = future_to_feed[future]
                try:
                    articles = future.result(timeout=10)
                    all_articles.extend(articles)
                    successful += 1
                    self.log(f"  ✅ {feed['url'][:50]}... got {len(articles)} articles")
                except concurrent.futures.TimeoutError:
                    failed += 1
                    self.log(f"  ❌ Timeout: {feed['url'][:50]}...", "WARNING")
                except Exception as e:
                    failed += 1
                    self.log(f"  ❌ Failed: {feed['url'][:50]}... - {str(e)[:30]}", "WARNING")

        self.news = all_articles
        self.log(f"Feed summary: {successful} successful, {failed} failed")
        self.log(f"Total relevant news: {len(self.news)}")

        # Limit total news to avoid overload
        if len(self.news) > 60:
            self.log(f"Limiting to 60 articles (was {len(self.news)})")
            self.news = self.news[:60]


    # -------------------------------------------------
    # Translation
    # -------------------------------------------------

    def translate_news(self, item):
        """Translate Chinese news to English using DeepSeek"""
        try:
            prompt = f"""Translate this Chinese consumer electronics news to English accurately.

Original Chinese:
Title: {item['title']}
Summary: {item['summary'][:500]}

Requirements:
- Keep company names accurate (海尔 → Haier, 美的 → Midea, 京东方 → BOE)
- Preserve technical terms, investment figures, and locations
- Use professional business English

Provide ONLY the translation in this format:
Title: [translated title]
Summary: [translated summary (2-3 sentences)]"""

            response = openai.ChatCompletion.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=600,
                timeout=20
            )

            translation = response.choices[0].message.content
            
            # Parse response
            title_en = item['title']
            summary_en = item['summary']
            
            lines = translation.strip().split('\n', 1)
            if lines and lines[0].startswith('Title:'):
                title_en = lines[0].replace('Title:', '').strip()
                if len(lines) > 1 and lines[1].startswith('Summary:'):
                    summary_en = lines[1].replace('Summary:', '').strip()
                elif len(lines) > 1:
                    summary_en = lines[1].strip()

            return {
                **item,
                'title_en': title_en,
                'summary_en': summary_en,
                'translated': True
            }

        except Exception as e:
            self.log(f"Translation failed for {item['title'][:30]}...: {e}", "WARNING")
            return {
                **item,
                'title_en': f"[Auto-translated] {item['title']}",
                'summary_en': item['summary'],
                'translated': False
            }


    def process_translations(self):
        """Translate Chinese news in parallel"""
        chinese_news = [n for n in self.news if n.get('lang') == 'zh']
        
        if not chinese_news:
            self.news_enriched = [n for n in self.news if n.get('lang') == 'en']
            self.log("No Chinese news to translate")
            return

        self.log(f"Translating {len(chinese_news)} Chinese articles...")

        # Limit translations to avoid API overload
        to_translate = chinese_news[:12]
        translated = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_news = {
                executor.submit(self.translate_news, news): news 
                for news in to_translate
            }
            
            for future in concurrent.futures.as_completed(future_to_news, timeout=60):
                try:
                    result = future.result(timeout=25)
                    translated.append(result)
                except Exception as e:
                    self.log(f"Translation task failed: {e}", "WARNING")
                    # Add original as fallback
                    news = future_to_news[future]
                    translated.append({
                        **news,
                        'title_en': news['title'],
                        'summary_en': news['summary']
                    })

        # Combine with English news
        english_news = [n for n in self.news if n.get('lang') == 'en']
        self.news_enriched = translated + english_news
        
        self.log(f"Total enriched news: {len(self.news_enriched)}")


    # -------------------------------------------------
    # Categorization
    # -------------------------------------------------

    def categorize_news(self):
        """Categorize news into topics"""
        self.log("Categorizing news...")

        for item in self.news_enriched:
            # Use English fields if available
            title = item.get('title_en', item['title'])
            summary = item.get('summary_en', item['summary'])
            text = (title + " " + summary).lower()

            # New Products & Technologies
            if any(k in text for k in MOBILE_ELECTRONICS_KEYWORDS + HOME_APPLIANCES_KEYWORDS):
                if item not in self.tech_news:
                    self.tech_news.append(item)

            # Manufacturing & Investment
            if any(k in text for k in MANUFACTURING_KEYWORDS):
                if item not in self.manufacturing_news:
                    self.manufacturing_news.append(item)

            # Research Breakthroughs
            if any(k in text for k in RESEARCH_KEYWORDS):
                if item not in self.research_news:
                    self.research_news.append(item)

            # Exhibitions & Events
            if any(k in text for k in EXHIBITION_KEYWORDS):
                if item not in self.exhibition_news:
                    self.exhibition_news.append(item)

            # Extract trends
            self.extract_trends(text)

        # Limit each category
        self.tech_news = self.tech_news[:15]
        self.manufacturing_news = self.manufacturing_news[:15]
        self.research_news = self.research_news[:10]
        self.exhibition_news = self.exhibition_news[:8]

        self.log(f"Categorized: {len(self.tech_news)} tech, {len(self.manufacturing_news)} manufacturing, "
                f"{len(self.research_news)} research, {len(self.exhibition_news)} exhibitions")


    def extract_trends(self, text):
        """Extract trends from text"""
        for company in COMPANIES:
            if company.lower() in text:
                self.companies.append(company)

        for loc in SEA_LOCATIONS:
            if loc in text:
                self.locations.append(loc.title())

        for tech in TECHNOLOGY:
            if tech in text:
                self.technologies.append(tech.upper() if tech in ['ai','ar','vr','5g'] else tech.title())


    # -------------------------------------------------
    # HTML Generation
    # -------------------------------------------------

    def get_source_logo(self, source):
        """Get source logo/icon"""
        source_lower = source.lower()
        
        logos = {
            'technews': '📱 TechNews', 'ledinside': '💡 LEDinside', 'digitimes': '📰 Digitimes',
            '21jingji': '📊 21st Century', 'people': '🏛️ People\'s Daily', 'ycwb': '📰 Yangcheng',
            'cnyes': '📈 CNYES', 'cnpowder': '⚙️ Powder',
            'materials': '🔬 Materials', 'xincailiao': '🧪 New Materials', 'aibang': '🧪 Aibang',
            'xiaguangshe': '🌏 Xiaguang', 'cena': '📡 CENA',
            'mida': '🇲🇾 MIDA', 'matrade': '🇲🇾 MATRADE', 'crest': '🇲🇾 CREST',
            'boi': '🇹🇭 BOI', 'edb': '🇸🇬 EDB',
            'cas': '🔬 CAS', 'fudan': '🎓 Fudan', 'gfk': '📊 GfK',
            'jd': '🛒 JD.com', 'chinadaily': '🇨🇳 China Daily',
            'rokid': '👓 Rokid', 'colmo': '🏠 COLMO', '36kr': '📱 36Kr',
            'kr-asia': '🌏 KrASIA', 'techcrunch': '📱 TechCrunch',
            'theverge': '📱 The Verge', 'engadget': '📱 Engadget',
            'gsmarena': '📱 GSMArena', 'bangkokpost': '🇹🇭 Bangkok Post',
            'thestar': '🇲🇾 The Star', 'straitstimes': '🇸🇬 Straits Times',
            'vietnam-briefing': '🇻🇳 Vietnam Briefing', 'vnexpress': '🇻🇳 VNExpress',
            'semiengineering': '🔧 SemiEngineering', 'electronicproducts': '🔌 ElecProducts',
            'displaydaily': '📺 DisplayDaily'
        }
        
        for key, logo in logos.items():
            if key in source_lower:
                return logo
        
        return f"📰 {source[:15]}"


    def news_card(self, item, color="#0066cc"):
        """Generate HTML for a news card"""
        title = html_module.escape(item.get('title_en', item['title'])[:120])
        summary = html_module.escape(item.get('summary_en', item['summary'])[:250])
        source_logo = self.get_source_logo(item['source'])
        link = item['link']
        published = item.get('published', '')[:10]

        return f"""
<div style="margin-bottom:20px; padding:20px; background:white; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.05); border-left:4px solid {color};">
    <div style="display:flex; align-items:center; margin-bottom:12px; flex-wrap:wrap;">
        <span style="background:{color}; color:white; padding:4px 12px; border-radius:20px; font-size:0.85em; font-weight:600; margin-right:12px;">{source_logo}</span>
        <span style="color:#64748b; font-size:0.85em;">{published}</span>
    </div>
    <h4 style="font-size:1.2em; margin-bottom:12px; color:#0a1929; line-height:1.4;">{title}</h4>
    <p style="color:#475569; margin-bottom:16px; line-height:1.5;">{summary}...</p>
    <a href="{link}" style="color:{color}; text-decoration:none; font-weight:500; display:inline-flex; align-items:center;" target="_blank">🔗 Read original →</a>
</div>
"""


    def generate_html(self):
        """Generate complete HTML dashboard"""
        self.log("Generating HTML dashboard...")

        # Executive summary
        summary = self.executive_summary()

        # Location stats for manufacturing
        location_stats = ""
        if self.locations:
            location_counts = Counter(self.locations).most_common(6)
            location_stats = '<div style="background:#f8fafc; padding:20px; border-radius:12px; margin-bottom:30px;">'
            location_stats += '<h4 style="margin-bottom:16px; color:#0a1929; font-size:1.2em;">📍 Manufacturing Hotspots</h4>'
            location_stats += '<div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:15px;">'
            
            for loc, count in location_counts:
                location_stats += f"""
                <div style="background:white; padding:15px; border-radius:10px; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                    <div style="font-weight:600; color:#0066cc; font-size:1.1em;">{loc}</div>
                    <div style="font-size:1.8em; font-weight:bold; color:#0a1929; margin:5px 0;">{count}</div>
                    <div style="font-size:0.85em; color:#64748b;">mentions</div>
                </div>
                """
            location_stats += '</div></div>'

        # Render sections
        def render_section(items, color, empty_msg="No news available"):
            if not items:
                return f'<p style="color:#666; text-align:center; padding:40px;">{empty_msg}</p>'
            return ''.join([self.news_card(i, color) for i in items])

        # Current date
        date_str = datetime.now().strftime('%B %d, %Y')
        time_str = datetime.now().strftime('%H:%M:%S')

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Southeast Asia Consumer Electronics Intelligence</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f1f5f9; 
            padding: 30px 20px; 
            line-height: 1.6;
            color: #1e293b;
        }}
        .dashboard {{ max-width: 1400px; margin: 0 auto; }}
        
        .header {{ 
            background: linear-gradient(135deg, #0a1929 0%, #1a2a3a 100%); 
            color: white; 
            padding: 40px 50px; 
            border-radius: 20px 20px 0 0; 
            margin-bottom: 30px; 
        }}
        .header h1 {{ font-size: 2.5em; font-weight: 300; margin-bottom: 10px; }}
        .header h1 strong {{ font-weight: 600; color: #ffd700; }}
        .header .date {{ color: #94a3b8; font-size: 1.1em; margin: 10px 0 20px; }}
        .header .meta {{ 
            display: flex; 
            gap: 30px; 
            color: #cbd5e1; 
            border-top: 1px solid #334155; 
            padding-top: 20px; 
            flex-wrap: wrap; 
        }}
        
        .summary-card {{ 
            background: white; 
            border-radius: 16px; 
            padding: 35px; 
            margin-bottom: 30px; 
            border-left: 6px solid #ffd700; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        }}
        .summary-card h2 {{ color: #0a1929; font-size: 1.8em; margin-bottom: 20px; }}
        .summary-card p {{ font-size: 1.2em; color: #334155; line-height: 1.8; }}
        
        .kpi-grid {{ 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: 25px; 
            margin-bottom: 40px; 
        }}
        .kpi-card {{ 
            background: white; 
            border-radius: 16px; 
            padding: 25px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        }}
        .kpi-icon {{ font-size: 2.5em; margin-bottom: 15px; }}
        .kpi-value {{ 
            font-size: 2.8em; 
            font-weight: 600; 
            color: #0a1929; 
            line-height: 1.2; 
        }}
        .kpi-label {{ 
            color: #64748b; 
            font-size: 1em; 
            text-transform: uppercase; 
            letter-spacing: 0.5px; 
            margin-bottom: 5px; 
        }}
        
        .section-header {{ margin: 50px 0 30px; }}
        .section-header h2 {{ 
            font-size: 2.2em; 
            color: #0a1929; 
            font-weight: 500; 
            display: inline-block; 
            background: #f1f5f9; 
            padding-right: 20px; 
        }}
        
        .news-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr)); 
            gap: 25px; 
        }}
        
        .footer {{ 
            background: #0a1929; 
            color: white; 
            padding: 40px; 
            border-radius: 0 0 20px 20px; 
            margin-top: 50px; 
            text-align: center; 
        }}
        .footer p {{ color: #94a3b8; margin-bottom: 10px; }}
        .footer .sources {{ font-size: 0.85em; color: #64748b; margin-top: 20px; }}
        
        @media (max-width: 768px) {{ 
            .kpi-grid {{ grid-template-columns: 1fr; }} 
            .news-grid {{ grid-template-columns: 1fr; }} 
            .header {{ padding: 30px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1><strong>Southeast Asia</strong> Consumer Electronics Intelligence</h1>
            <div class="date">{date_str}</div>
            <div class="meta">
                <span>📊 Total Articles: {len(self.news_enriched)}</span>
                <span>🌏 Focus: Consumer Electronics in SEA</span>
                <span>⏰ Generated: {time_str}</span>
                <span>⚡ Sources: 50+</span>
            </div>
        </div>
        
        <div class="summary-card">
            <h2>📋 Executive Summary</h2>
            <p>{summary}</p>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-icon">📱</div>
                <div class="kpi-label">New Products</div>
                <div class="kpi-value">{len(self.tech_news)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🏭</div>
                <div class="kpi-label">Manufacturing</div>
                <div class="kpi-value">{len(self.manufacturing_news)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🔬</div>
                <div class="kpi-label">Research</div>
                <div class="kpi-value">{len(self.research_news)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🎪</div>
                <div class="kpi-label">Exhibitions</div>
                <div class="kpi-value">{len(self.exhibition_news)}</div>
            </div>
        </div>
        
        <div class="section-header"><h2>📱 New Products & Technologies</h2></div>
        <div class="news-grid">{render_section(self.tech_news, "#0066cc", "No new product news today")}</div>
        
        <div class="section-header"><h2>🏭 Manufacturing & Investment</h2></div>
        {location_stats}
        <div class="news-grid">{render_section(self.manufacturing_news, "#10b981", "No manufacturing news today")}</div>
        
        <div class="section-header"><h2>🔬 Research Breakthroughs</h2></div>
        <div class="news-grid">{render_section(self.research_news, "#8b5cf6", "No research news today")}</div>
        
        <div class="section-header"><h2>🎪 Exhibitions & Events</h2></div>
        <div class="news-grid">{render_section(self.exhibition_news, "#f59e0b", "No exhibition news today")}</div>
        
        <div class="footer">
            <p>Southeast Asia Consumer Electronics Intelligence • Daily Briefing</p>
            <p>Data sources include: TechNews, LEDinside, Digitimes, 21st Century, People's Daily, Powder Network, Materials.cn, New Materials Online, Aibang, Xiaguang, MIDA, BOI, EDB, CAS, Fudan, GFK, JD.com, TechCrunch, The Verge, Engadget, GSMArena, KrASIA, and regional SEA media</p>
            <div class="sources">© 2026 • Generated by DeepSeek AI • For executive use only</div>
        </div>
    </div>
</body>
</html>
"""
        return html


    # -------------------------------------------------
    # AI Executive Summary
    # -------------------------------------------------

    def executive_summary(self):
        """Generate AI executive summary"""
        try:
            # Get top trends
            companies = ", ".join([c[0] for c in Counter(self.companies).most_common(3)]) or "major brands"
            locations = ", ".join([l[0] for l in Counter(self.locations).most_common(2)]) or "Southeast Asia"
            technologies = ", ".join([t[0] for t in Counter(self.technologies).most_common(2)]) or "consumer electronics"

            prompt = f"""Write a concise executive summary about consumer electronics manufacturing and innovation in Southeast Asia.

Today's Activity:
- New products/technologies: {len(self.tech_news)} articles
- Manufacturing/investment: {len(self.manufacturing_news)} articles
- Research breakthroughs: {len(self.research_news)} articles
- Exhibitions/events: {len(self.exhibition_news)} articles

Key players: {companies}
Key locations: {locations}
Key technologies: {technologies}

Write 3-4 professional sentences. Focus on strategic implications for the consumer electronics industry. Use English only."""

            response = openai.ChatCompletion.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=250,
                timeout=15
            )

            return response.choices[0].message.content

        except Exception as e:
            self.log(f"Summary generation failed: {e}", "WARNING")
            return (f"Today's report covers {len(self.tech_news)} new products, {len(self.manufacturing_news)} "
                   f"manufacturing projects, {len(self.research_news)} research breakthroughs, and "
                   f"{len(self.exhibition_news)} exhibitions in Southeast Asia's consumer electronics sector. "
                   f"Key activity in {locations} from companies including {companies}.")


    # -------------------------------------------------
    # Email Delivery
    # -------------------------------------------------

    def send_email(self, html):
        """Send email with HTML report"""
        if not RECEIVER_EMAIL:
            self.log("No email recipients configured", "WARNING")
            return False

        try:
            # Parse multiple recipients
            recipients = [e.strip() for e in RECEIVER_EMAIL.replace(';', ',').split(',') if '@' in e]
            
            if not recipients:
                self.log("No valid email recipients", "ERROR")
                return False

            # Create message
            msg = MIMEMultipart()
            msg["Subject"] = f"SEA Consumer Electronics Intelligence - {datetime.now().strftime('%Y-%m-%d')}"
            msg["From"] = SENDER_EMAIL
            msg["To"] = ", ".join(recipients)

            msg.attach(MIMEText(html, "html", "utf-8"))

            # Send via SMTP
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
            server.quit()

            self.log(f"Email sent to {len(recipients)} recipients")
            return True

        except Exception as e:
            self.log(f"Email failed: {e}", "ERROR")
            traceback.print_exc()
            return False


    # -------------------------------------------------
    # Main Execution
    # -------------------------------------------------

    def run(self):
        """Main execution pipeline"""
        self.start_time = time.time()

        self.log("=" * 60)
        self.log("SOUTHEAST ASIA CONSUMER ELECTRONICS INTELLIGENCE SYSTEM")
        self.log("=" * 60)

        # Step 1: Fetch news
        self.fetch_news()
        if not self.news:
            self.log("No news found, exiting", "ERROR")
            return

        # Step 2: Process translations
        self.process_translations()

        # Step 3: Categorize news
        self.categorize_news()

        # Step 4: Generate HTML
        html = self.generate_html()

        # Step 5: Send email
        self.send_email(html)

        # Final stats
        elapsed = time.time() - self.start_time
        self.log(f"System completed in {elapsed:.1f} seconds")
        self.log(f"Final counts: Tech={len(self.tech_news)}, Mfg={len(self.manufacturing_news)}, "
                f"Research={len(self.research_news)}, Exhib={len(self.exhibition_news)}")


# =====================================================
# MAIN ENTRY POINT
# =====================================================

if __name__ == "__main__":
    try:
        system = SEAConsumerElectronicsIntel()
        system.run()
    except KeyboardInterrupt:
        print("\nSystem interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
