#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Southeast Asia Tech Intelligence Dashboard - Director's Edition
Professional executive-level daily briefing with detailed analytics
"""

import os
import sys
import json
import hashlib
import feedparser
import requests
from datetime import datetime, timedelta
import openai
import yagmail
import tempfile
import re
import time
import traceback
import smtplib
import html as html_module  # Import html module
from collections import Counter
from typing import List, Dict, Any

# ==================== CONFIGURATION ====================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
openai.api_key = DEEPSEEK_API_KEY
openai.api_base = "https://api.deepseek.com/v1"

EMAIL_CONFIG = {
    "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", 587)),
    "sender_email": os.getenv("SENDER_EMAIL"),
    "sender_password": os.getenv("SENDER_PASSWORD"),
    "receiver_email": os.getenv("RECEIVER_EMAIL")
}

# ==================== ENHANCED RSS FEEDS ====================
RSS_FEEDS = [
    # Taiwan Tech (English-friendly)
    {"url": "https://technews.tw/feed/", "category": "tech", "region": "taiwan", "lang": "zh"},
    {"url": "https://www.digitimes.com.tw/rss/rptlist.asp", "category": "semiconductor", "region": "taiwan", "lang": "zh"},
    
    # English Tech News
    {"url": "https://feeds.bloomberg.com/markets/news.rss", "category": "finance", "region": "global", "lang": "en"},
    {"url": "https://www.reuters.com/agency/feed/?-t=2", "category": "business", "region": "global", "lang": "en"},
    {"url": "https://techcrunch.com/feed/", "category": "tech", "region": "global", "lang": "en"},
    {"url": "https://www.theverge.com/rss/index.xml", "category": "tech", "region": "global", "lang": "en"},
    {"url": "https://arstechnica.com/feed/", "category": "tech", "region": "global", "lang": "en"},
    
    # Southeast Asia English News
    {"url": "https://www.bangkokpost.com/rss/data/business.xml", "category": "business", "region": "thailand", "lang": "en"},
    {"url": "https://www.thestar.com.my/rss/business", "category": "business", "region": "malaysia", "lang": "en"},
    {"url": "https://www.straitstimes.com/news/business/rss.xml", "category": "business", "region": "singapore", "lang": "en"},
    {"url": "https://www.nst.com.my/rss/business", "category": "business", "region": "malaysia", "lang": "en"},
    {"url": "https://www.philstar.com/rss/business", "category": "business", "region": "philippines", "lang": "en"},
    
    # Industry Publications
    {"url": "https://semiengineering.com/feed/", "category": "semiconductor", "region": "global", "lang": "en"},
    {"url": "https://www.electronicproducts.com/feed/", "category": "components", "region": "global", "lang": "en"},
    {"url": "https://www.ledinside.com/news/feed", "category": "display", "region": "global", "lang": "en"},
    {"url": "https://www.displaydaily.com/feed", "category": "display", "region": "global", "lang": "en"},
]

# ==================== MAIN SCRIPT ====================
class TechIntelligenceDashboard:
    def __init__(self):
        self.news_items = []
        self.english_news = []
        self.chinese_news = []
        self.report_data = {}
        
    def log(self, msg, level="INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {msg}")
        sys.stdout.flush()
    
    def fetch_all_news(self):
        """Fetch news from all RSS feeds"""
        self.log("📡 Fetching news from 15+ sources...")
        feedparser.USER_AGENT = "Mozilla/5.0 (compatible; Executive Dashboard)"
        
        for feed in RSS_FEEDS:
            try:
                self.log(f"  Fetching: {feed['url']}")
                parsed = feedparser.parse(feed['url'])
                
                for entry in parsed.entries[:15]:  # Get more items for better coverage
                    title = entry.get('title', 'No title')
                    summary = entry.get('summary', '') or entry.get('description', '')
                    link = entry.get('link', '')
                    
                    # Extract full content if available
                    content = ''
                    if 'content' in entry and entry['content']:
                        content = entry['content'][0].get('value', '')[:1000]
                    
                    # Get publication date
                    published = entry.get('published', '')
                    if not published:
                        published = entry.get('updated', datetime.now().strftime('%Y-%m-%d'))
                    
                    # Extract source
                    source = feed['url'].split('/')[2] if '//' in feed['url'] else feed['url']
                    
                    news_item = {
                        'title': title,
                        'summary': summary[:800],
                        'content': content,
                        'link': link,
                        'source': source,
                        'published': published,
                        'category': feed['category'],
                        'region': feed['region'],
                        'lang': feed['lang']
                    }
                    
                    self.news_items.append(news_item)
                    
                    # Separate by language
                    if feed['lang'] == 'en':
                        self.english_news.append(news_item)
                    else:
                        self.chinese_news.append(news_item)
                        
            except Exception as e:
                self.log(f"  ⚠️ Error: {feed['url']} - {e}", "WARNING")
                continue
        
        self.log(f"✅ Total articles: {len(self.news_items)}")
        self.log(f"   English: {len(self.english_news)} | Chinese: {len(self.chinese_news)}")
        return self.news_items
    
    def translate_chinese_news(self):
        """Translate Chinese news to English using DeepSeek"""
        if not self.chinese_news:
            return []
        
        self.log("🔄 Translating Chinese news to English...")
        translated = []
        
        for news in self.chinese_news[:10]:  # Translate top 10 Chinese articles
            try:
                prompt = f"""Translate this Chinese news to English. Keep all technical terms and company names accurate.

