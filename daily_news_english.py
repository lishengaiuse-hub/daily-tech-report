#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东南亚消费电子智能简报系统
每日高管简报，严格过滤只保留消费电子产品相关新闻
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

# ==================== 严格的关键词定义 ====================

# 东南亚地点（保持不变）
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

# ===== 家电类产品关键词（严格）=====
HOME_APPLIANCES_KEYWORDS = [
    # 冰箱/冷柜
    'refrigerator', 'fridge', '冷柜', '冰箱', 'freezer', '冰柜',
    # 洗衣机
    'washing machine', 'washer', '洗衣机',
    # 空调
    'air conditioner', 'ac', '空调',
    # 厨房电器
    'microwave', '微波炉', 'oven', '烤箱', 'dishwasher', '洗碗机',
    'toaster', '烤面包机', 'coffee maker', '咖啡机',
    'food processor', '食品加工机', 'rice cooker', '电饭煲',
    'air fryer', '空气炸锅',
    # 清洁电器
    'vacuum', '扫地机器人', '吸尘器', 'robot vacuum', 'vacuum cleaner',
    # 热水器
    'water heater', '热水器',
    # 电视/显示器
    'tv', 'television', '电视',
    # 通用家电品牌
    'haier', '海尔', 'midea', '美的', 'hisense', '海信',
    'gree', '格力', 'lg', 'panasonic', 'sharp', 'toshiba',
]

# ===== 可移动电子数码产品关键词（严格）=====
MOBILE_ELECTRONICS_KEYWORDS = [
    # 手机
    'smartphone', 'phone', 'mobile', '手机',
    'samsung', 'galaxy', 'apple', 'iphone', 'xiaomi', 'oppo', 'vivo', 'realme',
    'foldable', '折叠屏',
    # 可穿戴设备
    'wearable', '可穿戴',
    'smart watch', 'smartwatch', '智能手表',
    'fitness tracker', '手环',
    # 智能眼镜/AR/VR
    'ai glasses', 'AI眼镜', '智能眼镜',
    'ar glasses', 'AR眼镜', 'augmented reality', '增强现实',
    'vr headset', 'VR头显', 'virtual reality', '虚拟现实',
    'mr headset', 'mixed reality', '混合现实',
    # 音频设备
    'headphone', 'earphone', 'earbud', '耳机',
    'true wireless', 'tws',
    # 平板/笔记本
    'tablet', 'ipad', 'laptop', 'notebook',
    # 相机/无人机
    'camera', 'drone', 'action camera',
    # 可穿戴品牌
    'rokid', 'htc', 'vive', 'meta quest', 'pico',
]

# ===== 制造与投资关键词 =====
MANUFACTURING_KEYWORDS = [
    'factory', 'plant', 'manufacturing', 'production', 'assembly', '生产线', '量产',
    'facility', '新建工厂', '投产', '开工', '奠基', 'investment', 'invest',
    'supplier', '供应链', 'vendor', '供应商', 'localization', '本地化',
    'expansion', '扩建', 'capacity', '产能',
    '出海', 'going global', '全球化', 'globalization',
    '东南亚市场', 'Southeast Asia market', '越南建厂', 'Vietnam factory',
    '泰国投资', 'Thailand investment', '印尼制造', 'Indonesia manufacturing',
    '海外扩张', 'overseas expansion',
]

# ===== 研究突破关键词 =====
RESEARCH_KEYWORDS = [
    'breakthrough', '突破', 'innovation', '创新', 'research', '研究',
    'prototype', '原型', 'commercialization', '商业化',
    'thermoelectric', '热电', 'body heat', '体温发电',
    'fiber chip', '纤维芯片', 'electronic fiber', '电子纤维',
    'flexible electronics', '柔性电子', 'wearable tech', '可穿戴技术',
    'brain-computer', '脑机接口', 'bci',
    '新材料', 'new material', '先进材料', 'advanced material',
    '复合材料', 'composite', '高分子', 'polymer',
    '粉体', 'powder', '纳米', 'nano',
    '涂层', 'coating', '薄膜', 'thin film',
    '阻燃', 'flame retardant', '阻燃材料',
    '尼龙', 'nylon', '聚酰胺', 'polyamide',
    '薄膜电容', 'film capacitor', '电容器', 'capacitor',
]

