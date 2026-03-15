#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东南亚消费电子智能简报系统
每日高管简报，覆盖：

1. 新技术与产品：家电类、可移动电子数码产品类（手机、可穿戴、AR/VR/AI眼镜、扫地机器人等）
2. 制造与投资：消费电子在东南亚的工厂建设（含政府网站、出海报道）
3. 研究突破：材料科学、前沿技术、技术突破
4. 行业展会：展览会、贸易展、会议
5. 市场情报：消费者行为、供应商情报、趋势分析
"""

import os
import sys
import json
import hashlib
import feedparser
import requests
from datetime import datetime, timedelta
import openai
import tempfile
import re
import time
import traceback
import smtplib
import html as html_module
from collections import Counter
from typing import List, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ==================== 配置 ====================
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

# ==================== 完整RSS源列表 ====================
RSS_FEEDS = [
    # ===== 中文科技媒体（全面覆盖）=====
    {"url": "https://technews.tw/feed/", "category": "tech", "region": "taiwan", "lang": "zh"},
    {"url": "https://finance.technews.tw/feed/", "category": "finance", "region": "taiwan", "lang": "zh"},
    {"url": "https://www.ledinside.cn/rss.xml", "category": "display", "region": "china", "lang": "zh"},
    {"url": "https://www.ledinside.com/news/feed", "category": "display", "region": "global", "lang": "en"},
    {"url": "https://www.digitimes.com.tw/rss/rptlist.asp", "category": "semiconductor", "region": "taiwan", "lang": "zh"},
    {"url": "https://www.21jingji.com/rss/", "category": "business", "region": "china", "lang": "zh"},
    {"url": "http://world.people.com.cn/rss/index.xml", "category": "business", "region": "china", "lang": "zh"},
    {"url": "https://ep.ycwb.com/rss/", "category": "business", "region": "china", "lang": "zh"},
    {"url": "https://epaper.guanhai.com.cn/rss/", "category": "business", "region": "china", "lang": "zh"},
    {"url": "https://news.cnyes.com/rss", "category": "tech", "region": "taiwan", "lang": "zh"},
    
    # ===== 中文科技资源（新材料、粉体等）=====
    {"url": "http://www.cnpowder.com.cn/rss/", "category": "materials", "region": "china", "lang": "zh"},
    {"url": "http://www.materials.cn/rss/", "category": "materials", "region": "china", "lang": "zh"},
    {"url": "https://www.xincailiao.com/rss/", "category": "materials", "region": "china", "lang": "zh"},
    {"url": "https://www.aibang.com/feed/", "category": "materials", "region": "china", "lang": "zh"},
    {"url": "https://www.aibang.com/news/feed/", "category": "industry", "region": "china", "lang": "zh"},
    {"url": "https://www.aibang.com/category/manufacturing/feed/", "category": "manufacturing", "region": "china", "lang": "zh"},
    {"url": "https://www.aibang.com/category/materials/feed/", "category": "materials", "region": "china", "lang": "zh"},
    
    # ===== 出海报道网站 =====
    {"url": "https://xiaguangshe.com/feed/", "category": "overseas", "region": "china", "lang": "zh"},
    {"url": "https://xiaguangshe.com/en/feed/", "category": "overseas", "region": "china", "lang": "en"},
    {"url": "https://www.cena.com.cn/rss.xml", "category": "industry", "region": "china", "lang": "zh"},
    {"url": "https://www.cena.com.cn/node/feed", "category": "industry", "region": "china", "lang": "zh"},
    {"url": "https://www.chinaoverseasemi.com/feed", "category": "semiconductor", "region": "china", "lang": "en"},
    
    # ===== 政府与投资机构网站 =====
    {"url": "https://www.mida.gov.my/press-releases/feed/", "category": "investment", "region": "malaysia", "lang": "en"},
    {"url": "https://www.mida.gov.my/news/feed/", "category": "investment", "region": "malaysia", "lang": "en"},
    {"url": "https://www.matrade.gov.my/en/media/press-releases/feed", "category": "trade", "region": "malaysia", "lang": "en"},
    {"url": "https://www.crest.my/feed/", "category": "electronics", "region": "malaysia", "lang": "en"},
    {"url": "https://www.boi.go.th/upload/rss/boi_news_en.xml", "category": "investment", "region": "thailand", "lang": "en"},
    {"url": "https://www.edb.gov.sg/en/news-and-events/feed.html", "category": "investment", "region": "singapore", "lang": "en"},
    
    # ===== 其他中文科技资源 =====
    {"url": "https://www.chinadaily.com.cn/rss/business_rss.xml", "category": "business", "region": "china", "lang": "en"},
    {"url": "https://www.chinadailyhk.com/rss", "category": "tech", "region": "china", "lang": "en"},
    {"url": "https://english.cas.cn/news/rss/", "category": "research", "region": "china", "lang": "en"},
    {"url": "http://www.cas.cn/rss/", "category": "research", "region": "china", "lang": "zh"},
    {"url": "https://news.fudan.edu.cn/rss.xml", "category": "research", "region": "china", "lang": "zh"},
    {"url": "https://www.gfk.com/insights/rss", "category": "market", "region": "global", "lang": "en"},
    {"url": "https://stcn.com/rss/finance.xml", "category": "finance", "region": "china", "lang": "zh"},
    {"url": "https://xueqiu.com/rss/", "category": "finance", "region": "china", "lang": "zh"},
    {"url": "https://en.ncsti.gov.cn/Latest/rss/", "category": "research", "region": "china", "lang": "en"},
    {"url": "https://arynews.tv/category/technology/feed/", "category": "tech", "region": "global", "lang": "en"},
    {"url": "https://ir.jd.com/rss", "category": "market", "region": "china", "lang": "en"},
    {"url": "https://www.rokid.com/blog/feed/", "category": "wearables", "region": "china", "lang": "en"},
    {"url": "https://www.colmo.com.cn/news/feed/", "category": "appliances", "region": "china", "lang": "zh"},
    {"url": "https://36kr.com/feed", "category": "tech", "region": "china", "lang": "zh"},
    {"url": "https://36kr.com/feed/english", "category": "tech", "region": "china", "lang": "en"},
    {"url": "https://www.kr-asia.com/feed", "category": "tech", "region": "asia", "lang": "en"},
    {"url": "https://jingdaily.com/category/tech/feed/", "category": "trends", "region": "china", "lang": "en"},
    
    # ===== 全球科技媒体 =====
    {"url": "https://techcrunch.com/feed/", "category": "tech", "region": "global", "lang": "en"},
    {"url": "https://www.theverge.com/rss/index.xml", "category": "tech", "region": "global", "lang": "en"},
    {"url": "https://arstechnica.com/feed/", "category": "tech", "region": "global", "lang": "en"},
    {"url": "https://www.engadget.com/rss.xml", "category": "consumer", "region": "global", "lang": "en"},
    {"url": "https://www.gsmarena.com/rss-news-reviews.php", "category": "mobile", "region": "global", "lang": "en"},
    {"url": "https://www.androidauthority.com/feed/", "category": "mobile", "region": "global", "lang": "en"},
    
    # ===== 东南亚新闻 =====
    {"url": "https://www.vietnam-briefing.com/news/feed/", "category": "business", "region": "vietnam", "lang": "en"},
    {"url": "https://e.vnexpress.net/rss/business.rss", "category": "business", "region": "vietnam", "lang": "en"},
    {"url": "https://www.bangkokpost.com/rss/data/business.xml", "category": "business", "region": "thailand", "lang": "en"},
    {"url": "https://thailand-briefing.com/news/feed/", "category": "business", "region": "thailand", "lang": "en"},
    {"url": "https://www.thestar.com.my/rss/business", "category": "business", "region": "malaysia", "lang": "en"},
    {"url": "https://www.nst.com.my/rss/business", "category": "business", "region": "malaysia", "lang": "en"},
    {"url": "https://www.straitstimes.com/news/business/rss.xml", "category": "business", "region": "singapore", "lang": "en"},
    {"url": "https://sbr.com.sg/rss.xml", "category": "business", "region": "singapore", "lang": "en"},
    {"url": "https://indonesia-briefing.com/news/feed/", "category": "business", "region": "indonesia", "lang": "en"},
    {"url": "https://www.thejakartapost.com/rss/business.xml", "category": "business", "region": "indonesia", "lang": "en"},
    {"url": "https://www.philstar.com/rss/business", "category": "business", "region": "philippines", "lang": "en"},
    
    # ===== 行业出版物 =====
    {"url": "https://semiengineering.com/feed/", "category": "semiconductor", "region": "global", "lang": "en"},
    {"url": "https://www.electronicproducts.com/feed/", "category": "components", "region": "global", "lang": "en"},
    {"url": "https://www.displaydaily.com/feed", "category": "display", "region": "global", "lang": "en"},
]

# ==================== 全面的关键词 ====================

# 东南亚地点
SEA_LOCATIONS = [
    'vietnam', '越南', 'thailand', '泰国', 'indonesia', '印尼', '印度尼西亚',
    'malaysia', '马来西亚', 'singapore', '新加坡', 'philippines', '菲律宾',
    'myanmar', '缅甸', 'cambodia', '柬埔寨', 'laos', '老挝', 'brunei', '文莱',
    'asean', '东盟', 'southeast asia', '东南亚',
    'bac ninh', '北宁', 'thai nguyen', '太原', 'ho chi minh', '胡志明',
    'hanoi', '河内', 'haiphong', '海防', 'dong nai', '同奈',
    'binh duong', '平阳', 'long an', '隆安', 'bac giang', '北江',
    'vinh phuc', '永福',
    'bangkok', '曼谷', 'chon buri', '春武里', 'chonburi', 'rayong', '罗勇',
    'ayutthaya', '大城', 'pathum thani', '巴吞他尼', 'samut prakan', '北榄',
    'lamphun', '南奔', 'prachin buri', '巴真', 'amata', '安美德',
    'hemaraj', '赫马拉', 'eastern seaboard', '东部经济走廊', 'eec',
    'jakarta', '雅加达', 'west java', '西爪哇', 'central java', '中爪哇',
    'east java', '东爪哇', 'batam', '巴淡', 'banten', '万丹',
    'bekasi', '勿加泗', 'karawang', '加拉璜', 'tangerang', '唐格朗',
    'kuala lumpur', '吉隆坡', 'penang', '槟城', 'selangor', '雪兰莪',
    'johor', '柔佛', 'melaka', '马六甲', 'kedah', '吉打', 'kulim', '居林',
    'manila', '马尼拉', 'cebu', '宿务'
]

# 消费电子产品与技术 - 家电类和可移动电子数码产品
CONSUMER_ELECTRONICS = [
    # ===== 白色家电 / 家用电器 =====
    'refrigerator', 'fridge', '冷柜', '冰箱', 'freezer', '冰柜',
    'washing machine', 'washer', '洗衣机',
    'air conditioner', 'ac', '空调',
    'microwave', '微波炉', 'oven', '烤箱',
    'dishwasher', '洗碗机',
    'water heater', '热水器',
    'vacuum', '扫地机器人', '吸尘器', 'robot vacuum',
    
    # ===== 厨房电器 =====
    'kitchen appliance', '厨房电器',
    'cooktop', '灶具', 'range hood', '抽油烟机',
    'toaster', '烤面包机', 'coffee maker', '咖啡机',
    'food processor', '食品加工机', 'rice cooker', '电饭煲',
    'air fryer', '空气炸锅',
    
    # ===== 手机 =====
    'smartphone', 'phone', 'mobile', '手机',
    'galaxy', 'samsung', 'apple', 'iphone', 
    'xiaomi', 'oppo', 'vivo', 'realme', 'oneplus',
    'foldable', '折叠屏', '5g', '5G',
    
    # ===== 可穿戴数字产品 =====
    'wearable', '可穿戴',
    'smart watch', 'smartwatch', '智能手表',
    'ai glasses', 'AI眼镜', '智能眼镜',
    'ar glasses', 'AR眼镜', '增强现实',
    'vr headset', 'VR头显', '虚拟现实',
    'headphone', 'earbud', '耳机',
    'fitness tracker', '手环',
    
    # ===== 消费电子品牌 =====
    'haier', '海尔', 'midea', '美的', 'hisense', '海信',
    'tcl', '奥马', 'gree', '格力', 'homa', '奥马',
    'samsung', 'lg', 'sony', 'panasonic', 'toshiba', 'sharp',
    'foxconn', '富士康', 'pegatron', '和硕', 'luxshare', '立讯',
    'goertek', '歌尔', 'lens', '伯恩', 'boe', '京东方',
    'rokid', 'colmo', 'htc', '宏达电',
]

# 制造与投资关键词
MANUFACTURING_KEYWORDS = [
    'factory', 'plant', 'manufacturing', 'production', 'assembly', '生产线', '量产',
    'facility', '新建工厂', '投产', '开工', '奠基', 'investment', 'invest',
    'supplier', '供应链', 'vendor', '供应商', 'localization', '本地化',
    'expansion', '扩建', 'capacity', '产能',
    '出海', 'going global', '全球化', 'globalization',
    '东南亚市场', 'Southeast Asia market', '越南建厂', 'Vietnam factory',
    '泰国投资', 'Thailand investment', '印尼制造', 'Indonesia manufacturing',
    '跨境电商', 'cross-border e-commerce', '海外扩张', 'overseas expansion',
]

# 研究突破关键词
RESEARCH_KEYWORDS = [
    'breakthrough', '突破', 'innovation', '创新', 'research', '研究',
    'prototype', '原型', 'commercialization', '商业化', 'mass production', '量产',
    'thermoelectric', '热电', 'body heat', '体温发电',
    'fiber chip', '纤维芯片', 'electronic fiber', '电子纤维',
    'flexible electronics', '柔性电子', 'wearable tech', '可穿戴技术',
    'brain-computer', '脑机接口', 'bci', '神经接口',
    '新材料', 'new material', '先进材料', 'advanced material',
    '复合材料', 'composite', '高分子', 'polymer',
    '粉体', 'powder', '纳米', 'nano',
    '涂层', 'coating', '薄膜', 'thin film',
    '阻燃', 'flame retardant', '阻燃材料', 'flame retardant material',
    '尼龙', 'nylon', '聚酰胺', 'polyamide',
    '薄膜电容', 'film capacitor', '电容器', 'capacitor',
]

# 展会关键词
EXHIBITION_KEYWORDS = [
    'exhibition', 'expo', 'conference', 'trade show', '展', 'awe', 'ces', 'mwc', 'ifa'
]

# ==================== 主类 ====================
class TechIntelligenceDashboard:
    def __init__(self):
        self.news_items = []
        self.english_news = []
        self.chinese_news = []
        
    def log(self, msg, level="INFO"):
        """增强日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {msg}")
        sys.stdout.flush()
    
    def is_relevant_news(self, title, summary):
        """检查新闻是否关于东南亚 AND 消费电子/制造/研究"""
        text = (title + ' ' + summary).lower()
        
        # 必须提及东南亚地点
        is_sea = any(loc.lower() in text for loc in SEA_LOCATIONS)
        if not is_sea:
            return False
        
        # 检查消费电子、制造、研究关键词
        all_keywords = CONSUMER_ELECTRONICS + MANUFACTURING_KEYWORDS + RESEARCH_KEYWORDS + EXHIBITION_KEYWORDS
        is_relevant = any(kw.lower() in text for kw in all_keywords)
        
        if is_relevant:
            matched_loc = next((loc for loc in SEA_LOCATIONS if loc.lower() in text), "unknown")
            self.log(f"      ✓ SEA: {matched_loc}")
        
        return is_relevant
    
    def fetch_all_news(self):
        """从所有RSS源获取新闻"""
        self.log("📡 正在从60+源获取新闻...")
        feedparser.USER_AGENT = "Mozilla/5.0 (compatible; Executive Dashboard)"
        
        for feed in RSS_FEEDS:
            try:
                self.log(f"  获取: {feed['url']}")
                parsed = feedparser.parse(feed['url'])
                
                for entry in parsed.entries[:15]:
                    title = entry.get('title', 'No title')
                    summary = entry.get('summary', '') or entry.get('description', '')
                    link = entry.get('link', '')
                    
                    if not self.is_relevant_news(title, summary):
                        continue
                    
                    content = ''
                    if 'content' in entry and entry['content']:
                        content = entry['content'][0].get('value', '')[:1000]
                    
                    published = entry.get('published', '')
                    if not published:
                        published = entry.get('updated', datetime.now().strftime('%Y-%m-%d'))
                    
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
                    self.log(f"    ✅ 相关: {title[:60]}...")
                    
                    if feed['lang'] == 'en':
                        self.english_news.append(news_item)
                    else:
                        self.chinese_news.append(news_item)
                        
            except Exception as e:
                self.log(f"  ⚠️ 错误: {feed['url']} - {e}", "WARNING")
                continue
        
        self.log(f"✅ 总相关文章: {len(self.news_items)}")
        self.log(f"   英文: {len(self.english_news)} | 中文: {len(self.chinese_news)}")
        return self.news_items
    
    def translate_chinese_news(self):
        """将中文新闻翻译成英文"""
        if not self.chinese_news:
            return []
        
        self.log("🔄 将中文新闻翻译成英文...")
        translated = []
        
        for news in self.chinese_news[:25]:
            try:
                prompt = f"""Translate this Chinese news to English accurately.

Original Chinese:
Title: {news['title']}
Summary: {news['summary'][:500]}

Requirements:
- Keep all company names accurate (海尔→Haier, 美的→Midea, 京东方→BOE, 富士康→Foxconn)
- Preserve technical terms, investment figures, and timelines exactly
- Maintain product names and specifications
- Keep location names accurate (泰国→Thailand, 越南→Vietnam, etc.)

Provide:
- First line: Title
- Then a concise summary paragraph (2-3 sentences)"""
                
                response = openai.ChatCompletion.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=600,
                    timeout=25
                )
                
                translation = response.choices[0].message.content
                lines = translation.split('\n', 1)
                news['title_en'] = lines[0].strip() if lines else "Translation"
                news['summary_en'] = lines[1].strip() if len(lines) > 1 else translation
                translated.append(news)
                self.log(f"  ✅ 翻译: {news['title'][:40]}...")
                
            except Exception as e:
                self.log(f"  ⚠️ 翻译失败: {e}", "WARNING")
                news['title_en'] = f"[翻译] {news['title']}"
                news['summary_en'] = f"原文: {news['summary'][:200]}..."
                translated.append(news)
        
        self.log(f"✅ 翻译了 {len(translated)} 篇文章")
        return translated
    
    def analyze_trends(self, news_items):
        """分析趋势并提取关键洞察"""
        self.log("📊 分析趋势...")
        
        companies = []
        locations = []
        products = []
        technologies = []
        investments = []
        
        location_news = {}
        tech_news_map = {}
        company_news = {}
        
        for item in news_items:
            title_for_analysis = item.get('title_en', item['title'])
            summary_for_analysis = item.get('summary_en', item.get('summary', ''))
            text = f"{title_for_analysis} {summary_for_analysis}".lower()
            
            # 提取公司
            company_list = [
                ('samsung', 'Samsung'), ('haier', 'Haier'), ('海尔', 'Haier'),
                ('midea', 'Midea'), ('美的', 'Midea'), ('xiaomi', 'Xiaomi'),
                ('oppo', 'OPPO'), ('foxconn', 'Foxconn'), ('富士康', 'Foxconn'),
                ('rokid', 'Rokid'), ('htc', 'HTC'), ('lg', 'LG'),
                ('sony', 'Sony'), ('boe', 'BOE'), ('京东方', 'BOE'),
                ('tcl', 'TCL'), ('hisense', 'Hisense'), ('海信', 'Hisense'),
                ('gree', 'Gree'), ('格力', 'Gree'), ('colmo', 'COLMO')
            ]
            
            for company_key, company_display in company_list:
                if company_key.lower() in text:
                    companies.append(company_display)
                    if company_display not in company_news:
                        company_news[company_display] = []
                    if item not in company_news[company_display]:
                        company_news[company_display].append(item)
            
            # 提取地点
            for loc in SEA_LOCATIONS:
                if loc.lower() in text:
                    loc_title = loc.title()
                    locations.append(loc_title)
                    if loc_title not in location_news:
                        location_news[loc_title] = []
                    if item not in location_news[loc_title]:
                        location_news[loc_title].append(item)
            
            # 提取产品
            product_list = ['smartphone', 'phone', 'glasses', 'wearable', 'watch',
                           'refrigerator', 'fridge', 'air conditioner', 'tv',
                           '扫地机器人', 'vacuum', 'washing machine', 'microwave',
                           'oven', 'robot vacuum', 'earbud', 'headphone']
            
            for prod in product_list:
                if prod.lower() in text:
                    products.append(prod.title())
            
            # 提取新兴技术
            tech_list = [
                ('ai', 'AI'), ('人工智能', 'AI'),
                ('ar', 'AR'), ('增强现实', 'AR'),
                ('vr', 'VR'), ('虚拟现实', 'VR'),
                ('thermoelectric', '热电'), ('热电', '热电'),
                ('fiber chip', '纤维芯片'), ('纤维芯片', '纤维芯片'),
                ('flexible', '柔性电子'), ('柔性', '柔性电子'),
                ('brain-computer', '脑机接口'), ('脑机', '脑机接口'),
                ('powder', '粉体'), ('粉体', '粉体'),
                ('flame retardant', '阻燃'), ('阻燃', '阻燃'),
                ('nylon', '尼龙'), ('尼龙', '尼龙'),
                ('capacitor', '电容器'), ('电容器', '电容器'),
                ('microled', 'MicroLED'), ('oled', 'OLED')
            ]
            
            for tech_key, tech_display in tech_list:
                if tech_key.lower() in text:
                    technologies.append(tech_display)
                    if tech_display not in tech_news_map:
                        tech_news_map[tech_display] = []
                    if item not in tech_news_map[tech_display]:
                        tech_news_map[tech_display].append(item)
            
            if 'invest' in text or '$' in text or 'billion' in text or 'million' in text or '投资' in text:
                investments.append('investment mentioned')
        
        return {
            'top_companies': Counter(companies).most_common(10),
            'top_locations': Counter(locations).most_common(5),
            'top_products': Counter(products).most_common(5),
            'top_technologies': Counter(technologies).most_common(5),
            'total_investments': len(investments),
            'location_news': location_news,
            'tech_news_map': tech_news_map,
            'company_news': company_news
        }
    
    def _get_source_logo(self, source):
        """获取网站logo（简化版）"""
        source_lower = source.lower()
        if 'technews' in source_lower:
            return "📱 TechNews"
        elif 'ledinside' in source_lower:
            return "💡 LEDinside"
        elif 'digitimes' in source_lower:
            return "📰 Digitimes"
        elif '21jingji' in source_lower:
            return "📊 21经济"
        elif 'people' in source_lower:
            return "🏛️ 人民网"
        elif 'ycwb' in source_lower:
            return "📰 羊城晚报"
        elif 'guanhai' in source_lower:
            return "📰 青岛日报"
        elif 'cnyes' in source_lower:
            return "📈 鉅亨網"
        elif 'cnpowder' in source_lower:
            return "⚙️ 粉体网"
        elif 'materials' in source_lower:
            return "🔬 寻材问料"
        elif 'xincailiao' in source_lower:
            return "🧪 新材料在线"
        elif 'aibang' in source_lower:
            return "🧪 艾邦"
        elif 'xiaguangshe' in source_lower:
            return "🌏 霞光社"
        elif 'cena' in source_lower:
            return "📡 电子信息网"
        elif 'chinaoverseasemi' in source_lower:
            return "🔌 出海半导体"
        elif 'mida' in source_lower:
            return "🇲🇾 MIDA"
        elif 'matrade' in source_lower:
            return "🇲🇾 MATRADE"
        elif 'crest' in source_lower:
            return "🇲🇾 CREST"
        elif 'boi' in source_lower:
            return "🇹🇭 BOI"
        elif 'edb' in source_lower:
            return "🇸🇬 EDB"
        elif 'chinadaily' in source_lower:
            return "🇨🇳 China Daily"
        elif 'cas' in source_lower:
            return "🔬 中科院"
        elif 'fudan' in source_lower:
            return "🎓 复旦大学"
        elif 'gfk' in source_lower:
            return "📊 GfK"
        elif 'stcn' in source_lower:
            return "📈 证券时报"
        elif 'xueqiu' in source_lower:
            return "📊 雪球"
        elif 'ncsti' in source_lower:
            return "🔬 NCSTI"
        elif 'arynews' in source_lower:
            return "📰 ARY"
        elif 'jd' in source_lower:
            return "🛒 京东"
        elif 'rokid' in source_lower:
            return "👓 Rokid"
        elif 'colmo' in source_lower:
            return "🏠 COLMO"
        elif '36kr' in source_lower:
            return "📱 36Kr"
        elif 'kr-asia' in source_lower:
            return "🌏 KrASIA"
        elif 'jingdaily' in source_lower:
            return "📰 Jing Daily"
        elif 'techcrunch' in source_lower:
            return "📱 TechCrunch"
        elif 'theverge' in source_lower:
            return "📱 The Verge"
        elif 'arstechnica' in source_lower:
            return "💻 Ars"
        elif 'engadget' in source_lower:
            return "📱 Engadget"
        elif 'gsmarena' in source_lower:
            return "📱 GSMArena"
        elif 'androidauthority' in source_lower:
            return "🤖 Android Auth"
        elif 'vietnam-briefing' in source_lower:
            return "🇻🇳 Vietnam Briefing"
        elif 'vnexpress' in source_lower:
            return "🇻🇳 VNExpress"
        elif 'bangkokpost' in source_lower:
            return "🇹🇭 Bangkok Post"
        elif 'thestar' in source_lower:
            return "🇲🇾 The Star"
        elif 'nst' in source_lower:
            return "🇲🇾 NST"
        elif 'straitstimes' in source_lower:
            return "🇸🇬 Straits Times"
        elif 'sbr' in source_lower:
            return "🇸🇬 SBR"
        elif 'jakartapost' in source_lower:
            return "🇮🇩 Jakarta Post"
        elif 'philstar' in source_lower:
            return "🇵🇭 PhilStar"
        elif 'semiengineering' in source_lower:
            return "🔧 SemiEngineering"
        elif 'electronicproducts' in source_lower:
            return "🔌 Elec Products"
        elif 'displaydaily' in source_lower:
            return "📺 DisplayDaily"
        else:
            return f"📰 {source[:15]}"
    
    def _create_news_card(self, item, logo_color="#0066cc"):
        """创建统一的新闻卡片"""
        title = html_module.escape(item.get('title_en', item['title'])[:100])
        summary = html_module.escape(item.get('summary_en', item.get('summary', ''))[:200])
        source_logo = self._get_source_logo(item['source'])
        link = item['link']
        
        return f"""
        <div class="news-card" style="margin-bottom: 20px; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid {logo_color};">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="background: {logo_color}; color: white; padding: 5px 10px; border-radius: 20px; font-size: 0.85em; font-weight: bold; margin-right: 10px;">{source_logo}</span>
                <span style="color: #666; font-size: 0.85em;">{item.get('published', '')[:10]}</span>
            </div>
            <h4 style="font-size: 1.2em; margin-bottom: 10px; color: #0a1929;">{title}</h4>
            <p style="color: #334155; margin-bottom: 15px; line-height: 1.5;">{summary}...</p>
            <a href="{link}" style="color: {logo_color}; text-decoration: none; font-weight: 500;" target="_blank">🔗 阅读原文 →</a>
        </div>
        """
    
    def generate_executive_dashboard(self, news_items, trends):
        """生成专业HTML仪表板"""
        self.log("🎨 创建高管仪表板...")
        
        date = datetime.now().strftime('%B %d, %Y')
        
        # 分类新闻
        tech_news = []          # 新技术与产品（家电、可移动数码）
        manufacturing_news = [] # 制造与投资
        research_news = []      # 研究突破
        exhibition_news = []    # 展会活动
        
        for n in news_items:
            text = (n.get('title_en', n['title']) + ' ' + n.get('summary_en', n.get('summary', ''))).lower()
            
            # 新技术与产品 - 只保留家电类和可移动电子数码产品
            is_tech = False
            for keyword in ['refrigerator', 'fridge', 'washing machine', 'air conditioner', 
                           'microwave', 'oven', 'vacuum', '扫地机器人', 'robot vacuum',
                           'smartphone', 'phone', 'wearable', 'watch', 'glasses', '眼镜',
                           'ar', 'vr', 'ai', 'earbud', 'headphone', '智能手表', '智能眼镜']:
                if keyword.lower() in text:
                    is_tech = True
                    break
            
            if is_tech:
                tech_news.append(n)
            
            # 制造与投资 - 工厂、投资、出海、政府公告
            is_manufacturing = False
            for keyword in MANUFACTURING_KEYWORDS:
                if keyword.lower() in text:
                    is_manufacturing = True
                    break
            
            if is_manufacturing:
                manufacturing_news.append(n)
            
            # 研究突破
            is_research = False
            for keyword in RESEARCH_KEYWORDS:
                if keyword.lower() in text:
                    is_research = True
                    break
            
            if is_research:
                research_news.append(n)
            
            # 展会活动
            is_exhibition = False
            for keyword in EXHIBITION_KEYWORDS:
                if keyword.lower() in text:
                    is_exhibition = True
                    break
            
            if is_exhibition:
                exhibition_news.append(n)
        
        self.log(f"   分类: 技术 {len(tech_news)}, 制造 {len(manufacturing_news)}, 研究 {len(research_news)}, 展会 {len(exhibition_news)}")
        
        # 生成各专题HTML
        tech_html = self._create_tech_section(tech_news[:10])
        manufacturing_html = self._create_manufacturing_section(manufacturing_news[:10], trends)
        research_html = self._create_research_section(research_news[:8])
        exhibition_html = self._create_exhibition_section(exhibition_news[:6])
        
        # 生成高管摘要
        exec_summary = self._generate_executive_summary(news_items, trends, manufacturing_news, tech_news, research_news)
        
        # 构建完整HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>东南亚消费电子智能简报 - {date}</title>
    <style>
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
        
        .news-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
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
        
        @media (max-width: 768px) {{
            .news-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1><strong>东南亚消费电子</strong> 智能简报</h1>
            <div class="date">{date}</div>
            <div class="meta">
                <span>📊 分析文章: {len(news_items)}</span>
                <span>🌏 聚焦: 东南亚</span>
                <span>📱 消费电子 + 新材料 + 出海</span>
                <span>⏰ {datetime.now().strftime('%H:%M:%S')}</span>
            </div>
        </div>
        
        <div class="summary-card">
            <h2>📋 高管摘要</h2>
            <p>{exec_summary}</p>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-icon">📱</div>
                <div class="kpi-label">新技术与产品</div>
                <div class="kpi-value">{len(tech_news)}</div>
                <div class="kpi-trend">家电、可穿戴、手机</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🏭</div>
                <div class="kpi-label">制造与投资</div>
                <div class="kpi-value">{len(manufacturing_news)}</div>
                <div class="kpi-trend">东南亚建厂、出海</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🔬</div>
                <div class="kpi-label">研究突破</div>
                <div class="kpi-value">{len(research_news)}</div>
                <div class="kpi-trend">材料、芯片、AI</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🎪</div>
                <div class="kpi-label">展会活动</div>
                <div class="kpi-value">{len(exhibition_news)}</div>
                <div class="kpi-trend">即将举办的展会</div>
            </div>
        </div>
        
        <!-- 1. 新技术与产品专题 (移到制造上方) -->
        <div class="section-header">
            <h2>📱 新技术与产品</h2>
        </div>
        <div class="news-grid">
            {tech_html}
        </div>
        
        <!-- 2. 制造与投资专题 (含政府网站、出海报道) -->
        <div class="section-header">
            <h2>🏭 制造与投资</h2>
        </div>
        <div class="news-grid">
            {manufacturing_html}
        </div>
        
        <!-- 3. 研究突破专题 -->
        <div class="section-header">
            <h2>🔬 研究突破与技术前沿</h2>
        </div>
        <div class="news-grid">
            {research_html}
        </div>
        
        <!-- 4. 展会活动专题 -->
        <div class="section-header">
            <h2>🎪 展会与活动</h2>
        </div>
        <div class="news-grid">
            {exhibition_html}
        </div>
        
        <div class="footer">
            <p>东南亚消费电子制造情报 • 涵盖新材料、粉体技术、高分子、出海报道、政府投资公告</p>
            <p>信息来源: 中国粉体网, 寻材问料, 新材料在线, 霞光社, 艾邦高分子, MIDA, BOI, EDB, 中科院, 复旦大学</p>
            <div class="disclaimer">
                © 2026 东南亚消费电子智能简报 • 仅供高管审阅 • 由DeepSeek AI生成
            </div>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _create_tech_section(self, tech_news):
        """创建新技术与产品专题 - 只保留家电和可移动数码产品"""
        if not tech_news:
            return '<p style="color:#666; text-align:center; padding:30px;">今日无相关技术新闻。</p>'
        
        html = ""
        for item in tech_news:
            html += self._create_news_card(item, logo_color="#0066cc")
        return html
    
    def _create_manufacturing_section(self, manufacturing_news, trends):
        """创建制造与投资专题 - 含政府网站、出海报道，整合制造热点"""
        if not manufacturing_news:
            return '<p style="color:#666; text-align:center; padding:30px;">今日无制造与投资新闻。</p>'
        
        html = ""
        
        # 先显示制造热点统计数据（简洁版）
        if trends['top_locations']:
            html += '<div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #e0e0e0;">'
            html += '<h4 style="margin-bottom: 15px; color: #0a1929;">📍 制造热点分布</h4>'
            html += '<div style="display: flex; flex-wrap: wrap; gap: 15px;">'
            
            for location, count in trends['top_locations'][:5]:
                location_key = location.title() if isinstance(location, str) else location[0].title()
                related_news = trends.get('location_news', {}).get(location_key, [])
                
                html += f"""
                <div style="flex: 1; min-width: 120px; background: white; padding: 12px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="font-weight: bold; color: #0066cc;">{location_key}</div>
                    <div style="font-size: 1.5em; font-weight: bold;">{count}</div>
                    <div style="font-size: 0.85em; color: #666;">{len(related_news)} 条新闻</div>
                </div>
                """
            
            html += '</div></div>'
        
        # 显示制造新闻卡片
        for item in manufacturing_news:
            html += self._create_news_card(item, logo_color="#10b981")
        
        return html
    
    def _create_research_section(self, research_news):
        """创建研究突破专题"""
        if not research_news:
            return '<p style="color:#666; text-align:center; padding:30px;">今日无研究突破新闻。</p>'
        
        html = ""
        for item in research_news:
            html += self._create_news_card(item, logo_color="#8b5cf6")
        return html
    
    def _create_exhibition_section(self, exhibition_news):
        """创建展会活动专题"""
        if not exhibition_news:
            return '<p style="color:#666; text-align:center; padding:30px;">今日无展会新闻。</p>'
        
        html = ""
        for item in exhibition_news:
            html += self._create_news_card(item, logo_color="#ff9800")
        return html
    
    def _generate_executive_summary(self, news_items, trends, manufacturing_news, tech_news, research_news):
        """生成高管摘要"""
        try:
            locations = ', '.join([loc[0].title() for loc in trends['top_locations'][:2]]) if trends['top_locations'] else '东南亚'
            companies = ', '.join([comp[0].title() for comp in trends['top_companies'][:2]]) if trends['top_companies'] else '主要品牌'
            technologies = ', '.join([tech[0] for tech in trends['top_technologies'][:2]]) if trends['top_technologies'] else '新兴技术'
            
            prompt = f"""Write a 4-sentence executive summary in English about consumer electronics in Southeast Asia.

Today's highlights:
- New products/tech: {len(tech_news)} articles on appliances, wearables, smartphones
- Manufacturing/investment: {len(manufacturing_news)} articles on factories, investment,出海
- Research breakthroughs: {len(research_news)} articles on materials, chips, AI
- Key locations: {locations}
- Active companies: {companies}
- Emerging technologies: {technologies}

Make it professional, data-driven, and impactful for a company director."""
            
            response = openai.ChatCompletion.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=250,
                timeout=10
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.log(f"⚠️ 摘要生成失败: {e}", "WARNING")
            return f"Today's report covers {len(news_items)} articles on consumer electronics in Southeast Asia. Highlights include {len(tech_news)} new products/technologies, {len(manufacturing_news)} manufacturing/investment projects, and {len(research_news)} research breakthroughs. Key activity in {locations} from companies including {companies}."
    
    def parse_recipients(self, recipients_string):
        """解析邮件收件人"""
        if not recipients_string:
            return []
        cleaned = recipients_string.replace('*', '').replace('\n', ',').replace('\r', ',').replace(';', ',')
        recipients = [email.strip() for email in cleaned.split(',') if email.strip() and '@' in email]
        return recipients
    
    def send_email(self, subject, html_content):
        """发送邮件"""
        self.log("\n📧 发送高管简报...")
        
        try:
            recipients = self.parse_recipients(EMAIL_CONFIG["receiver_email"])
            if not recipients:
                self.log("❌ 无有效收件人", "ERROR")
                return False
            
            self.log(f"   收件人: {recipients}")
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = EMAIL_CONFIG["sender_email"]
            msg['To'] = ', '.join(recipients)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            try:
                server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
                server.ehlo()
                server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
                server.send_message(msg)
                server.quit()
                self.log("✅ 通过SSL端口465发送成功")
                return True
            except Exception as e:
                self.log(f"⚠️ SSL失败: {e}, 尝试TLS...", "WARNING")
                
                server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
                server.starttls()
                server.ehlo()
                server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
                server.send_message(msg)
                server.quit()
                self.log("✅ 通过TLS端口587发送成功")
                return True
            
        except Exception as e:
            self.log(f"❌ 邮件发送失败: {e}", "ERROR")
            traceback.print_exc()
            return False
    
    def run(self):
        """主执行流程"""
        self.log("\n" + "="*70)
        self.log("🚀 东南亚消费电子智能简报系统")
        self.log("="*70)
        
        start_time = time.time()
        
        news_items = self.fetch_all_news()
        if not news_items:
            self.log("❌ 未找到相关新闻", "ERROR")
            return
        
        translated = self.translate_chinese_news()
        all_news = news_items + translated
        
        trends = self.analyze_trends(all_news)
        
        html_content = self.generate_executive_dashboard(all_news, trends)
        
        subject = f"📱 东南亚消费电子简报 - {datetime.now().strftime('%Y-%m-%d')}"
        self.send_email(subject, html_content)
        
        elapsed = time.time() - start_time
        self.log("\n" + "="*70)
        self.log(f"✅ 完成，耗时 {elapsed:.1f} 秒")
        self.log("="*70)

# ==================== 主程序 ====================
if __name__ == "__main__":
    dashboard = TechIntelligenceDashboard()
    dashboard.run()