Original: {news['title']} - {news['summary'][:300]}

Provide ONLY the translation, no explanations."""
                
                response = openai.ChatCompletion.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=500,
                    timeout=15
                )
                
                translation = response.choices[0].message.content
                news['title_en'] = translation.split('\n')[0]
                news['summary_en'] = translation
                translated.append(news)
                self.log(f"  ✅ Translated: {news['title'][:50]}...")
                
            except Exception as e:
                self.log(f"  ⚠️ Translation failed: {e}", "WARNING")
                continue
        
        self.log(f"✅ Translated {len(translated)} articles")
        return translated
    
    def analyze_trends(self, news_items):
        """Analyze trends and extract key insights"""
        self.log("📊 Analyzing trends...")
        
        # Extract companies mentioned
        company_pattern = r'([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?)(?:\s+(?:Corp|Inc|Ltd|Company|Group|Technology))'
        companies = []
        locations = []
        investments = []
        
        for item in news_items[:50]:
            text = f"{item['title']} {item.get('summary', '')}"
            
            # Find companies
            found_companies = re.findall(company_pattern, text)
            companies.extend(found_companies)
            
            # Find locations in Southeast Asia
            sea_locations = ['Thailand', 'Vietnam', 'Indonesia', 'Malaysia', 'Singapore', 'Philippines', 'Myanmar', 'Cambodia', 'Laos']
            for loc in sea_locations:
                if loc.lower() in text.lower():
                    locations.append(loc)
            
            # Find investment figures
            investment_pattern = r'\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:billion|million|B|M)'
            found_investments = re.findall(investment_pattern, text)
            investments.extend(found_investments)
        
        # Count frequencies
        top_companies = Counter(companies).most_common(10)
        top_locations = Counter(locations).most_common(5)
        
        return {
            'top_companies': top_companies,
            'top_locations': top_locations,
            'total_investments': len(investments),
            'estimated_value': investments[:5]  # Top 5 investment figures
        }
    
    def generate_executive_dashboard(self, news_items, trends):
        """Generate professional HTML dashboard"""
        self.log("🎨 Creating executive dashboard...")
        
        date = datetime.now().strftime('%B %d, %Y')
        
        # Separate news by category
        factory_news = []
        tech_news = []
        exhibition_news = []
        
        for n in news_items:
            text = (n['title'] + ' ' + n.get('summary', '')).lower()
            if any(k in text for k in ['factory', 'plant', 'manufacturing', 'production', 'facility']):
                factory_news.append(n)
            elif any(k in text for k in ['technology', 'innovation', 'ar', 'vr', 'ai', 'chip', 'semiconductor']):
                tech_news.append(n)
            elif any(k in text for k in ['exhibition', 'expo', 'conference', 'trade show', 'awe', 'ces']):
                exhibition_news.append(n)
        
        # Create detailed sections
        factory_section = self._create_factory_section(factory_news[:8])
        tech_section = self._create_tech_section(tech_news[:10])
        exhibition_section = self._create_exhibition_section(exhibition_news[:6])
        trends_section = self._create_trends_section(trends)
        
        # Generate executive summary
        exec_summary = self._generate_executive_summary(news_items, trends)
        
        # Build complete HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEA Tech Intelligence Dashboard - {date}</title>
    <style>
        /* Professional Executive Styling */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background: #f0f2f5;
            color: #1a1a1a;
            line-height: 1.6;
            padding: 30px 20px;
        }}
        
        .dashboard {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        /* Header Section */
        .header {{
            background: linear-gradient(135deg, #0a1929 0%, #1a2a3a 100%);
            color: white;
            padding: 40px 50px;
            border-radius: 20px 20px 0 0;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            font-weight: 300;
            margin-bottom: 10px;
        }}
        
        .header h1 strong {{
            font-weight: 600;
            color: #ffd700;
        }}
        
        .header .date {{
            color: #94a3b8;
            font-size: 1.1em;
            margin-bottom: 20px;
        }}
        
        .header .meta {{
            display: flex;
            gap: 30px;
            color: #cbd5e1;
            font-size: 0.95em;
            border-top: 1px solid #334155;
            padding-top: 20px;
            flex-wrap: wrap;
        }}
        
        /* Executive Summary Card */
        .summary-card {{
            background: white;
            border-radius: 16px;
            padding: 35px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-left: 6px solid #ffd700;
        }}
        
        .summary-card h2 {{
            color: #0a1929;
            font-size: 1.8em;
            margin-bottom: 20px;
            font-weight: 500;
        }}
        
        .summary-card p {{
            font-size: 1.2em;
            color: #334155;
            line-height: 1.8;
        }}
        
        /* KPI Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}
        
        .kpi-card {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: transform 0.3s;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }}
        
        .kpi-icon {{
            font-size: 2.5em;
            margin-bottom: 15px;
        }}
        
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
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        .kpi-trend {{
            color: #10b981;
            font-size: 0.9em;
        }}
        
        /* Section Headers */
        .section-header {{
            margin: 50px 0 30px;
            position: relative;
        }}
        
        .section-header h2 {{
            font-size: 2.2em;
            color: #0a1929;
            font-weight: 500;
            display: inline-block;
            background: #f0f2f5;
            padding-right: 20px;
        }}
        
        .section-header::after {{
            content: '';
            position: absolute;
            bottom: -10px;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, #ffd700, #e0e0e0);
            z-index: -1;
        }}
        
        /* Manufacturing Grid */
        .manufacturing-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .manufacturing-card {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid #e0e0e0;
        }}
        
        .company-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .company-logo {{
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #0a1929 0%, #1a2a3a 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffd700;
            font-size: 1.8em;
            font-weight: bold;
            margin-right: 15px;
        }}
        
        .company-info h3 {{
            font-size: 1.3em;
            margin-bottom: 5px;
            color: #0a1929;
        }}
        
        .company-meta {{
            color: #64748b;
            font-size: 0.9em;
        }}
        
        .detail-row {{
            margin: 15px 0;
            padding: 10px 0;
            border-bottom: 1px dashed #e0e0e0;
        }}
        
        .detail-label {{
            color: #64748b;
            font-size: 0.85em;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        
        .detail-value {{
            font-weight: 500;
            color: #0a1929;
        }}
        
        .investment-badge {{
            background: #10b981;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            display: inline-block;
            margin-right: 8px;
        }}
        
        /* Technology Table */
        .tech-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 30px;
        }}
        
        .tech-table th {{
            background: #0a1929;
            color: white;
            font-weight: 600;
            padding: 18px 15px;
            text-align: left;
        }}
        
        .tech-table td {{
            padding: 18px 15px;
            border-bottom: 1px solid #e0e0e0;
            vertical-align: top;
        }}
        
        .tech-table tr:hover {{
            background: #f8fafc;
        }}
        
        .tech-name {{
            font-weight: 600;
            color: #0a1929;
            font-size: 1.1em;
        }}
        
        .supplier-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .supplier-tag {{
            background: #e6f7ff;
            color: #0066cc;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
        }}
        
        /* Exhibition Cards */
        .exhibition-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .exhibition-card {{
            background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid #e0e0e0;
        }}
        
        .exhibition-name {{
            font-size: 1.4em;
            font-weight: 600;
            color: #0a1929;
            margin-bottom: 15px;
        }}
        
        .exhibition-dates {{
            color: #0066cc;
            font-weight: 500;
            margin-bottom: 10px;
        }}
        
        .exhibition-venue {{
            color: #64748b;
            margin-bottom: 20px;
        }}
        
        .exhibitor-list {{
            margin: 15px 0;
        }}
        
        .exhibitor-item {{
            background: #f1f5f9;
            color: #334155;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            display: inline-block;
            margin: 3px;
        }}
        
        /* Trends Section */
        .trends-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 25px;
            margin: 30px 0;
        }}
        
        .trend-card {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        
        .trend-card h3 {{
            color: #0a1929;
            margin-bottom: 20px;
            font-size: 1.3em;
        }}
        
        .trend-list {{
            list-style: none;
        }}
        
        .trend-item {{
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            align-items: center;
        }}
        
        .trend-rank {{
            width: 25px;
            height: 25px;
            background: #ffd700;
            color: #0a1929;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 12px;
            font-size: 0.9em;
        }}
        
        /* Footer */
        .footer {{
            background: #0a1929;
            color: white;
            padding: 40px;
            border-radius: 0 0 20px 20px;
            margin-top: 50px;
            text-align: center;
        }}
        
        .footer p {{
            color: #94a3b8;
            margin-bottom: 10px;
        }}
        
        .disclaimer {{
            font-size: 0.85em;
            color: #64748b;
            margin-top: 20px;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .trends-grid {{
                grid-template-columns: 1fr;
            }}
            .manufacturing-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <!-- Header -->
        <div class="header">
            <h1><strong>SEA TECH</strong> INTELLIGENCE DASHBOARD</h1>
            <div class="date">{date}</div>
            <div class="meta">
                <span>📊 Articles Analyzed: {len(news_items)}</span>
                <span>🌏 Sources: 15+ Publications</span>
                <span>📧 For: Executive Review</span>
                <span>⏰ {datetime.now().strftime('%H:%M:%S')}</span>
            </div>
        </div>
        
        <!-- Executive Summary -->
        <div class="summary-card">
            <h2>📋 Executive Summary</h2>
            <p>{exec_summary}</p>
        </div>
        
        <!-- KPI Dashboard -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-icon">🏭</div>
                <div class="kpi-label">Manufacturing Projects</div>
                <div class="kpi-value">{len(factory_news)}</div>
                <div class="kpi-trend">↑ {len([n for n in factory_news if 'investment' in str(n.get('summary','')).lower()])} with investments</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">💡</div>
                <div class="kpi-label">New Technologies</div>
                <div class="kpi-value">{len(tech_news)}</div>
                <div class="kpi-trend">{len([n for n in tech_news if 'AR' in n.get('title','')])} AR/VR related</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🤝</div>
                <div class="kpi-label">Suppliers Identified</div>
                <div class="kpi-value">{len(trends['top_companies'])}</div>
                <div class="kpi-trend">New this week</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🎪</div>
                <div class="kpi-label">Upcoming Events</div>
                <div class="kpi-value">{len(exhibition_news)}</div>
                <div class="kpi-trend">Next 30 days</div>
            </div>
        </div>
        
        <!-- Manufacturing Section -->
        <div class="section-header">
            <h2>🏭 Southeast Asia Manufacturing & Investment</h2>
        </div>
        {factory_section}
        
        <!-- Technology Section -->
        <div class="section-header">
            <h2>🔬 Emerging Technologies & Supplier Intelligence</h2>
        </div>
        {tech_section}
        
        <!-- Exhibitions Section -->
        <div class="section-header">
            <h2>🎪 Industry Events & Exhibitions</h2>
        </div>
        {exhibition_section}
        
        <!-- Market Trends -->
        <div class="section-header">
            <h2>📈 Market Intelligence & Trends</h2>
        </div>
        {trends_section}
        
        <!-- Footer -->
        <div class="footer">
            <p>This intelligence briefing is automatically generated for executive review.</p>
            <p>Data sources: Bloomberg, Reuters, TechCrunch, Digitimes, Bangkok Post, The Star, Straits Times, and industry publications.</p>
            <div class="disclaimer">
                © 2026 Southeast Asia Tech Intelligence • For internal use only • Generated by DeepSeek AI
            </div>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _create_factory_section(self, factory_news):
        """Create detailed manufacturing section"""
        if not factory_news:
            return '<p style="color:#666; text-align:center; padding:30px;">No manufacturing news today.</p>'
        
        html = '<div class="manufacturing-grid">'
        for item in factory_news:
            # Extract company name (simplified)
            company = item['title'].split()[0] if item['title'].split() else "Unknown"
            
            # Determine investment if mentioned
            investment = "Undisclosed"
            if 'invest' in item.get('summary', '').lower() or '$' in item.get('summary', ''):
                investment = "See details"
            
            # Safely escape HTML content
            title_safe = html_module.escape(item['title'][:80])
            summary_safe = html_module.escape(item.get('summary', '')[:200])
            
            html += f"""
            <div class="manufacturing-card">
                <div class="company-header">
                    <div class="company-logo">{company[0] if company else '?'}</div>
                    <div class="company-info">
                        <h3>{title_safe}</h3>
                        <div class="company-meta">{item['source']} • {item.get('region', 'Global').title()}</div>
                    </div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Investment</div>
                    <div class="detail-value"><span class="investment-badge">{investment}</span></div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Summary</div>
                    <div class="detail-value">{summary_safe}...</div>
                </div>
                <div style="margin-top: 15px;">
                    <a href="{item['link']}" style="color: #0066cc; text-decoration: none;">🔗 Read More →</a>
                </div>
                <div style="margin-top: 10px; color: #94a3b8; font-size: 0.85em;">
                    Published: {item['published'][:16]}
                </div>
            </div>
            """
        html += '</div>'
        return html
    
    def _create_tech_section(self, tech_news):
        """Create detailed technology section with supplier information"""
        if not tech_news:
            return '<p style="color:#666; text-align:center; padding:30px;">No technology news today.</p>'
        
        html = """<table class="tech-table">
            <thead>
                <tr>
                    <th>Technology</th>
                    <th>Application</th>
                    <th>Key Suppliers</th>
                    <th>Source</th>
                </tr>
            </thead>
            <tbody>"""
        
        for item in tech_news[:10]:
            # Extract potential suppliers from text
            suppliers = []
            supplier_pattern = r'([A-Z][a-zA-Z0-9]+(?:[\s-][A-Z][a-zA-Z0-9]+)?)\s+(?:supplies?|partners?|collaborates?|provides?)'
            found_suppliers = re.findall(supplier_pattern, item.get('summary', '') + item['title'])
            suppliers = found_suppliers[:3] if found_suppliers else ["Information pending"]
            
            supplier_tags = ''.join([f'<span class="supplier-tag">{html_module.escape(s)}</span>' for s in suppliers])
            
            # Determine application area
            application = "Consumer Electronics"
            title_lower = item['title'].lower()
            summary_lower = item.get('summary', '').lower()
            
            if 'ar' in title_lower or 'vr' in title_lower:
                application = "AR/VR Devices"
            elif 'chip' in title_lower or 'semiconductor' in title_lower:
                application = "Semiconductors"
            elif 'display' in title_lower or 'screen' in title_lower:
                application = "Display Technology"
            elif 'battery' in title_lower:
                application = "Battery Technology"
            elif 'ai' in title_lower:
                application = "Artificial Intelligence"
            
            title_safe = html_module.escape(item['title'][:60])
            
            html += f"""
            <tr>
                <td>
                    <div class="tech-name">{title_safe}</div>
                    <div style="color: #64748b; font-size: 0.9em;">{item['region'].title()}</div>
                </td>
                <td>{application}</td>
                <td><div class="supplier-tags">{supplier_tags}</div></td>
                <td><a href="{item['link']}" style="color: #0066cc;">{item['source']}</a></td>
            </tr>"""
        
        html += "</tbody></table>"
        return html
    
    def _create_exhibition_section(self, exhibition_news):
        """Create detailed exhibition section"""
        if not exhibition_news:
            return '<p style="color:#666; text-align:center; padding:30px;">No exhibition news today.</p>'
        
        html = '<div class="exhibition-grid">'
        for item in exhibition_news:
            # Extract date if available
            date_match = re.search(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}', item.get('summary', ''))
            date = date_match.group() if date_match else "TBA"
            
            title_safe = html_module.escape(item['title'][:60])
            
            html += f"""
            <div class="exhibition-card">
                <div class="exhibition-name">{title_safe}</div>
                <div class="exhibition-dates">📅 {date}</div>
                <div class="exhibition-venue">📍 {item.get('region', 'TBA').title()}</div>
                <div class="exhibitor-list">
                    <strong>Featured:</strong><br>
                    <span class="exhibitor-item">{item['source']}</span>
                </div>
                <div style="margin-top: 15px;">
                    <a href="{item['link']}" style="color: #0066cc; text-decoration: none;">🔗 Event Details →</a>
                </div>
            </div>
            """
        html += '</div>'
        return html
    
    def _create_trends_section(self, trends):
        """Create market trends section"""
        html = '<div class="trends-grid">'
        
        # Top Companies
        html += '<div class="trend-card"><h3>🏢 Top Companies</h3><ul class="trend-list">'
        for i, (company, count) in enumerate(trends['top_companies'][:5], 1):
            html += f'<li class="trend-item"><span class="trend-rank">{i}</span>{company} ({count} mentions)</li>'
        html += '</ul></div>'
        
        # Top Locations
        html += '<div class="trend-card"><h3>📍 Hotspots</h3><ul class="trend-list">'
        for i, (location, count) in enumerate(trends['top_locations'][:5], 1):
            html += f'<li class="trend-item"><span class="trend-rank">{i}</span>{location} ({count} projects)</li>'
        html += '</ul></div>'
        
        # Investment Trends
        html += f"""
        <div class="trend-card">
            <h3>💰 Investment Insights</h3>
            <ul class="trend-list">
                <li class="trend-item">Total investment mentions: {trends['total_investments']}</li>
                <li class="trend-item">Top deals: {', '.join(trends['estimated_value'][:3]) if trends['estimated_value'] else 'N/A'}</li>
                <li class="trend-item">Active sectors: Electronics, Semiconductors, EV</li>
            </ul>
        </div>
        """
        
        html += '</div>'
        return html
    
    def _generate_executive_summary(self, news_items, trends):
        """Generate executive summary using AI"""
        try:
            location_text = ', '.join([loc[0] for loc in trends['top_locations'][:3]]) if trends['top_locations'] else 'Various'
            
            prompt = f"""Write a brief executive summary (3-4 sentences) of today's Southeast Asia tech and manufacturing news.