# ===== 展会关键词 =====
EXHIBITION_KEYWORDS = [
    'exhibition', 'expo', 'conference', 'trade show', '展', 
    'awe', 'ces', 'mwc', 'ifa', 'electronica',
]

# ==================== RSS源 ====================
RSS_FEEDS = [
    # 中文科技媒体
    {"url": "https://technews.tw/feed/", "category": "tech", "region": "taiwan", "lang": "zh"},
    {"url": "https://finance.technews.tw/feed/", "category": "finance", "region": "taiwan", "lang": "zh"},
    {"url": "https://www.ledinside.cn/rss.xml", "category": "display", "region": "china", "lang": "zh"},
    {"url": "https://www.digitimes.com.tw/rss/rptlist.asp", "category": "semiconductor", "region": "taiwan", "lang": "zh"},
    
    # 材料专业网站
    {"url": "http://www.cnpowder.com.cn/rss/", "category": "materials", "region": "china", "lang": "zh"},
    {"url": "http://www.materials.cn/rss/", "category": "materials", "region": "china", "lang": "zh"},
    {"url": "https://www.xincailiao.com/rss/", "category": "materials", "region": "china", "lang": "zh"},
    {"url": "https://www.aibang.com/feed/", "category": "materials", "region": "china", "lang": "zh"},
    
    # 出海报道
    {"url": "https://xiaguangshe.com/feed/", "category": "overseas", "region": "china", "lang": "zh"},
    {"url": "https://www.cena.com.cn/rss.xml", "category": "industry", "region": "china", "lang": "zh"},
    
    # 政府网站
    {"url": "https://www.mida.gov.my/press-releases/feed/", "category": "investment", "region": "malaysia", "lang": "en"},
    {"url": "https://www.boi.go.th/upload/rss/boi_news_en.xml", "category": "investment", "region": "thailand", "lang": "en"},
    {"url": "https://www.edb.gov.sg/en/news-and-events/feed.html", "category": "investment", "region": "singapore", "lang": "en"},
    
    # 全球科技媒体
    {"url": "https://techcrunch.com/feed/", "category": "tech", "region": "global", "lang": "en"},
    {"url": "https://www.theverge.com/rss/index.xml", "category": "tech", "region": "global", "lang": "en"},
    {"url": "https://www.engadget.com/rss.xml", "category": "consumer", "region": "global", "lang": "en"},
    {"url": "https://www.gsmarena.com/rss-news-reviews.php", "category": "mobile", "region": "global", "lang": "en"},
    
    # 东南亚新闻
    {"url": "https://www.bangkokpost.com/rss/data/business.xml", "category": "business", "region": "thailand", "lang": "en"},
    {"url": "https://www.thestar.com.my/rss/business", "category": "business", "region": "malaysia", "lang": "en"},
    {"url": "https://www.straitstimes.com/news/business/rss.xml", "category": "business", "region": "singapore", "lang": "en"},
]

