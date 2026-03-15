#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Southeast Asia Consumer Electronics Intelligence System
Production Version

Features
- RSS aggregation (50+ sources including Chinese tech media, government sites)
- strict consumer electronics filtering
- deduplication
- AI translation
- AI executive summary
- industry trend extraction
- HTML executive dashboard
- email delivery

Author: Production Edition
"""

import os
import sys
import re
import time
import hashlib
import traceback
import feedparser
import openai
import smtplib
import html as html_module

from datetime import datetime
from collections import Counter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# =====================================================
# CONFIGURATION
# =====================================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

openai.api_key = DEEPSEEK_API_KEY
openai.api_base = "https://api.deepseek.com/v1"

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")


# =====================================================
# KEYWORDS (Expanded)
# =====================================================

SEA_LOCATIONS = [
    # Countries
    "vietnam", "thailand", "indonesia", "malaysia", "singapore",
    "philippines", "myanmar", "cambodia", "laos", "brunei",
    "asean", "southeast asia", "东南亚",
    
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

HOME_APPLIANCES_KEYWORDS = [
    # Refrigeration
    "refrigerator", "fridge", "freezer", "冷柜", "冰箱",
    
    # Laundry
    "washing machine", "washer", "dryer", "洗衣机",
    
    # HVAC
    "air conditioner", "ac", "空调", "hvac",
    
    # Cleaning
    "vacuum", "robot vacuum", "扫地机器人", "吸尘器",
    
    # Kitchen
    "microwave", "oven", "dishwasher", "rice cooker", "电饭煲",
    "air fryer", "空气炸锅", "coffee maker", "toaster",
    
    # TV/Display
    "tv", "television", "电视", "display", "screen"
]

MOBILE_ELECTRONICS_KEYWORDS = [
    # Phones
    "smartphone", "phone", "mobile", "手机",
    "samsung", "galaxy", "apple", "iphone", "xiaomi", "oppo", "vivo", "realme",
    "foldable", "折叠屏",
    
    # Wearables
    "wearable", "smartwatch", "智能手表", "fitness tracker", "手环",
    
    # AR/VR
    "ar", "vr", "ai glasses", "smart glasses", "智能眼镜", "ar glasses", "vr headset",
    "rokid", "htc", "vive", "meta quest", "pico",
    
    # Audio
    "earbuds", "headphones", "tws", "耳机",
    
    # Tablets/Laptops
    "tablet", "ipad", "laptop", "notebook"
]

MANUFACTURING_KEYWORDS = [
    "factory", "plant", "manufacturing", "production", "assembly", "生产线", "量产",
    "facility", "新建工厂", "投产", "开工", "奠基", "investment", "invest",
    "supplier", "供应链", "vendor", "供应商", "localization", "本地化",
    "expansion", "扩建", "capacity", "产能",
    "出海", "going global", "全球化", "globalization",
    "东南亚市场", "vietnam factory", "thailand investment", "indonesia manufacturing",
    "海外扩张", "overseas expansion"
]

RESEARCH_KEYWORDS = [
    "research", "innovation", "prototype", "breakthrough", "研究", "突破", "创新",
    "flexible electronics", "柔性电子", "wearable tech", "可穿戴技术",
    "thermoelectric", "热电", "fiber chip", "纤维芯片",
    "brain-computer", "脑机接口", "新材料", "new material",
    "powder", "粉体", "nano", "纳米", "coating", "涂层",
    "thin film", "薄膜", "capacitor", "电容器"
]

EXHIBITION_KEYWORDS = [
    "expo", "exhibition", "trade show", "conference", "展", 
    "ces", "ifa", "mwc", "awe", "electronica"
]

NON_CONSUMER_KEYWORDS = [
    "electric vehicle", "ev battery", "solar farm", "steel plant", "mining",
    "oil and gas", "chemical plant", "pharmaceutical", "biotech"
]

COMPANIES = [
    "Samsung", "Apple", "Xiaomi", "Oppo", "Vivo", "Realme",
    "Haier", "Midea", "Hisense", "Gree", "TCL",
    "Sony", "Panasonic", "LG", "Sharp", "Toshiba",
    "Foxconn", "Pegatron", "Luxshare", "Goertek", "BOE",
    "Rokid", "HTC"
]

TECHNOLOGY = [
    "ai", "ar", "vr", "wearable", "foldable", "smart home",
    "5g", "iot", "microled", "oled", "flexible display"
]


# =====================================================
# RSS SOURCES (Expanded - 50+ sources)
# =====================================================

RSS_FEEDS = [
    # ===== Chinese Tech Media =====
    {"url": "https://technews.tw/feed/", "lang": "zh"},
    {"url": "https://finance.technews.tw/feed/", "lang": "zh"},
    {"url": "https://www.ledinside.cn/rss.xml", "lang": "zh"},
    {"url": "https://www.digitimes.com.tw/rss/rptlist.asp", "lang": "zh"},
    {"url": "https://www.21jingji.com/rss/", "lang": "zh"},
    {"url": "http://world.people.com.cn/rss/index.xml", "lang": "zh"},
    {"url": "https://ep.ycwb.com/rss/", "lang": "zh"},
    {"url": "https://news.cnyes.com/rss", "lang": "zh"},
    
    # ===== Materials & Industry Sites =====
    {"url": "http://www.cnpowder.com.cn/rss/", "lang": "zh"},
    {"url": "http://www.materials.cn/rss/", "lang": "zh"},
    {"url": "https://www.xincailiao.com/rss/", "lang": "zh"},
    {"url": "https://www.aibang.com/feed/", "lang": "zh"},
    {"url": "https://www.aibang.com/news/feed/", "lang": "zh"},
    
    # ===== Chinese Overseas/Industry =====
    {"url": "https://xiaguangshe.com/feed/", "lang": "zh"},
    {"url": "https://www.cena.com.cn/rss.xml", "lang": "zh"},
    {"url": "https://www.chinaoverseasemi.com/feed", "lang": "en"},
    
    # ===== Government & Investment Sites =====
    {"url": "https://www.mida.gov.my/press-releases/feed/", "lang": "en"},
    {"url": "https://www.mida.gov.my/news/feed/", "lang": "en"},
    {"url": "https://www.matrade.gov.my/en/media/press-releases/feed", "lang": "en"},
    {"url": "https://www.crest.my/feed/", "lang": "en"},
    {"url": "https://www.boi.go.th/upload/rss/boi_news_en.xml", "lang": "en"},
    {"url": "https://www.edb.gov.sg/en/news-and-events/feed.html", "lang": "en"},
    
    # ===== Chinese Research Institutions =====
    {"url": "https://english.cas.cn/news/rss/", "lang": "en"},
    {"url": "http://www.cas.cn/rss/", "lang": "zh"},
    {"url": "https://news.fudan.edu.cn/rss.xml", "lang": "zh"},
    {"url": "https://en.ncsti.gov.cn/Latest/rss/", "lang": "en"},
    
    # ===== Market Research =====
    {"url": "https://www.gfk.com/insights/rss", "lang": "en"},
    {"url": "https://ir.jd.com/rss", "lang": "en"},
    {"url": "https://jingdaily.com/category/tech/feed/", "lang": "en"},
    
    # ===== Chinese Tech Media (English) =====
    {"url": "https://www.chinadaily.com.cn/rss/business_rss.xml", "lang": "en"},
    {"url": "https://www.chinadailyhk.com/rss", "lang": "en"},
    {"url": "https://36kr.com/feed/english", "lang": "en"},
    {"url": "https://www.kr-asia.com/feed", "lang": "en"},
    
    # ===== Manufacturer Blogs =====
    {"url": "https://www.rokid.com/blog/feed/", "lang": "en"},
    {"url": "https://www.colmo.com.cn/news/feed/", "lang": "zh"},
    
    # ===== Global Tech Media =====
    {"url": "https://techcrunch.com/feed/", "lang": "en"},
    {"url": "https://www.theverge.com/rss/index.xml", "lang": "en"},
    {"url": "https://arstechnica.com/feed/", "lang": "en"},
    {"url": "https://www.engadget.com/rss.xml", "lang": "en"},
    {"url": "https://www.gsmarena.com/rss-news-reviews.php", "lang": "en"},
    {"url": "https://www.androidauthority.com/feed/", "lang": "en"},
    
    # ===== Southeast Asia News =====
    {"url": "https://www.vietnam-briefing.com/news/feed/", "lang": "en"},
    {"url": "https://e.vnexpress.net/rss/business.rss", "lang": "en"},
    {"url": "https://www.bangkokpost.com/rss/data/business.xml", "lang": "en"},
    {"url": "https://thailand-briefing.com/news/feed/", "lang": "en"},
    {"url": "https://www.thestar.com.my/rss/business", "lang": "en"},
    {"url": "https://www.nst.com.my/rss/business", "lang": "en"},
    {"url": "https://www.straitstimes.com/news/business/rss.xml", "lang": "en"},
    {"url": "https://sbr.com.sg/rss.xml", "lang": "en"},
    {"url": "https://indonesia-briefing.com/news/feed/", "lang": "en"},
    {"url": "https://www.thejakartapost.com/rss/business.xml", "lang": "en"},
    {"url": "https://www.philstar.com/rss/business", "lang": "en"},
    
    # ===== Industry Publications =====
    {"url": "https://semiengineering.com/feed/", "lang": "en"},
    {"url": "https://www.electronicproducts.com/feed/", "lang": "en"},
    {"url": "https://www.displaydaily.com/feed", "lang": "en"},
]


# =====================================================
# SYSTEM CLASS
# =====================================================

class SEAConsumerElectronicsIntel:

    def __init__(self):

        self.news = []
        self.news_enriched = []  # 包含翻译后的新闻

        self.tech_news = []
        self.manufacturing_news = []
        self.research_news = []
        self.exhibition_news = []

        self.seen_hash = set()

        self.companies = []
        self.locations = []
        self.technologies = []


    # -------------------------------------------------
    # logging
    # -------------------------------------------------

    def log(self, msg):

        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        sys.stdout.flush()


    # -------------------------------------------------
    # normalize news
    # -------------------------------------------------

    def normalize_news(self, entry, source_url, lang):

        title = entry.get("title", "").strip()
        summary = entry.get("summary") or entry.get("description") or ""
        link = entry.get("link", "").strip()

        if not title or not link:
            return None

        # 清理HTML标签
        summary = re.sub("<.*?>", "", summary)
        summary = summary.replace("\n", " ").strip()

        # 提取来源域名作为source name
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


    # -------------------------------------------------
    # relevance filter
    # -------------------------------------------------

    def is_relevant_news(self, title, summary):

        text = (title + " " + summary).lower()

        # 必须包含东南亚地点
        if not any(loc in text for loc in SEA_LOCATIONS):
            return False

        # 排除非消费电子类
        if any(k in text for k in NON_CONSUMER_KEYWORDS):
            return False

        # 必须是消费电子产品相关
        product = (
            any(k in text for k in HOME_APPLIANCES_KEYWORDS) or
            any(k in text for k in MOBILE_ELECTRONICS_KEYWORDS)
        )

        return product


    # -------------------------------------------------
    # deduplication
    # -------------------------------------------------

    def is_duplicate(self, title, link):

        key = hashlib.md5((title + link).encode()).hexdigest()

        if key in self.seen_hash:
            return True

        self.seen_hash.add(key)
        return False


    # -------------------------------------------------
    # quality score
    # -------------------------------------------------

    def quality_score(self, title, summary):

        score = 0
        text = (title + summary).lower()

        if len(summary) > 120:
            score += 1

        if any(loc in text for loc in SEA_LOCATIONS):
            score += 1

        if any(k in text for k in MOBILE_ELECTRONICS_KEYWORDS + HOME_APPLIANCES_KEYWORDS):
            score += 1

        if any(k in text for k in COMPANIES):
            score += 1

        return score


    # -------------------------------------------------
    # translate Chinese to English
    # -------------------------------------------------

    def translate_news(self, item):

        try:
            prompt = f"""Translate this Chinese news to English accurately.