Focus on: investments, new factories, major technology announcements, and strategic trends.

Key stats:
- Total articles: {len(news_items)}
- Top locations: {location_text}
- Investment mentions: {trends['total_investments']}

Make it professional and impactful for a company director."""
            
            response = openai.ChatCompletion.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
                timeout=10
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.log(f"⚠️ Summary generation failed: {e}", "WARNING")
            location_text = trends['top_locations'][0][0] if trends['top_locations'] else 'the region'
            return f"Today's intelligence covers {len(news_items)} articles with significant activity in {location_text}. Key developments include manufacturing expansions and technology innovations across Southeast Asia."
    
    def parse_recipients(self, recipients_string):
        """Parse email recipients"""
        if not recipients_string:
            return []
        
        cleaned = recipients_string.replace('*', '').replace('\n', ',').replace('\r', ',').replace(';', ',')
        recipients = [email.strip() for email in cleaned.split(',') if email.strip() and '@' in email]
        return recipients
    
    def send_email(self, subject, html_content):
    """Send email with professional dashboard using direct SMTP"""
    self.log("\n📧 Sending executive briefing...")
    
    try:
        recipients = self.parse_recipients(EMAIL_CONFIG["receiver_email"])
        if not recipients:
            self.log("❌ No valid recipients", "ERROR")
            return False
        
        self.log(f"   To: {recipients}")
        
        # Use direct SMTP instead of yagmail to avoid SSL issues
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = ', '.join(recipients)
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Connect to Gmail SMTP with proper SSL
        self.log(f"   Connecting to {EMAIL_CONFIG['smtp_host']}:{EMAIL_CONFIG['smtp_port']}...")
        
        # Try different connection methods
        try:
            # Method 1: Standard TLS
            server = smtplib.SMTP(EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"], timeout=30)
            server.starttls()
            server.ehlo()
            self.log("   ✅ Connected with STARTTLS")
        except Exception as e:
            self.log(f"   ⚠️ Method 1 failed: {e}", "WARNING")
            try:
                # Method 2: Direct SSL
                server = smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_host"], 465, timeout=30)
                self.log("   ✅ Connected with SSL on port 465")
            except Exception as e:
                self.log(f"   ⚠️ Method 2 failed: {e}", "WARNING")
                # Method 3: No encryption (not recommended but as fallback)
                server = smtplib.SMTP(EMAIL_CONFIG["smtp_host"], 25, timeout=30)
                self.log("   ⚠️ Connected without encryption", "WARNING")
        
        # Login
        self.log("   Logging in...")
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        self.log("   ✅ Login successful")
        
        # Send email
        self.log("   Sending email...")
        server.send_message(msg)
        self.log("   ✅ Message sent")
        
        # Close connection
        server.quit()
        
        self.log("✅ Executive briefing sent successfully!")
        return True
        
    except Exception as e:
        self.log(f"❌ Email failed: {e}", "ERROR")
        traceback.print_exc()
        return False
        
    
    def run(self):
        """Main execution flow"""
        self.log("\n" + "="*70)
        self.log("🚀 SOUTHEAST ASIA TECH INTELLIGENCE DASHBOARD")
        self.log("="*70)
        
        start_time = time.time()
        
        # Step 1: Fetch news
        news_items = self.fetch_all_news()
        if not news_items:
            self.log("❌ No news fetched", "ERROR")
            return
        
        # Step 2: Translate Chinese news
        translated = self.translate_chinese_news()
        all_news = news_items + translated
        
        # Step 3: Analyze trends
        trends = self.analyze_trends(all_news)
        
        # Step 4: Generate dashboard
        html_content = self.generate_executive_dashboard(all_news, trends)
        
        # Step 5: Send email
        subject = f"📊 SEA Tech Intelligence Dashboard - {datetime.now().strftime('%Y-%m-%d')}"
        self.send_email(subject, html_content)
        
        elapsed = time.time() - start_time
        self.log("\n" + "="*70)
        self.log(f"✅ DASHBOARD COMPLETE in {elapsed:.1f} seconds")
        self.log("="*70)

# ==================== MAIN ====================
if __name__ == "__main__":
    dashboard = TechIntelligenceDashboard()
    dashboard.run()