# ==================== 主类 ====================
class TechIntelligenceDashboard:
    def __init__(self):
        self.news_items = []
        self.english_news = []
        self.chinese_news = []
        # 存储各专题的实际新闻
        self.tech_news = []
        self.manufacturing_news = []
        self.research_news = []
        self.exhibition_news = []
        
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {msg}")
        sys.stdout.flush()
    
    def is_relevant_news(self, title, summary):
        """严格检查新闻是否相关 - 必须同时满足：东南亚地点 + 消费电子相关"""
        text = (title + ' ' + summary).lower()
        
        # 必须提及东南亚地点
        is_sea = any(loc.lower() in text for loc in SEA_LOCATIONS)
        if not is_sea:
            return False
        
        # 检查是否属于任何类别
        is_home_appliance = any(kw.lower() in text for kw in HOME_APPLIANCES_KEYWORDS)
        is_mobile_electronics = any(kw.lower() in text for kw in MOBILE_ELECTRONICS_KEYWORDS)
        is_manufacturing = any(kw.lower() in text for kw in MANUFACTURING_KEYWORDS)
        is_research = any(kw.lower() in text for kw in RESEARCH_KEYWORDS)
        is_exhibition = any(kw.lower() in text for kw in EXHIBITION_KEYWORDS)
        
        is_relevant = is_home_appliance or is_mobile_electronics or is_manufacturing or is_research or is_exhibition
        
        if is_relevant:
            self.log(f"      ✓ 相关: {title[:60]}...")
        
        return is_relevant
    
    def categorize_news(self, news_item):
        """将新闻分类到具体专题"""
        text = (news_item.get('title_en', news_item['title']) + ' ' + 
                news_item.get('summary_en', news_item.get('summary', ''))).lower()
        
        categories = []
        
        # 新技术与产品 - 家电和可移动数码
        is_home_appliance = any(kw.lower() in text for kw in HOME_APPLIANCES_KEYWORDS)
        is_mobile_electronics = any(kw.lower() in text for kw in MOBILE_ELECTRONICS_KEYWORDS)
        
        if is_home_appliance or is_mobile_electronics:
            categories.append('tech')
        
        # 制造与投资
        if any(kw.lower() in text for kw in MANUFACTURING_KEYWORDS):
            categories.append('manufacturing')
        
        # 研究突破
        if any(kw.lower() in text for kw in RESEARCH_KEYWORDS):
            categories.append('research')
        
        # 展会
        if any(kw.lower() in text for kw in EXHIBITION_KEYWORDS):
            categories.append('exhibition')
        
        return categories
    
    def fetch_all_news(self):
        self.log("📡 正在获取新闻...")
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
                    
                    published = entry.get('published', '')
                    if not published:
                        published = entry.get('updated', datetime.now().strftime('%Y-%m-%d'))
                    
                    source = feed['url'].split('/')[2] if '//' in feed['url'] else feed['url']
                    
                    news_item = {
                        'title': title,
                        'summary': summary[:800],
                        'link': link,
                        'source': source,
                        'published': published,
                        'category': feed['category'],
                        'region': feed['region'],
                        'lang': feed['lang']
                    }
                    
                    self.news_items.append(news_item)
                    
                    if feed['lang'] == 'en':
                        self.english_news.append(news_item)
                    else:
                        self.chinese_news.append(news_item)
                        
            except Exception as e:
                self.log(f"  ⚠️ 错误: {feed['url']} - {e}", "WARNING")
                continue
        
        self.log(f"✅ 总相关文章: {len(self.news_items)}")
        return self.news_items
    
    def translate_chinese_news(self):
        """翻译中文新闻"""
        if not self.chinese_news:
            return []
        
        self.log("🔄 翻译中文新闻...")
        translated = []
        
        for news in self.chinese_news[:20]:
            try:
                prompt = f"""Translate this Chinese news to English accurately.

Original Chinese:
Title: {news['title']}
Summary: {news['summary'][:500]}

Requirements:
- Keep company names accurate (海尔→Haier, 美的→Midea, 京东方→BOE)
- Preserve technical terms and locations
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
                news['title_en'] = lines[0].replace('Title:', '').strip() if 'Title:' in lines[0] else lines[0].strip()
                news['summary_en'] = lines[1].replace('Summary:', '').strip() if len(lines) > 1 else translation
                translated.append(news)
                self.log(f"  ✅ 翻译: {news['title'][:40]}...")
                
            except Exception as e:
                self.log(f"  ⚠️ 翻译失败: {e}", "WARNING")
                news['title_en'] = f"[Translation] {news['title']}"
                news['summary_en'] = news['summary'][:200]
                translated.append(news)
        
        return translated
    
    def analyze_and_categorize(self, news_items):
        """分析和分类新闻，确保KPI数字准确"""
        self.log("📊 分析新闻分类...")
        
        # 清空各专题列表
        self.tech_news = []
        self.manufacturing_news = []
        self.research_news = []
        self.exhibition_news = []
        
        # 用于趋势分析
        companies = []
        locations = []
        technologies = []
        location_news = {}
        
        for item in news_items:
            # 分类新闻
            categories = self.categorize_news(item)
            
            for cat in categories:
                if cat == 'tech' and item not in self.tech_news:
                    self.tech_news.append(item)
                elif cat == 'manufacturing' and item not in self.manufacturing_news:
                    self.manufacturing_news.append(item)
                elif cat == 'research' and item not in self.research_news:
                    self.research_news.append(item)
                elif cat == 'exhibition' and item not in self.exhibition_news:
                    self.exhibition_news.append(item)
            
            # 收集趋势数据
            text = (item.get('title_en', item['title']) + ' ' + 
                   item.get('summary_en', item.get('summary', ''))).lower()
            
            # 提取公司
            for company in ['samsung', 'haier', '海尔', 'midea', '美的', 'xiaomi', 
                           'oppo', 'foxconn', '富士康', 'rokid']:
                if company.lower() in text:
                    companies.append(company.replace('海尔', 'Haier').replace('美的', 'Midea'))
            
            # 提取地点
            for loc in SEA_LOCATIONS:
                if loc.lower() in text:
                    loc_title = loc.title()
                    locations.append(loc_title)
                    if loc_title not in location_news:
                        location_news[loc_title] = []
                    if item not in location_news[loc_title]:
                        location_news[loc_title].append(item)
            
            # 提取技术
            for tech in ['ai', 'ar', 'vr', 'thermoelectric', 'flexible', '脑机']:
                if tech.lower() in text:
                    technologies.append(tech.upper() if tech in ['ai', 'ar', 'vr'] else tech.title())
        
        # 去重并限制数量
        self.tech_news = self.tech_news[:15]
        self.manufacturing_news = self.manufacturing_news[:15]
        self.research_news = self.research_news[:10]
        self.exhibition_news = self.exhibition_news[:8]
        
        self.log(f"   分类结果:")
        self.log(f"     新技术与产品: {len(self.tech_news)} 条")
        self.log(f"     制造与投资: {len(self.manufacturing_news)} 条")
        self.log(f"     研究突破: {len(self.research_news)} 条")
        self.log(f"     展会活动: {len(self.exhibition_news)} 条")
        
        return {
            'top_companies': Counter(companies).most_common(10),
            'top_locations': Counter(locations).most_common(5),
            'top_technologies': Counter(technologies).most_common(5),
            'location_news': location_news
        }
    
    def _get_source_logo(self, source):
        """获取网站logo"""
        source_lower = source.lower()
        logos = {
            'technews': '📱 TechNews', 'ledinside': '💡 LEDinside', 'digitimes': '📰 Digitimes',
            '21jingji': '📊 21经济', 'people': '🏛️ 人民网', 'ycwb': '📰 羊城晚报',
            'guanhai': '📰 青岛日报', 'cnyes': '📈 鉅亨網', 'cnpowder': '⚙️ 粉体网',
            'materials': '🔬 寻材问料', 'xincailiao': '🧪 新材料在线', 'aibang': '🧪 艾邦',
            'xiaguangshe': '🌏 霞光社', 'cena': '📡 电子信息网', 'mida': '🇲🇾 MIDA',
            'boi': '🇹🇭 BOI', 'edb': '🇸🇬 EDB', 'chinadaily': '🇨🇳 China Daily',
            'cas': '🔬 中科院', 'fudan': '🎓 复旦大学', 'gfk': '📊 GfK',
            'stcn': '📈 证券时报', 'xueqiu': '📊 雪球', 'jd': '🛒 京东',
            'rokid': '👓 Rokid', 'colmo': '🏠 COLMO', '36kr': '📱 36Kr',
            'kr-asia': '🌏 KrASIA', 'techcrunch': '📱 TechCrunch', 'theverge': '📱 The Verge',
            'engadget': '📱 Engadget', 'gsmarena': '📱 GSMArena', 'bangkokpost': '🇹🇭 Bangkok Post',
            'thestar': '🇲🇾 The Star', 'straitstimes': '🇸🇬 Straits Times',
        }
        
        for key, logo in logos.items():
            if key in source_lower:
                return logo
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
        """生成HTML仪表板，确保KPI数字与实际展示条数一致"""
        self.log("🎨 创建高管仪表板...")
        
        date = datetime.now().strftime('%B %d, %Y')
        
        # 生成各专题HTML
        tech_html = ""
        for item in self.tech_news:
            tech_html += self._create_news_card(item, logo_color="#0066cc")
        if not tech_html:
            tech_html = '<p style="color:#666; text-align:center; padding:30px;">今日无相关技术新闻。</p>'
        
        # 制造与投资专题
        manufacturing_html = ""
        if self.manufacturing_news:
            # 显示制造热点统计
            if trends['top_locations']:
                manufacturing_html += '<div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 25px;">'
                manufacturing_html += '<h4 style="margin-bottom: 15px; color: #0a1929;">📍 制造热点分布</h4>'
                manufacturing_html += '<div style="display: flex; flex-wrap: wrap; gap: 15px;">'
                
                for location, count in trends['top_locations'][:5]:
                    location_key = location.title() if isinstance(location, str) else location[0].title()
                    location_count = len(trends.get('location_news', {}).get(location_key, []))
                    
                    manufacturing_html += f"""
                    <div style="flex: 1; min-width: 120px; background: white; padding: 12px; border-radius: 8px;">
                        <div style="font-weight: bold; color: #0066cc;">{location_key}</div>
                        <div style="font-size: 1.5em; font-weight: bold;">{location_count}</div>
                        <div style="font-size: 0.85em; color: #666;">条新闻</div>
                    </div>
                    """
                manufacturing_html += '</div></div>'
            
            for item in self.manufacturing_news:
                manufacturing_html += self._create_news_card(item, logo_color="#10b981")
        else:
            manufacturing_html = '<p style="color:#666; text-align:center; padding:30px;">今日无制造与投资新闻。</p>'
        
        # 研究突破专题
        research_html = ""
        for item in self.research_news:
            research_html += self._create_news_card(item, logo_color="#8b5cf6")
        if not research_html:
            research_html = '<p style="color:#666; text-align:center; padding:30px;">今日无研究突破新闻。</p>'
        
        # 展会活动专题
        exhibition_html = ""
        for item in self.exhibition_news:
            exhibition_html += self._create_news_card(item, logo_color="#ff9800")
        if not exhibition_html:
            exhibition_html = '<p style="color:#666; text-align:center; padding:30px;">今日无展会新闻。</p>'
        
        # 生成高管摘要 - 使用实际的新闻条数
        exec_summary = self._generate_executive_summary(
            len(self.tech_news),
            len(self.manufacturing_news), 
            len(self.research_news),
            trends
        )
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>东南亚消费电子智能简报 - {date}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f0f2f5;
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
        }}
        .header h1 {{ font-size: 2.5em; font-weight: 300; }}
        .header h1 strong {{ font-weight: 600; color: #ffd700; }}
        .header .date {{ color: #94a3b8; font-size: 1.1em; margin: 10px 0 20px; }}
        .header .meta {{ display: flex; gap: 30px; color: #cbd5e1; border-top: 1px solid #334155; padding-top: 20px; }}
        
        .summary-card {{
            background: white; border-radius: 16px; padding: 35px; margin-bottom: 30px;
            border-left: 6px solid #ffd700; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        .summary-card h2 {{ color: #0a1929; font-size: 1.8em; margin-bottom: 20px; }}
        .summary-card p {{ font-size: 1.2em; color: #334155; line-height: 1.8; }}
        
        .kpi-grid {{
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 25px; margin-bottom: 40px;
        }}
        .kpi-card {{
            background: white; border-radius: 16px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        .kpi-icon {{ font-size: 2.5em; margin-bottom: 15px; }}
        .kpi-value {{ font-size: 2.8em; font-weight: 600; color: #0a1929; line-height: 1.2; }}
        .kpi-label {{ color: #64748b; font-size: 1em; text-transform: uppercase; margin-bottom: 10px; }}
        
        .section-header {{ margin: 50px 0 30px; }}
        .section-header h2 {{
            font-size: 2.2em; color: #0a1929; font-weight: 500;
            display: inline-block; background: #f0f2f5; padding-right: 20px;
        }}
        
        .news-grid {{
            display: grid; grid-template-columns: repeat(auto-fill, minmax(450px, 1fr)); gap: 25px;
        }}
        
        .footer {{
            background: #0a1929; color: white; padding: 40px; border-radius: 0 0 20px 20px;
            margin-top: 50px; text-align: center;
        }}
        .footer p {{ color: #94a3b8; margin-bottom: 10px; }}
        
        @media (max-width: 768px) {{
            .kpi-grid {{ grid-template-columns: 1fr; }}
            .news-grid {{ grid-template-columns: 1fr; }}
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
                <span>🌏 聚焦: 东南亚消费电子</span>
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
                <div class="kpi-value">{len(self.tech_news)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🏭</div>
                <div class="kpi-label">制造与投资</div>
                <div class="kpi-value">{len(self.manufacturing_news)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🔬</div>
                <div class="kpi-label">研究突破</div>
                <div class="kpi-value">{len(self.research_news)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🎪</div>
                <div class="kpi-label">展会活动</div>
                <div class="kpi-value">{len(self.exhibition_news)}</div>
            </div>
        </div>
        
        <div class="section-header"><h2>📱 新技术与产品</h2></div>
        <div class="news-grid">{tech_html}</div>
        
        <div class="section-header"><h2>🏭 制造与投资</h2></div>
        <div class="news-grid">{manufacturing_html}</div>
        
        <div class="section-header"><h2>🔬 研究突破</h2></div>
        <div class="news-grid">{research_html}</div>
        
        <div class="section-header"><h2>🎪 展会活动</h2></div>
        <div class="news-grid">{exhibition_html}</div>
        
        <div class="footer">
            <p>东南亚消费电子智能简报 • 严格过滤只保留电子产品相关新闻</p>
            <p>信息来源: 科技媒体、政府网站、出海报道、材料专业网站</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _generate_executive_summary(self, tech_count, manuf_count, research_count, trends):
        """生成高管摘要，使用实际的新闻条数"""
        try:
            locations = ', '.join([loc[0].title() for loc in trends['top_locations'][:2]]) if trends['top_locations'] else '东南亚'
            companies = ', '.join([comp[0].title() for comp in trends['top_companies'][:2]]) if trends['top_companies'] else '主要品牌'
            
            prompt = f"""Write a 3-sentence executive summary about consumer electronics in Southeast Asia.