Original Chinese:
Title: {item['title']}
Summary: {item['summary'][:500]}

Requirements:
- Keep company names accurate (海尔→Haier, 美的→Midea, 京东方→BOE)
- Preserve technical terms, investment figures, and locations
- Provide concise translation (2-3 sentences)

Provide:
Title: [translated title]
Summary: [translated summary]"""

            response = openai.ChatCompletion.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
                timeout=20
            )

            translation = response.choices[0].message.content
            lines = translation.split('\n', 1)
            
            title_en = lines[0].replace('Title:', '').strip() if lines else item['title']
            summary_en = lines[1].replace('Summary:', '').strip() if len(lines) > 1 else item['summary']

            return {
                **item,
                'title_en': title_en,
                'summary_en': summary_en
            }

        except Exception as e:
            self.log(f"Translation failed: {e}")
            return {
                **item,
                'title_en': f"[Translation] {item['title']}",
                'summary_en': item['summary']
            }


    # -------------------------------------------------
    # fetch all RSS feeds
    # -------------------------------------------------

    def fetch_news(self):

        self.log(f"Fetching RSS feeds ({len(RSS_FEEDS)} sources)")

        for feed in RSS_FEEDS:

            try:
                self.log(f"  Fetching: {feed['url']}")
                parsed = feedparser.parse(feed['url'])

                for entry in parsed.entries[:15]:

                    item = self.normalize_news(entry, feed['url'], feed.get('lang', 'en'))

                    if not item:
                        continue

                    if self.is_duplicate(item['title'], item['link']):
                        continue

                    if not self.is_relevant_news(item['title'], item['summary']):
                        continue

                    if self.quality_score(item['title'], item['summary']) < 2:
                        continue

                    self.news.append(item)

            except Exception as e:
                self.log(f"  RSS error: {feed['url']} - {e}")
                continue

        self.log(f"Total relevant news: {len(self.news)}")

        # 翻译中文新闻
        chinese_news = [n for n in self.news if n.get('lang') == 'zh']
        self.log(f"Translating {len(chinese_news)} Chinese articles...")

        for cn in chinese_news:
            translated = self.translate_news(cn)
            self.news_enriched.append(translated)

        # 英文新闻直接使用
        english_news = [n for n in self.news if n.get('lang') == 'en']
        self.news_enriched.extend(english_news)

        self.log(f"Total enriched news: {len(self.news_enriched)}")


    # -------------------------------------------------
    # categorize news
    # -------------------------------------------------

    def categorize(self):

        for item in self.news_enriched:

            # 使用英文标题和摘要进行分析
            title = item.get('title_en', item['title'])
            summary = item.get('summary_en', item['summary'])
            text = (title + " " + summary).lower()

            # 新技术与产品 - 必须包含家电或可移动数码关键词
            if any(k in text for k in MOBILE_ELECTRONICS_KEYWORDS + HOME_APPLIANCES_KEYWORDS):
                if item not in self.tech_news:
                    self.tech_news.append(item)

            # 制造与投资
            if any(k in text for k in MANUFACTURING_KEYWORDS):
                if item not in self.manufacturing_news:
                    self.manufacturing_news.append(item)

            # 研究突破
            if any(k in text for k in RESEARCH_KEYWORDS):
                if item not in self.research_news:
                    self.research_news.append(item)

            # 展会活动
            if any(k in text for k in EXHIBITION_KEYWORDS):
                if item not in self.exhibition_news:
                    self.exhibition_news.append(item)

            # 提取趋势数据
            self.extract_trends(text)


    # -------------------------------------------------
    # extract industry trends
    # -------------------------------------------------

    def extract_trends(self, text):

        for c in COMPANIES:
            if c.lower() in text:
                self.companies.append(c)

        for l in SEA_LOCATIONS:
            if l in text:
                self.locations.append(l.title())

        for t in TECHNOLOGY:
            if t in text:
                self.technologies.append(t.upper() if t in ['ai','ar','vr','5g'] else t.title())


    # -------------------------------------------------
    # get source logo/icon
    # -------------------------------------------------

    def get_source_logo(self, source):

        source_lower = source.lower()
        
        logos = {
            'technews': '📱 TechNews', 'ledinside': '💡 LEDinside', 'digitimes': '📰 Digitimes',
            '21jingji': '📊 21经济', 'people': '🏛️ 人民网', 'ycwb': '📰 羊城晚报',
            'cnyes': '📈 鉅亨網', 'cnpowder': '⚙️ 粉体网',
            'materials': '🔬 寻材问料', 'xincailiao': '🧪 新材料在线', 'aibang': '🧪 艾邦',
            'xiaguangshe': '🌏 霞光社', 'cena': '📡 电子信息网',
            'mida': '🇲🇾 MIDA', 'matrade': '🇲🇾 MATRADE', 'crest': '🇲🇾 CREST',
            'boi': '🇹🇭 BOI', 'edb': '🇸🇬 EDB',
            'cas': '🔬 中科院', 'fudan': '🎓 复旦大学', 'gfk': '📊 GfK',
            'jd': '🛒 京东', 'chinadaily': '🇨🇳 China Daily',
            'rokid': '👓 Rokid', 'colmo': '🏠 COLMO', '36kr': '📱 36Kr',
            'kr-asia': '🌏 KrASIA', 'techcrunch': '📱 TechCrunch',
            'theverge': '📱 The Verge', 'engadget': '📱 Engadget',
            'gsmarena': '📱 GSMArena', 'bangkokpost': '🇹🇭 Bangkok Post',
            'thestar': '🇲🇾 The Star', 'straitstimes': '🇸🇬 Straits Times',
            'vietnam-briefing': '🇻🇳 Vietnam Briefing', 'vnexpress': '🇻🇳 VNExpress',
            'semiengineering': '🔧 SemiEngineering'
        }
        
        for key, logo in logos.items():
            if key in source_lower:
                return logo
        
        return f"📰 {source[:15]}"


    # -------------------------------------------------
    # create html news card
    # -------------------------------------------------

    def news_card(self, item, color="#0066cc"):

        title = html_module.escape(item.get('title_en', item['title'])[:100])
        summary = html_module.escape(item.get('summary_en', item['summary'])[:200])
        source_logo = self.get_source_logo(item['source'])
        link = item['link']

        return f"""