Today's numbers:
- New products: {tech_count} articles
- Manufacturing/Investment: {manuf_count} articles
- Research breakthroughs: {research_count} articles
- Key locations: {locations}
- Active companies: {companies}

Make it professional and concise for a company director."""
            
            response = openai.ChatCompletion.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
                timeout=10
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.log(f"⚠️ 摘要生成失败: {e}", "WARNING")
            return f"Today's report covers {tech_count} new products, {manuf_count} manufacturing projects, and {research_count} research breakthroughs in Southeast Asia's consumer electronics sector."
    
    def parse_recipients(self, recipients_string):
        if not recipients_string:
            return []
        cleaned = recipients_string.replace('*', '').replace('\n', ',').replace('\r', ',').replace(';', ',')
        recipients = [email.strip() for email in cleaned.split(',') if email.strip() and '@' in email]
        return recipients
    
    def send_email(self, subject, html_content):
        self.log("\n📧 发送高管简报...")
        
        try:
            recipients = self.parse_recipients(EMAIL_CONFIG["receiver_email"])
            if not recipients:
                self.log("❌ 无有效收件人", "ERROR")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = EMAIL_CONFIG["sender_email"]
            msg['To'] = ', '.join(recipients)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 尝试SSL
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
            server.ehlo()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.send_message(msg)
            server.quit()
            self.log("✅ 邮件发送成功")
            return True
            
        except Exception as e:
            self.log(f"❌ 邮件发送失败: {e}", "ERROR")
            return False
    
    def run(self):
        self.log("\n" + "="*70)
        self.log("🚀 东南亚消费电子智能简报系统")
        self.log("="*70)
        
        start_time = time.time()
        
        # 获取新闻
        news_items = self.fetch_all_news()
        if not news_items:
            self.log("❌ 未找到相关新闻", "ERROR")
            return
        
        # 翻译
        translated = self.translate_chinese_news()
        all_news = news_items + translated
        
        # 分析和分类（会填充 self.tech_news, self.manufacturing_news 等）
        trends = self.analyze_and_categorize(all_news)
        
        # 生成仪表板
        html_content = self.generate_executive_dashboard(all_news, trends)
        
        # 发送邮件
        subject = f"📱 东南亚消费电子简报 - {datetime.now().strftime('%Y-%m-%d')}"
        self.send_email(subject, html_content)
        
        elapsed = time.time() - start_time
        self.log(f"✅ 完成，耗时 {elapsed:.1f} 秒")

# ==================== 主程序 ====================
if __name__ == "__main__":
    dashboard = TechIntelligenceDashboard()
    dashboard.run()