<div style="margin-bottom:20px; padding:20px; background:white; border-radius:10px; box-shadow:0 2px 4px rgba(0,0,0,0.05); border-left:4px solid {color};">
    <div style="display:flex; align-items:center; margin-bottom:10px;">
        <span style="background:{color}; color:white; padding:5px 10px; border-radius:20px; font-size:0.85em; font-weight:bold; margin-right:10px;">{source_logo}</span>
        <span style="color:#666; font-size:0.85em;">{item.get('published', '')[:10]}</span>
    </div>
    <h4 style="font-size:1.2em; margin-bottom:10px; color:#0a1929;">{title}</h4>
    <p style="color:#334155; margin-bottom:15px; line-height:1.5;">{summary}...</p>
    <a href="{link}" style="color:{color}; text-decoration:none; font-weight:500;" target="_blank">🔗 阅读原文 →</a>
</div>
"""


    # -------------------------------------------------
    # AI executive summary
    # -------------------------------------------------

    def executive_summary(self):

        try:
            companies = ", ".join([c[0] for c in Counter(self.companies).most_common(3)])
            locations = ", ".join([l[0] for l in Counter(self.locations).most_common(3)])
            technologies = ", ".join([t[0] for t in Counter(self.technologies).most_common(2)])

            prompt = f"""Write a concise executive insight about Southeast Asia consumer electronics.

Today's activity:
- New products/tech: {len(self.tech_news)} articles
- Manufacturing/investment: {len(self.manufacturing_news)} articles
- Research breakthroughs: {len(self.research_news)} articles
- Exhibitions/events: {len(self.exhibition_news)} articles

Key companies: {companies}
Key locations: {locations}
Key technologies: {technologies}

Write 3-4 professional sentences suitable for a company director."""

            r = openai.ChatCompletion.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200,
                timeout=10
            )

            return r.choices[0].message.content

        except Exception as e:
            self.log(f"Summary generation failed: {e}")
            return f"Today's report covers {len(self.tech_news)} new products, {len(self.manufacturing_news)} manufacturing projects, {len(self.research_news)} research breakthroughs, and {len(self.exhibition_news)} exhibitions in Southeast Asia's consumer electronics sector."


    # -------------------------------------------------
    # generate html dashboard
    # -------------------------------------------------

    def generate_html(self):

        summary = self.executive_summary()

        def render_section(items, color):
            html = ""
            for i in items:
                html += self.news_card(i, color)
            if not html:
                html = '<p style="color:#666; text-align:center; padding:20px;">暂无新闻</p>'
            return html

        # 制造热点统计
        location_stats = ""
        if self.locations:
            location_counts = Counter(self.locations).most_common(5)
            location_stats = '<div style="background:#f8f9fa; padding:20px; border-radius:10px; margin-bottom:25px;">'
            location_stats += '<h4 style="margin-bottom:15px; color:#0a1929;">📍 制造热点分布</h4>'
            location_stats += '<div style="display:flex; flex-wrap:wrap; gap:15px;">'
            
            for loc, count in location_counts:
                location_stats += f"""
                <div style="flex:1; min-width:120px; background:white; padding:12px; border-radius:8px;">
                    <div style="font-weight:bold; color:#0066cc;">{loc}</div>
                    <div style="font-size:1.5em; font-weight:bold;">{count}</div>
                    <div style="font-size:0.85em; color:#666;">mentions</div>
                </div>
                """
            location_stats += '</div></div>'

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Southeast Asia Consumer Electronics Intelligence</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',Arial,sans-serif; background:#f0f2f5; padding:30px 20px; }}
        .dashboard {{ max-width:1400px; margin:0 auto; }}
        .header {{ background:linear-gradient(135deg,#0a1929 0%,#1a2a3a 100%); color:white; padding:40px 50px; border-radius:20px 20px 0 0; margin-bottom:30px; }}
        .header h1 {{ font-size:2.5em; font-weight:300; }}
        .header h1 strong {{ font-weight:600; color:#ffd700; }}
        .header .date {{ color:#94a3b8; font-size:1.1em; margin:10px 0 20px; }}
        .header .meta {{ display:flex; gap:30px; color:#cbd5e1; border-top:1px solid #334155; padding-top:20px; flex-wrap:wrap; }}
        
        .summary-card {{ background:white; border-radius:16px; padding:35px; margin-bottom:30px; border-left:6px solid #ffd700; box-shadow:0 4px 6px rgba(0,0,0,0.05); }}
        .summary-card h2 {{ color:#0a1929; font-size:1.8em; margin-bottom:20px; }}
        .summary-card p {{ font-size:1.2em; color:#334155; line-height:1.8; }}
        
        .kpi-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:25px; margin-bottom:40px; }}
        .kpi-card {{ background:white; border-radius:16px; padding:25px; box-shadow:0 4px 6px rgba(0,0,0,0.05); }}
        .kpi-icon {{ font-size:2.5em; margin-bottom:15px; }}
        .kpi-value {{ font-size:2.8em; font-weight:600; color:#0a1929; line-height:1.2; }}
        .kpi-label {{ color:#64748b; font-size:1em; text-transform:uppercase; margin-bottom:10px; }}
        
        .section-header {{ margin:50px 0 30px; }}
        .section-header h2 {{ font-size:2.2em; color:#0a1929; font-weight:500; display:inline-block; background:#f0f2f5; padding-right:20px; }}
        
        .news-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(450px,1fr)); gap:25px; }}
        
        .footer {{ background:#0a1929; color:white; padding:40px; border-radius:0 0 20px 20px; margin-top:50px; text-align:center; }}
        .footer p {{ color:#94a3b8; margin-bottom:10px; }}
        
        @media (max-width:768px) {{ .kpi-grid {{ grid-template-columns:1fr; }} .news-grid {{ grid-template-columns:1fr; }} }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1><strong>Southeast Asia</strong> Consumer Electronics Intelligence</h1>
            <div class="date">{datetime.now().strftime('%B %d, %Y')}</div>
            <div class="meta">
                <span>📊 Total Articles: {len(self.news_enriched)}</span>
                <span>🌏 Focus: Consumer Electronics in SEA</span>
                <span>⏰ {datetime.now().strftime('%H:%M:%S')}</span>
            </div>
        </div>
        
        <div class="summary-card">
            <h2>📋 Executive Summary</h2>
            <p>{summary}</p>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi-card"><div class="kpi-icon">📱</div><div class="kpi-label">New Products</div><div class="kpi-value">{len(self.tech_news)}</div></div>
            <div class="kpi-card"><div class="kpi-icon">🏭</div><div class="kpi-label">Manufacturing</div><div class="kpi-value">{len(self.manufacturing_news)}</div></div>
            <div class="kpi-card"><div class="kpi-icon">🔬</div><div class="kpi-label">Research</div><div class="kpi-value">{len(self.research_news)}</div></div>
            <div class="kpi-card"><div class="kpi-icon">🎪</div><div class="kpi-label">Exhibitions</div><div class="kpi-value">{len(self.exhibition_news)}</div></div>
        </div>
        
        <div class="section-header"><h2>📱 New Products & Technologies</h2></div>
        <div class="news-grid">{render_section(self.tech_news, "#0066cc")}</div>
        
        <div class="section-header"><h2>🏭 Manufacturing & Investment</h2></div>
        {location_stats}
        <div class="news-grid">{render_section(self.manufacturing_news, "#10b981")}</div>
        
        <div class="section-header"><h2>🔬 Research Breakthroughs</h2></div>
        <div class="news-grid">{render_section(self.research_news, "#8b5cf6")}</div>
        
        <div class="section-header"><h2>🎪 Exhibitions & Events</h2></div>
        <div class="news-grid">{render_section(self.exhibition_news, "#ff9800")}</div>
        
        <div class="footer">
            <p>Southeast Asia Consumer Electronics Intelligence • 50+ Sources including Chinese Tech Media, Government Sites</p>
            <p>Sources: TechNews, LEDinside, Digitimes, 21经济, 人民网, 中国粉体网, 寻材问料, 新材料在线, 艾邦, 霞光社, MIDA, BOI, EDB, 中科院</p>
        </div>
    </div>
</body>
</html>
"""

        return html


    # -------------------------------------------------
    # send email
    # -------------------------------------------------

    def send_email(self, html):

        if not RECEIVER_EMAIL:
            self.log("No email configured")
            return False

        try:
            # 解析多个收件人
            recipients = [e.strip() for e in RECEIVER_EMAIL.replace(';',',').split(',') if '@' in e]

            msg = MIMEMultipart()
            msg["Subject"] = f"SEA Consumer Electronics Intelligence - {datetime.now().strftime('%Y-%m-%d')}"
            msg["From"] = SENDER_EMAIL
            msg["To"] = ", ".join(recipients)

            msg.attach(MIMEText(html, "html", "utf-8"))

            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
            server.quit()

            self.log(f"Email sent to {len(recipients)} recipients")
            return True

        except Exception as e:
            self.log(f"Email failed: {e}")
            traceback.print_exc()
            return False


    # -------------------------------------------------
    # run system
    # -------------------------------------------------

    def run(self):

        start = time.time()

        self.log("=" * 60)
        self.log("Southeast Asia Consumer Electronics Intelligence System")
        self.log("=" * 60)

        # 1. 获取新闻
        self.fetch_news()

        # 2. 分类
        self.categorize()

        # 3. 生成HTML
        html = self.generate_html()

        # 4. 发送邮件
        self.send_email(html)

        elapsed = time.time() - start
        self.log(f"System finished in {elapsed:.1f} seconds")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    system = SEAConsumerElectronicsIntel()
    system.run()
