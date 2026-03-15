#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东南亚消费电子智能简报系统
每日高管简报，覆盖：

1. 制造与投资：消费电子在东南亚的工厂建设
2. 新技术：AR/VR/AI眼镜、可穿戴设备、智能家居、材料科学
3. 行业展会：展览会、贸易展、会议
4. 市场趋势：消费者行为、研究突破、供应商情报

信息来源：中文科技媒体、全球媒体、东南亚新闻、研究机构、材料专业网站
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
    # TechNews 台湾 - 电子制造
    {"url": "https://technews.tw/feed/", "category": "tech", "region": "taiwan", "lang": "zh"},
    {"url": "https://finance.technews.tw/feed/", "category": "finance", "region": "taiwan", "lang": "zh"},
    
    # LEDinside - 显示产业、消费电子组件
    {"url": "https://www.ledinside.cn/rss.xml", "category": "display", "region": "china", "lang": "zh"},
    {"url": "https://www.ledinside.com/news/feed", "category": "display", "region": "global", "lang": "en"},
    
    # Digitimes - 半导体和电子制造
    {"url": "https://www.digitimes.com.tw/rss/rptlist.asp", "category": "semiconductor", "region": "taiwan", "lang": "zh"},
    
    # 中国金融与商业新闻
    {"url": "https://www.21jingji.com/rss/", "category": "business", "region": "china", "lang": "zh"},
    {"url": "http://world.people.com.cn/rss/index.xml", "category": "business", "region": "china", "lang": "zh"},
    {"url": "https://ep.ycwb.com/rss/", "category": "business", "region": "china", "lang": "zh"},
    {"url": "https://epaper.guanhai.com.cn/rss/", "category": "business", "region": "china", "lang": "zh"},
    {"url": "https://news.cnyes.com/rss", "category": "tech", "region": "taiwan", "lang": "zh"},
    
    # ===== 已整合的中文科技资源 =====
    
    # 中国粉体网 - 粉体技术、材料科学
    # 涵盖先进材料、粉末加工、电子制造相关技术
    {"url": "http://www.cnpowder.com.cn/rss/", "category": "materials", "region": "china", "lang": "zh"},
    
    # 寻材问料 - 材料解决方案平台
    # 50万+材料数据库，80万+供应商数据库，连接制造商与材料供应商
    {"url": "http://www.materials.cn/rss/", "category": "materials", "region": "china", "lang": "zh"},
    
    # 新材料在线 - 新材料行业平台
    # 领先的新材料数字平台，覆盖消费电子、半导体、先进制造的材料突破
    {"url": "https://www.xincailiao.com/rss/", "category": "materials", "region": "china", "lang": "zh"},
    
    # 霞光社 - 全球市场与出海洞察
    # 聚焦中国制造走向全球，东南亚市场，跨境电商出海策略
    {"url": "https://xiaguangshe.com/feed/", "category": "business", "region": "china", "lang": "zh"},
    {"url": "https://xiaguangshe.com/en/feed/", "category": "business", "region": "china", "lang": "en"},
    
    # 艾邦高分子 - 高分子与先进材料平台
    # 覆盖阻燃材料、尼龙、薄膜电容器、新能源汽车材料、电子电器应用
    {"url": "https://www.aibang.com/feed/", "category": "materials", "region": "china", "lang": "zh"},
    {"url": "https://www.aibang.com/news/feed/", "category": "industry", "region": "china", "lang": "zh"},
    
    # 艾邦旗下细分网站
    {"url": "https://www.aibang.com/category/manufacturing/feed/", "category": "manufacturing", "region": "china", "lang": "zh"},
    {"url": "https://www.aibang.com/category/materials/feed/", "category": "materials", "region": "china", "lang": "zh"},
    
    # China Daily - 中国科技突破的官方英文报道
    {"url": "https://www.chinadaily.com.cn/rss/business_rss.xml", "category": "business", "region": "china", "lang": "en"},
    {"url": "https://www.chinadailyhk.com/rss", "category": "tech", "region": "china", "lang": "en"},
    
    # 中国科学院 - 前沿材料研究
    {"url": "https://english.cas.cn/news/rss/", "category": "research", "region": "china", "lang": "en"},
    {"url": "http://www.cas.cn/rss/", "category": "research", "region": "china", "lang": "zh"},
    
    # 复旦大学研究 - 纤维芯片、脑机接口
    {"url": "https://news.fudan.edu.cn/rss.xml", "category": "research", "region": "china", "lang": "zh"},
    
    # GfK中国 - 消费电子市场研究
    {"url": "https://www.gfk.com/insights/rss", "category": "market", "region": "global", "lang": "en"},
    
    # 证券时报 - 消费电子产业分析
    {"url": "https://stcn.com/rss/finance.xml", "category": "finance", "region": "china", "lang": "zh"},
    
    # 雪球 - 消费电子投资社区
    {"url": "https://xueqiu.com/rss/", "category": "finance", "region": "china", "lang": "zh"},
    
    # 国家科技技术创新中心 - 研究突破
    {"url": "https://en.ncsti.gov.cn/Latest/rss/", "category": "research", "region": "china", "lang": "en"},
    
    # ARY News - 技术突破报道
    {"url": "https://arynews.tv/category/technology/feed/", "category": "tech", "region": "global", "lang": "en"},
    
    # 京东研究 - 消费电子趋势数据
    {"url": "https://ir.jd.com/rss", "category": "market", "region": "china", "lang": "en"},
    
    # Rokid - AI眼镜制造商新闻
    {"url": "https://www.rokid.com/blog/feed/", "category": "wearables", "region": "china", "lang": "en"},
    
    # COLMO - AI智能家电
    {"url": "https://www.colmo.com.cn/news/feed/", "category": "appliances", "region": "china", "lang": "zh"},
    
    # 36Kr - 中国科技媒体
    {"url": "https://36kr.com/feed", "category": "tech", "region": "china", "lang": "zh"},
    {"url": "https://36kr.com/feed/english", "category": "tech", "region": "china", "lang": "en"},
    
    # KrASIA - 中国和东南亚科技英文报道
    {"url": "https://www.kr-asia.com/feed", "category": "tech", "region": "asia", "lang": "en"},
    
    # Jing Daily - 中国科技消费趋势
    {"url": "https://jingdaily.com/category/tech/feed/", "category": "trends", "region": "china", "lang": "en"},
    
    # ===== 全球科技媒体 =====
    {"url": "https://techcrunch.com/feed/", "category": "tech", "region": "global", "lang": "en"},
    {"url": "https://www.theverge.com/rss/index.xml", "category": "tech", "region": "global", "lang": "en"},
    {"url": "https://arstechnica.com/feed/", "category": "tech", "region": "global", "lang": "en"},
    {"url": "https://www.engadget.com/rss.xml", "category": "consumer", "region": "global", "lang": "en"},
    {"url": "https://www.gsmarena.com/rss-news-reviews.php", "category": "mobile", "region": "global", "lang": "en"},
    {"url": "https://www.androidauthority.com/feed/", "category": "mobile", "region": "global", "lang": "en"},
    
    # ===== 东南亚新闻 =====
    # 越南
    {"url": "https://www.vietnam-briefing.com/news/feed/", "category": "business", "region": "vietnam", "lang": "en"},
    {"url": "https://e.vnexpress.net/rss/business.rss", "category": "business", "region": "vietnam", "lang": "en"},
    
    # 泰国
    {"url": "https://www.bangkokpost.com/rss/data/business.xml", "category": "business", "region": "thailand", "lang": "en"},
    {"url": "https://thailand-briefing.com/news/feed/", "category": "business", "region": "thailand", "lang": "en"},
    
    # 马来西亚
    {"url": "https://www.thestar.com.my/rss/business", "category": "business", "region": "malaysia", "lang": "en"},
    {"url": "https://www.nst.com.my/rss/business", "category": "business", "region": "malaysia", "lang": "en"},
    
    # 新加坡
    {"url": "https://www.straitstimes.com/news/business/rss.xml", "category": "business", "region": "singapore", "lang": "en"},
    {"url": "https://sbr.com.sg/rss.xml", "category": "business", "region": "singapore", "lang": "en"},
    
    # 印度尼西亚
    {"url": "https://indonesia-briefing.com/news/feed/", "category": "business", "region": "indonesia", "lang": "en"},
    {"url": "https://www.thejakartapost.com/rss/business.xml", "category": "business", "region": "indonesia", "lang": "en"},
    
    # 菲律宾
    {"url": "https://www.philstar.com/rss/business", "category": "business", "region": "philippines", "lang": "en"},
    
    # ===== 行业出版物 =====
    {"url": "https://semiengineering.com/feed/", "category": "semiconductor", "region": "global", "lang": "en"},
    {"url": "https://www.electronicproducts.com/feed/", "category": "components", "region": "global", "lang": "en"},
    {"url": "https://www.displaydaily.com/feed", "category": "display", "region": "global", "lang": "en"},
]

# ==================== 全面的关键词 ====================

# 东南亚地点
SEA_LOCATIONS = [
    # 国家
    'vietnam', '越南', 'thailand', '泰国', 'indonesia', '印尼', '印度尼西亚',
    'malaysia', '马来西亚', 'singapore', '新加坡', 'philippines', '菲律宾',
    'myanmar', '缅甸', 'cambodia', '柬埔寨', 'laos', '老挝', 'brunei', '文莱',
    'asean', '东盟', 'southeast asia', '东南亚',
    
    # 越南地点
    'bac ninh', '北宁', 'thai nguyen', '太原', 'ho chi minh', '胡志明',
    'hanoi', '河内', 'haiphong', '海防', 'dong nai', '同奈',
    'binh duong', '平阳', 'long an', '隆安', 'bac giang', '北江',
    'vinh phuc', '永福',
    
    # 泰国地点
    'bangkok', '曼谷', 'chon buri', '春武里', 'chonburi', 'rayong', '罗勇',
    'ayutthaya', '大城', 'pathum thani', '巴吞他尼', 'samut prakan', '北榄',
    'lamphun', '南奔', 'prachin buri', '巴真', 'amata', '安美德',
    'hemaraj', '赫马拉', 'eastern seaboard', '东部经济走廊', 'eec',
    
    # 印度尼西亚地点
    'jakarta', '雅加达', 'west java', '西爪哇', 'central java', '中爪哇',
    'east java', '东爪哇', 'batam', '巴淡', 'banten', '万丹',
    'bekasi', '勿加泗', 'karawang', '加拉璜', 'tangerang', '唐格朗',
    
    # 马来西亚地点
    'kuala lumpur', '吉隆坡', 'penang', '槟城', 'selangor', '雪兰莪',
    'johor', '柔佛', 'melaka', '马六甲', 'kedah', '吉打', 'kulim', '居林',
    
    # 新加坡
    'singapore', '新加坡',
    
    # 菲律宾
    'manila', '马尼拉', 'cebu', '宿务'
]

# 消费电子产品与技术
CONSUMER_ELECTRONICS = [
    # ===== 白色家电 / 家用电器 =====
    'refrigerator', 'fridge', '冷柜', '冰箱', 'freezer', '冰柜',
    'washing machine', 'washer', '洗衣机',
    'air conditioner', 'ac', '空调',
    'microwave', '微波炉', 'oven', '烤箱',
    'dishwasher', '洗碗机',
    'water heater', '热水器',
    'vacuum', '扫地机器人', '吸尘器',
    
    # ===== 厨房电器 =====
    'kitchen appliance', '厨房电器',
    'cooktop', '灶具', 'range hood', '抽油烟机',
    'toaster', '烤面包机', 'coffee maker', '咖啡机',
    'food processor', '食品加工机', 'rice cooker', '电饭煲',
    
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
    
    # ===== 制造 =====
    'factory', 'plant', 'manufacturing', 'production', 'assembly', '生产线', '量产',
    'facility', '新建工厂', '投产', '开工', '奠基', 'investment', 'invest',
    'supplier', '供应链', 'vendor', '供应商', 'localization', '本地化',
    
    # ===== 研究与创新 =====
    'breakthrough', '突破', 'innovation', '创新', 'research', '研究',
    'prototype', '原型', 'commercialization', '商业化', 'mass production', '量产',
    
    # ===== 展会 =====
    'exhibition', 'expo', 'conference', 'trade show', '展', 'awe', 'ces', 'mwc', 'ifa'
]

# ===== 新材料与新兴技术关键词 =====
EMERGING_TECH_KEYWORDS = [
    # 材料科学（来自新资源）
    '粉体', 'powder', '颗粒', 'particle', '纳米', 'nano',
    '涂层', 'coating', '薄膜', 'thin film', '沉积', 'deposition',
    '材料解决方案', 'material solution', '供应商数据库', 'supplier database',
    '物性', 'material properties', '性能参数', 'specifications',
    '选材', 'material selection', '替代材料', 'substitute material',
    '新材料', 'new material', '先进材料', 'advanced material',
    '复合材料', 'composite', '高分子', 'polymer',
    '金属材料', 'metal', '陶瓷材料', 'ceramic',
    '材料突破', 'material breakthrough', '材料创新', 'material innovation',
    
    # 出海与全球化（来自霞光社）
    '出海', 'going global', '全球化', 'globalization',
    '东南亚市场', 'Southeast Asia market', '越南建厂', 'Vietnam factory',
    '泰国投资', 'Thailand investment', '印尼制造', 'Indonesia manufacturing',
    '跨境电商', 'cross-border e-commerce', '海外扩张', 'overseas expansion',
    
    # 高分子与电容器（来自艾邦）
    '阻燃', 'flame retardant', '阻燃材料', 'flame retardant material',
    '尼龙', 'nylon', '聚酰胺', 'polyamide',
    '薄膜电容', 'film capacitor', '电容器', 'capacitor',
    '电容膜', 'capacitor film',
    '改性塑料', 'modified plastic', '工程塑料', 'engineering plastic',
    '新能源汽车材料', 'EV materials', '电池材料', 'battery materials',
    
    # 消费电子材料
    '智能家居材料', 'smart home materials', '家电材料', 'appliance materials',
    '消费电子材料', 'consumer electronics materials', '手机材料', 'phone materials',
    '可穿戴材料', 'wearable materials', 'AR/VR材料', 'AR/VR materials',
    
    # 热电与能源材料
    'thermoelectric', '热电', 'body heat', '体温发电',
    'fiber chip', '纤维芯片', 'electronic fiber', '电子纤维',
    'flexible electronics', '柔性电子', 'wearable tech', '可穿戴技术',
    'conductive', '导电',
    
    # AI集成
    'ai glasses', 'AI眼镜', 'smart glasses', '智能眼镜',
    'ai assistant', 'AI助手', 'ai butler', 'AI管家',
    'voice command', '语音指令',
    
    # 智能家居
    'smart home', '智能家居', 'whole-home', '全屋智能',
    'proactive intelligence', '主动智能', 'scene-based', '场景化',
    'smart appliance', '智能家电', 'ai appliance', 'AI家电',
    
    # 显示技术
    'microled', 'oled', 'display', '屏幕',
    'foldable', '折叠屏', 'flexible display', '柔性屏',
    
    # 新兴产品
    'digital nostalgia', '数码复古', 'ccd camera', 'CCD相机',
    'dumb phone', '功能机', 'flip phone', '翻盖手机',
    'wired headphones', '有线耳机', 'retro tech', '复古科技',
    'brain-computer', '脑机接口', 'bci', '神经接口',
    
    # 研究突破
    'breakthrough', '突破', 'innovation', '创新',
    'prototype', '原型', 'commercialization', '商业化',
    'scalable', '可扩展',
    
    # 市场趋势
    'ai consumption', 'AI消费', 'smart living', '智慧生活',
    'consumer upgrade', '消费升级', 'premiumization', '高端化',
    'export', '出口', 'overseas expansion', '出海',
]

# 合并所有关键词
ALL_KEYWORDS = CONSUMER_ELECTRONICS + EMERGING_TECH_KEYWORDS

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
        """检查新闻是否关于东南亚 AND 消费电子"""
        text = (title + ' ' + summary).lower()
        
        # 必须提及东南亚地点
        is_sea = any(loc.lower() in text for loc in SEA_LOCATIONS)
        if not is_sea:
            return False
        
        # 检查消费电子或新兴技术关键词
        is_ce = any(kw.lower() in text for kw in ALL_KEYWORDS)
        
        # 为调试记录匹配
        if is_ce:
            matched_loc = next((loc for loc in SEA_LOCATIONS if loc.lower() in text), "unknown")
            matched_keyword = next((kw for kw in ALL_KEYWORDS if kw.lower() in text), "unknown")
            self.log(f"      ✓ SEA: {matched_loc} | 关键词: {matched_keyword}")
        
        return is_ce
    
    def fetch_all_news(self):
        """从所有RSS源获取新闻"""
        self.log("📡 正在从50+源获取新闻，包括中文科技媒体...")
        feedparser.USER_AGENT = "Mozilla/5.0 (compatible; Executive Dashboard)"
        
        for feed in RSS_FEEDS:
            try:
                self.log(f"  获取: {feed['url']}")
                parsed = feedparser.parse(feed['url'])
                
                for entry in parsed.entries[:15]:
                    title = entry.get('title', 'No title')
                    summary = entry.get('summary', '') or entry.get('description', '')
                    link = entry.get('link', '')
                    
                    # 快速相关度检查
                    if not self.is_relevant_news(title, summary):
                        continue
                    
                    # 提取完整内容
                    content = ''
                    if 'content' in entry and entry['content']:
                        content = entry['content'][0].get('value', '')[:1000]
                    
                    # 获取发布日期
                    published = entry.get('published', '')
                    if not published:
                        published = entry.get('updated', datetime.now().strftime('%Y-%m-%d'))
                    
                    # 提取来源
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
                    
                    # 按语言分离
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
        """将中文新闻翻译成英文，专注于技术准确性"""
        if not self.chinese_news:
            return []
        
        self.log("🔄 将中文科技新闻翻译成英文...")
        translated = []
        
        # 扩展的技术指标，用于更好的检测
        technical_indicators = [
            # 研究术语
            '研究', '研发', '科研', '实验室', '突破', '发现', '创新',
            '材料', '芯片', '半导体', '电路', '纤维', '聚合物',
            '技术', '工艺', '制备', '合成', '性能', '效率',
            
            # 材料科学特定
            '粉体', '粉末', '颗粒', '纳米', '涂层', '薄膜', '沉积',
            '高分子', '复合材料', '金属材料', '陶瓷',
            '阻燃', '尼龙', '聚酰胺', '电容器', '电容膜',
            '改性', '工程塑料', '特种材料', '功能材料',
            '新材料', '先进材料',
            
            # 英文术语
            'research', 'development', 'breakthrough', 'innovation',
            'material', 'chip', 'semiconductor', 'circuit', 'fiber',
            'technology', 'process', 'synthesis', 'performance',
            
            # 特定技术
            '热电', '体温发电', '纤维芯片', '电子纤维', '柔性电子',
            '脑机接口', '神经接口', 'microled', 'oled', '量子点',
            'thermoelectric', 'fiber chip', 'flexible electronics',
            'brain-computer', 'bci', 'neural interface'
        ]
        
        # 技术术语翻译词典
        tech_term_dictionary = {
            '热电材料': 'thermoelectric materials',
            '体温发电': 'body heat harvesting',
            '纤维芯片': 'fiber chip',
            '电子纤维': 'electronic fiber',
            '柔性电子': 'flexible electronics',
            '可穿戴技术': 'wearable technology',
            '脑机接口': 'brain-computer interface',
            '神经接口': 'neural interface',
            '量子点': 'quantum dots',
            'microled': 'microLED',
            'oled': 'OLED',
            '半导体': 'semiconductor',
            '聚合物': 'polymer',
            '导电': 'conductive',
            '制备': 'fabrication',
            '合成': 'synthesis',
            '性能': 'performance characteristics',
            '效率': 'efficiency',
            
            # 新材料术语
            '粉体': 'powder materials',
            '纳米材料': 'nanomaterials',
            '涂层技术': 'coating technology',
            '薄膜沉积': 'thin film deposition',
            '阻燃材料': 'flame retardant materials',
            '改性塑料': 'modified plastics',
            '工程塑料': 'engineering plastics',
            '高分子材料': 'polymer materials',
            '复合材料': 'composite materials',
            '薄膜电容器': 'film capacitors',
            '电容膜': 'capacitor film',
            '聚酰胺': 'polyamide',
            '尼龙': 'nylon',
            '新材料': 'new materials',
            '先进材料': 'advanced materials',
        }
        
        for news in self.chinese_news[:25]:  # 增加到25篇文章
            try:
                # 合并标题和摘要进行分析
                full_text = news['title'] + ' ' + news['summary']
                text_lower = full_text.lower()
                
                # 检测是否为研究/技术内容
                is_technical = any(term in full_text for term in technical_indicators)
                
                # 检查特定突破指标
                is_breakthrough = any(term in full_text for term in ['突破', '首次', '世界领先', '重大', '里程碑', '首创'])
                
                # 检查特定技术领域
                tech_areas = []
                if '热电' in full_text or 'thermoelectric' in text_lower:
                    tech_areas.append('thermoelectric materials')
                if '纤维芯片' in full_text or 'fiber chip' in text_lower:
                    tech_areas.append('fiber chip technology')
                if '脑机' in full_text or 'brain' in text_lower:
                    tech_areas.append('brain-computer interface')
                if '柔性' in full_text or 'flexible' in text_lower:
                    tech_areas.append('flexible electronics')
                if 'ai' in text_lower or '人工智能' in full_text:
                    tech_areas.append('artificial intelligence')
                if 'ar' in text_lower or 'vr' in text_lower or '眼镜' in full_text:
                    tech_areas.append('AR/VR/smart glasses')
                if '芯片' in full_text or 'chip' in text_lower:
                    tech_areas.append('semiconductor/chip technology')
                if '粉体' in full_text or 'powder' in text_lower:
                    tech_areas.append('powder technology')
                if '阻燃' in full_text or 'flame retardant' in text_lower:
                    tech_areas.append('flame retardant materials')
                if '尼龙' in full_text or 'nylon' in text_lower:
                    tech_areas.append('nylon/polyamide')
                if '薄膜电容' in full_text or 'film capacitor' in text_lower:
                    tech_areas.append('film capacitors')
                
                # 准备增强提示，包含词典上下文
                if is_technical:
                    # 在提示中包含技术术语词典以确保准确性
                    dict_context = "\n".join([f"- {chinese}: {english}" for chinese, english in tech_term_dictionary.items()])
                    
                    prompt = f"""You are a technical translator specializing in consumer electronics and materials science research. 
Translate this Chinese research/technology news to English with precise technical terminology.

TECHNICAL TERM REFERENCE:
{dict_context}

Original Chinese:
Title: {news['title']}
Summary: {news['summary'][:600]}

TECHNICAL CONTEXT:
- Technology areas: {', '.join(tech_areas) if tech_areas else 'General technology'}
- {'This appears to be a MAJOR BREAKTHROUGH announcement' if is_breakthrough else 'This is technical content'}

TRANSLATION REQUIREMENTS:
1. Keep ALL technical terms accurate - use the reference dictionary where applicable
2. Preserve numerical data, measurements, and scientific units exactly
3. Maintain company names (e.g., 京东方 → BOE, 华为 → Huawei) and researcher names
4. Use formal technical English suitable for an executive briefing
5. For breakthrough research, emphasize the significance and potential applications
6. If specific metrics (efficiency, performance, etc.) are mentioned, ensure they're precisely translated

Provide:
- First line: Title (concise, professional)
- Second line: [TECH AREA: {', '.join(tech_areas) if tech_areas else 'Technology'}]
- Then a detailed summary paragraph (3-5 sentences) covering: what was achieved, how it works (simplified), and potential applications."""
                else:
                    prompt = f"""You are a business translator specializing in consumer electronics industry news. 
Translate this Chinese business/industry news to English accurately.

Original Chinese:
Title: {news['title']}
Summary: {news['summary'][:450]}

TRANSLATION REQUIREMENTS:
- Keep all company names accurate (海尔→Haier, 美的→Midea, 京东方→BOE, 富士康→Foxconn)
- Preserve investment figures, production capacities, and timelines exactly
- Maintain product names and specifications
- Keep location names accurate (泰国→Thailand, 越南→Vietnam, etc.)
- Use professional business English suitable for an executive briefing

Provide:
- First line: Title
- Then a summary paragraph covering: what happened, who is involved, key numbers, and implications."""
                
                # 添加超时和重试逻辑
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        response = openai.ChatCompletion.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.1,
                            max_tokens=800,
                            timeout=30
                        )
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        self.log(f"  ⚠️ 重试 {attempt + 1} 次翻译", "WARNING")
                        time.sleep(2)
                
                translation = response.choices[0].message.content
                
                # 解析响应
                lines = translation.split('\n', 2)
                news['title_en'] = lines[0].strip() if lines else "Translation"
                
                # 如果存在技术领域行，提取它
                if len(lines) > 1 and lines[1].startswith('[TECH AREA:'):
                    news['tech_area'] = lines[1].replace('[TECH AREA:', '').replace(']', '').strip()
                    news['summary_en'] = lines[2].strip() if len(lines) > 2 else translation
                else:
                    news['summary_en'] = lines[1].strip() if len(lines) > 1 else translation
                
                # 标记技术内容以便特殊处理
                if is_technical:
                    news['is_technical'] = True
                    news['is_breakthrough'] = is_breakthrough
                    news['tech_areas'] = tech_areas
                    
                    # 带技术指标记录
                    tech_indicators = f"[{'突破' if is_breakthrough else '技术'}]"
                    areas = f"({', '.join(tech_areas[:2])})" if tech_areas else ""
                    self.log(f"  🔬 {tech_indicators} {areas}: {news['title'][:40]}...")
                else:
                    self.log(f"  ✅ 商业: {news['title'][:50]}...")
                
                translated.append(news)
                
            except Exception as e:
                self.log(f"  ⚠️ 翻译失败 '{news['title'][:30]}...': {e}", "WARNING")
                # 仍然包含原文，带基本翻译
                news['title_en'] = f"[翻译失败] {news['title']}"
                news['summary_en'] = f"原文中文: {news['summary'][:200]}..."
                news['is_technical'] = False
                translated.append(news)
                continue
        
        # 统计摘要
        tech_count = sum(1 for n in translated if n.get('is_technical', False))
        breakthrough_count = sum(1 for n in translated if n.get('is_breakthrough', False))
        
        self.log(f"✅ 翻译了 {len(translated)} 篇文章:")
        self.log(f"   - 技术内容: {tech_count} ({breakthrough_count} 项突破)")
        self.log(f"   - 商业/行业: {len(translated) - tech_count}")
        
        return translated
    
    def analyze_trends(self, news_items):
    """分析趋势并提取关键洞察，同时保存相关新闻"""
    self.log("📊 分析消费电子趋势...")
    
    companies = []
    locations = []
    products = []
    technologies = []
    investments = []
    
    # 用于存储与每个热点相关的新闻
    location_news = {}  # 键：地点，值：新闻列表
    tech_news_map = {}  # 键：技术，值：新闻列表
    company_news = {}   # 键：公司，值：新闻列表
    
    for item in news_items:
        text = f"{item.get('title_en', item['title'])} {item.get('summary_en', item.get('summary', ''))}".lower()
        
        # 提取公司
        for company in ['samsung', 'haier', '海尔', 'midea', '美的', 'xiaomi', 'oppo', 
                       'foxconn', '富士康', 'rokid', 'htc', 'lg', 'sony', 'boe', '京东方',
                       'tcl', 'hisense', '海信', 'gree', '格力']:
            if company.lower() in text:
                company_clean = company.replace('海尔', 'Haier').replace('美的', 'Midea').replace('富士康', 'Foxconn').replace('京东方', 'BOE')
                companies.append(company_clean)
                
                # 保存公司相关新闻
                if company_clean not in company_news:
                    company_news[company_clean] = []
                if item not in company_news[company_clean]:
                    company_news[company_clean].append(item)
        
        # 提取地点
        for loc in SEA_LOCATIONS:
            if loc.lower() in text:
                loc_title = loc.title()
                locations.append(loc_title)
                
                # 保存地点相关新闻
                if loc_title not in location_news:
                    location_news[loc_title] = []
                if item not in location_news[loc_title]:
                    location_news[loc_title].append(item)
        
        # 提取产品
        for prod in ['smartphone', 'glasses', 'wearable', 'refrigerator', 'fridge', 
                    'air conditioner', 'tv', 'watch', '扫地机器人', 'vacuum',
                    'washing machine', 'microwave', 'oven', 'capacitor', '电容器']:
            if prod.lower() in text:
                products.append(prod.title())
        
        # 提取新兴技术
        tech_list = [
            ('ai', 'AI'), ('人工智能', 'AI'),
            ('ar', 'AR'), ('增强现实', 'AR'),
            ('vr', 'VR'), ('虚拟现实', 'VR'),
            ('thermoelectric', '热电材料'), ('热电', '热电材料'),
            ('fiber chip', '纤维芯片'), ('纤维芯片', '纤维芯片'),
            ('flexible', '柔性电子'), ('柔性', '柔性电子'),
            ('microled', 'MicroLED'), ('oled', 'OLED'),
            ('brain-computer', '脑机接口'), ('脑机', '脑机接口'),
            ('powder', '粉体技术'), ('粉体', '粉体技术'),
            ('flame retardant', '阻燃材料'), ('阻燃', '阻燃材料'),
            ('nylon', '尼龙'), ('尼龙', '尼龙'),
            ('film capacitor', '薄膜电容'), ('薄膜电容', '薄膜电容')
        ]
        
        for tech_key, tech_display in tech_list:
            if tech_key.lower() in text:
                technologies.append(tech_display)
                
                # 保存技术相关新闻
                if tech_display not in tech_news_map:
                    tech_news_map[tech_display] = []
                if item not in tech_news_map[tech_display]:
                    tech_news_map[tech_display].append(item)
        
        # 提取投资
        if 'invest' in text or '$' in text or 'billion' in text or 'million' in text:
            investments.append('investment mentioned')
    
    return {
        'top_companies': Counter(companies).most_common(10),
        'top_locations': Counter(locations).most_common(5),
        'top_products': Counter(products).most_common(5),
        'top_technologies': Counter(technologies).most_common(5),
        'total_investments': len(investments),
        'location_news': location_news,      # 新增：地点相关新闻
        'tech_news_map': tech_news_map,      # 新增：技术相关新闻
        'company_news': company_news         # 新增：公司相关新闻
    }

    def _create_trends_section(self, trends):
    """创建趋势部分，显示统计数据和具体新闻"""
    html = '<div class="trends-section">'
    
    # 热门地点（制造热点）
    html += '<div class="trends-grid">'
    html += '<div class="trend-card" style="grid-column: span 3;">'
    html += '<h3>📍 制造热点 - 东南亚建厂动态</h3>'
    html += '<div style="display: flex; flex-wrap: wrap; gap: 20px; margin-top: 20px;">'
    
    for location, count in trends['top_locations'][:5]:
        location_key = location.title()
        related_news = trends.get('location_news', {}).get(location_key, [])
        
        html += f"""
        <div style="flex: 1; min-width: 200px; background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <h4 style="color: #0a1929; margin-bottom: 10px; border-bottom: 2px solid #ffd700; padding-bottom: 5px;">
                {location_key} <span style="color: #0066cc;">({count})</span>
            </h4>
            <ul style="list-style: none; padding: 0;">
        """
        
        # 显示最多3条相关新闻
        for news in related_news[:3]:
            title = news.get('title_en', news['title'])[:50]
            if len(title) >= 50:
                title += '...'
            html += f"""
            <li style="margin-bottom: 8px; font-size: 0.9em;">
                <a href="{news['link']}" style="color: #0066cc; text-decoration: none;">📄 {title}</a>
                <span style="color: #666; font-size: 0.8em; display: block;">{news['source']}</span>
            </li>
            """
        
        if len(related_news) > 3:
            html += f'<li style="color: #666; font-size: 0.85em;">... 还有 {len(related_news)-3} 条新闻</li>'
        
        html += '</ul></div>'
    
    html += '</div></div></div>'  # 结束制造热点部分
    
    # 新兴技术
    html += '<div class="trends-grid" style="margin-top: 30px;">'
    html += '<div class="trend-card" style="grid-column: span 3;">'
    html += '<h3>🔬 新兴技术 - 最新技术动态</h3>'
    html += '<div style="display: flex; flex-wrap: wrap; gap: 20px; margin-top: 20px;">'
    
    for tech, count in trends['top_technologies'][:5]:
        tech_key = tech
        related_news = trends.get('tech_news_map', {}).get(tech_key, [])
        
        html += f"""
        <div style="flex: 1; min-width: 200px; background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <h4 style="color: #0a1929; margin-bottom: 10px; border-bottom: 2px solid #8b5cf6; padding-bottom: 5px;">
                {tech_key} <span style="color: #0066cc;">({count})</span>
            </h4>
            <ul style="list-style: none; padding: 0;">
        """
        
        # 显示最多3条相关新闻
        for news in related_news[:3]:
            title = news.get('title_en', news['title'])[:50]
            if len(title) >= 50:
                title += '...'
            html += f"""
            <li style="margin-bottom: 8px; font-size: 0.9em;">
                <a href="{news['link']}" style="color: #8b5cf6; text-decoration: none;">🔬 {title}</a>
                <span style="color: #666; font-size: 0.8em; display: block;">{news['source']}</span>
            </li>
            """
        
        if len(related_news) > 3:
            html += f'<li style="color: #666; font-size: 0.85em;">... 还有 {len(related_news)-3} 条新闻</li>'
        
        html += '</ul></div>'
    
    html += '</div></div></div>'  # 结束新兴技术部分
    
    # 热门公司
    if trends['top_companies']:
        html += '<div class="trends-grid" style="margin-top: 30px;">'
        html += '<div class="trend-card" style="grid-column: span 3;">'
        html += '<h3>🏢 热门公司 - 最新动态</h3>'
        html += '<div style="display: flex; flex-wrap: wrap; gap: 20px; margin-top: 20px;">'
        
        for company, count in trends['top_companies'][:4]:
            related_news = trends.get('company_news', {}).get(company, [])
            
            html += f"""
            <div style="flex: 1; min-width: 200px; background: #f8f9fa; padding: 15px; border-radius: 10px;">
                <h4 style="color: #0a1929; margin-bottom: 10px; border-bottom: 2px solid #10b981; padding-bottom: 5px;">
                    {company} <span style="color: #0066cc;">({count})</span>
                </h4>
                <ul style="list-style: none; padding: 0;">
            """
            
            for news in related_news[:2]:
                title = news.get('title_en', news['title'])[:40]
                if len(title) >= 40:
                    title += '...'
                html += f"""
                <li style="margin-bottom: 8px; font-size: 0.9em;">
                    <a href="{news['link']}" style="color: #10b981; text-decoration: none;">📊 {title}</a>
                </li>
                """
            
            html += '</ul></div>'
        
        html += '</div></div></div>'
    
    html += '</div>'
    return html
    
    def generate_executive_dashboard(self, news_items, trends):
        """生成专业HTML仪表板"""
        self.log("🎨 创建高管仪表板...")
        
        date = datetime.now().strftime('%B %d, %Y')
        
        # 分类新闻
        factory_news = []
        tech_news = []
        exhibition_news = []
        research_news = []
        
        for n in news_items:
            text = (n.get('title_en', n['title']) + ' ' + n.get('summary_en', n.get('summary', ''))).lower()
            
            # 首先检查研究/突破
            if n.get('is_technical', False) or any(term in text for term in ['research', 'breakthrough', 'study', 'scientists', 'researchers']):
                research_news.append(n)
            elif any(k in text for k in ['factory', 'plant', 'manufacturing', 'production', 'facility', 'assembly', '新建工厂', '投产']):
                factory_news.append(n)
            elif any(k in text for k in ['technology', 'innovation', 'ar', 'vr', 'ai', 'chip', 'display', 'battery', 'sensor', 'glasses', '材料']):
                tech_news.append(n)
            elif any(k in text for k in ['exhibition', 'expo', 'conference', 'trade show', '展', 'awe', 'ces', 'mwc']):
                exhibition_news.append(n)
        
        self.log(f"   分类: {len(research_news)} 研究, {len(factory_news)} 工厂, {len(tech_news)} 技术, {len(exhibition_news)} 展会")
        
        # 创建各个部分
        research_section = self._create_research_section(research_news[:6])
        factory_section = self._create_factory_section(factory_news[:8])
        tech_section = self._create_tech_section(tech_news)
        exhibition_section = self._create_exhibition_section(exhibition_news[:6])
        trends_section = self._create_trends_section(trends)
        exec_summary = self._generate_executive_summary(news_items, trends, factory_news, tech_news, research_news)
        
        # 构建HTML（为简洁起见，保留现有的HTML模板，但更新标题以反映新材料覆盖）
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEA消费电子智能简报 - {date}</title>
    <style>
        /* 保留之前的所有CSS样式 */
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
        
        .research-badge {{
            background: #8b5cf6;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            display: inline-block;
            margin-right: 8px;
        }}
        
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
        <div class="header">
            <h1><strong>东南亚消费电子</strong> 智能简报</h1>
            <div class="date">{date}</div>
            <div class="meta">
                <span>📊 分析文章: {len(news_items)}</span>
                <span>🌏 聚焦: 东南亚</span>
                <span>📱 消费电子 + 新材料</span>
                <span>⏰ {datetime.now().strftime('%H:%M:%S')}</span>
            </div>
        </div>
        
        <div class="summary-card">
            <h2>📋 高管摘要</h2>
            <p>{exec_summary}</p>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-icon">🔬</div>
                <div class="kpi-label">研究突破</div>
                <div class="kpi-value">{len(research_news)}</div>
                <div class="kpi-trend">材料、芯片、AI</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🏭</div>
                <div class="kpi-label">制造项目</div>
                <div class="kpi-value">{len(factory_news)}</div>
                <div class="kpi-trend">东南亚建厂</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">💡</div>
                <div class="kpi-label">新技术</div>
                <div class="kpi-value">{len(tech_news)}</div>
                <div class="kpi-trend">AR/VR/AI/可穿戴</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">🎪</div>
                <div class="kpi-label">行业活动</div>
                <div class="kpi-value">{len(exhibition_news)}</div>
                <div class="kpi-trend">即将举办的展会</div>
            </div>
        </div>
        
        <!-- 研究与突破部分 -->
        <div class="section-header">
            <h2>🔬 研究突破与技术前沿</h2>
        </div>
        {research_section}
        
        <div class="section-header">
            <h2>🏭 制造与投资</h2>
        </div>
        {factory_section}
        
        <div class="section-header">
            <h2>📱 新技术与产品</h2>
        </div>
        {tech_section}
        
        <div class="section-header">
            <h2>🎪 展会与活动</h2>
        </div>
        {exhibition_section}
        
        <div class="section-header">
            <h2>📈 市场情报</h2>
        </div>
        {trends_section}
        
        <div class="footer">
            <p>东南亚消费电子制造情报 • 涵盖新材料、粉体技术、高分子材料</p>
            <p>信息来源: 中国粉体网, 寻材问料, 新材料在线, 霞光社, 艾邦高分子, 中国科学院, 复旦大学, 36Kr, KrASIA</p>
            <div class="disclaimer">
                © 2026 东南亚消费电子智能简报 • 仅供高管审阅 • 由DeepSeek AI生成
            </div>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _create_research_section(self, research_news):
        """创建研究突破部分，增强技术细节显示"""
        if not research_news:
            return '<p style="color:#666; text-align:center; padding:30px;">今日无研究突破。</p>'
        
        # 区分突破性研究与普通研究
        breakthroughs = [n for n in research_news if n.get('is_breakthrough', False)]
        regular_research = [n for n in research_news if not n.get('is_breakthrough', False)]
        
        html = '<div class="manufacturing-grid">'
        
        # 先展示突破性研究，使用特殊样式
        for item in breakthroughs:
            title_safe = html_module.escape(item.get('title_en', item['title'])[:80])
            summary_safe = html_module.escape(item.get('summary_en', item.get('summary', ''))[:250])
            tech_areas = item.get('tech_areas', [])
            
            # 创建技术领域标签
            area_badges = ''.join([f'<span class="research-badge" style="background: #8b5cf6;">{area}</span>' for area in tech_areas[:3]])
            
            html += f"""
            <div class="manufacturing-card" style="background: linear-gradient(135deg, #f0e7ff 0%, #ffffff 100%); border-left: 4px solid #8b5cf6;">
                <div class="company-header">
                    <div class="company-logo" style="background: #8b5cf6; color: white;">🏆</div>
                    <div class="company-info">
                        <h3 style="color: #8b5cf6;">{title_safe}</h3>
                        <div class="company-meta">{item['source']} • {item.get('region', '中国').title()}</div>
                    </div>
                </div>
                <div style="margin-bottom: 10px;">
                    {area_badges}
                    <span class="research-badge" style="background: #ffd700; color: #0a1929;">⭐ 突破性研究</span>
                </div>
                <div class="detail-row">
                    <div class="detail-value">{summary_safe}...</div>
                </div>
                <div style="margin-top: 15px;">
                    <a href="{item['link']}" style="color: #8b5cf6; font-weight: 500;">🔗 阅读研究 →</a>
                </div>
            </div>
            """
        
        # 展示普通研究
        for item in regular_research:
            title_safe = html_module.escape(item.get('title_en', item['title'])[:80])
            summary_safe = html_module.escape(item.get('summary_en', item.get('summary', ''))[:200])
            tech_areas = item.get('tech_areas', [])
            
            # 确定研究类型以显示图标
            research_type = "研究"
            icon = "🔬"
            color = "#8b5cf6"
            
            if 'thermoelectric' in title_safe.lower() or any('热电' in area for area in tech_areas):
                research_type = "热电材料"
                icon = "⚡"
            elif 'fiber chip' in title_safe.lower() or '纤维' in title_safe.lower():
                research_type = "纤维芯片"
                icon = "🧵"
            elif 'brain' in title_safe.lower() or '脑机' in title_safe.lower():
                research_type = "脑机接口"
                icon = "🧠"
            elif 'flexible' in title_safe.lower() or '柔性' in title_safe.lower():
                research_type = "柔性电子"
                icon = "📱"
            elif 'powder' in title_safe.lower() or '粉体' in title_safe.lower():
                research_type = "粉体技术"
                icon = "⚙️"
            elif 'flame retardant' in title_safe.lower() or '阻燃' in title_safe.lower():
                research_type = "阻燃材料"
                icon = "🔥"
            elif 'nylon' in title_safe.lower() or '尼龙' in title_safe.lower():
                research_type = "尼龙/聚酰胺"
                icon = "🧶"
            elif 'capacitor' in title_safe.lower() or '电容器' in title_safe.lower():
                research_type = "电容器"
                icon = "⚡"
            
            area_badge = f'<span class="research-badge">{research_type}</span>' if research_type != "研究" else ''
            
            html += f"""
            <div class="manufacturing-card">
                <div class="company-header">
                    <div class="company-logo" style="background: {color}; color: white;">{icon}</div>
                    <div class="company-info">
                        <h3>{title_safe}</h3>
                        <div class="company-meta">{item['source']} • {item.get('region', '中国').title()}</div>
                    </div>
                </div>
                {area_badge}
                <div class="detail-row">
                    <div class="detail-value">{summary_safe}...</div>
                </div>
                <div style="margin-top: 15px;">
                    <a href="{item['link']}" style="color: {color};">🔗 阅读研究 →</a>
                </div>
            </div>
            """
        
        html += '</div>'
        return html
    
    def _create_factory_section(self, factory_news):
        """创建制造部分"""
        if not factory_news:
            return '<p style="color:#666; text-align:center; padding:30px;">今日无制造新闻。</p>'
        
        html = '<div class="manufacturing-grid">'
        for item in factory_news:
            title_safe = html_module.escape(item.get('title_en', item['title'])[:80])
            summary_safe = html_module.escape(item.get('summary_en', item.get('summary', ''))[:200])
            
            # 提取公司名称
            company = "制造企业"
            if 'haier' in title_safe.lower() or '海尔' in title_safe.lower():
                company = "Haier"
            elif 'midea' in title_safe.lower() or '美的' in title_safe.lower():
                company = "Midea"
            elif 'hisense' in title_safe.lower() or '海信' in title_safe.lower():
                company = "Hisense"
            elif 'samsung' in title_safe.lower():
                company = "Samsung"
            elif 'foxconn' in title_safe.lower() or '富士康' in title_safe.lower():
                company = "Foxconn"
            
            html += f"""
            <div class="manufacturing-card">
                <div class="company-header">
                    <div class="company-logo">{company[0]}</div>
                    <div class="company-info">
                        <h3>{title_safe}</h3>
                        <div class="company-meta">{item['source']} • {item.get('region', '东南亚').title()}</div>
                    </div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">摘要</div>
                    <div class="detail-value">{summary_safe}...</div>
                </div>
                <div style="margin-top: 15px;">
                    <a href="{item['link']}" style="color: #0066cc;">🔗 阅读更多</a>
                </div>
            </div>
            """
        html += '</div>'
        return html
    
    def _create_tech_section(self, tech_news):
        """创建技术部分"""
        if not tech_news:
            return '<p style="color:#666; text-align:center; padding:30px;">今日无技术新闻。</p>'
        
        html = """<table class="tech-table">
            <thead>
                <tr>
                    <th>技术 / 产品</th>
                    <th>应用领域</th>
                    <th>公司</th>
                    <th>来源</th>
                </tr>
            </thead>
            <tbody>"""
        
        for item in tech_news[:10]:
            title_safe = html_module.escape(item.get('title_en', item['title'])[:70])
            text = (title_safe + ' ' + item.get('summary', '')).lower()
            
            # 增强应用检测
            app = "消费电子"
            if any(k in text for k in ['ai glass', 'smart glass', 'ar', 'vr', '眼镜']):
                app = "AI/AR/VR 眼镜"
            elif any(k in text for k in ['wearable', 'watch', '手环']):
                app = "可穿戴设备"
            elif any(k in text for k in ['smart home', '智能家居', 'appliance']):
                app = "智能家居"
            elif any(k in text for k in ['thermoelectric', 'body heat']):
                app = "能量采集"
            elif any(k in text for k in ['fiber chip', 'electronic fiber']):
                app = "智能纺织品"
            elif any(k in text for k in ['chip', 'semiconductor']):
                app = "半导体"
            elif any(k in text for k in ['display', 'screen', 'oled']):
                app = "显示技术"
            elif any(k in text for k in ['powder', '粉体']):
                app = "粉体材料"
            elif any(k in text for k in ['flame retardant', '阻燃']):
                app = "阻燃材料"
            elif any(k in text for k in ['nylon', '尼龙']):
                app = "工程塑料"
            elif any(k in text for k in ['capacitor', '电容器']):
                app = "电容器"
            
            # 提取公司
            company = "多家"
            for c in ['Haier', '海尔', 'Midea', '美的', 'Hisense', '海信', 
                     'Rokid', 'COLMO', 'BOE', '京东方', 'Huawei', '华为',
                     'Samsung', 'LG', 'Sony']:
                if c.lower() in text:
                    company = c.replace('海尔', 'Haier').replace('美的', 'Midea').replace('海信', 'Hisense')
                    break
            
            html += f"""
            <tr>
                <td><div class="tech-name">{title_safe}</div></td>
                <td>{app}</td>
                <td>{company}</td>
                <td><a href="{item['link']}" style="color: #0066cc;">{item['source']}</a></td>
            </tr>"""
        
        html += "</tbody></table>"
        return html
    
    def _create_exhibition_section(self, exhibition_news):
        """创建展会部分"""
        if not exhibition_news:
            return '<p style="color:#666; text-align:center; padding:30px;">今日无展会新闻。</p>'
        
        html = '<div class="exhibition-grid">'
        for item in exhibition_news:
            title_safe = html_module.escape(item.get('title_en', item['title'])[:60])
            
            # 提取日期
            date_match = re.search(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}', item.get('summary', ''))
            date = date_match.group() if date_match else "待定"
            
            html += f"""
            <div class="exhibition-card">
                <div class="exhibition-name">{title_safe}</div>
                <div class="exhibition-dates">📅 {date}</div>
                <div class="exhibition-venue">📍 {item.get('region', '东南亚').title()}</div>
                <div style="margin-top: 15px;">
                    <a href="{item['link']}" style="color: #0066cc;">🔗 详情</a>
                </div>
            </div>
            """
        html += '</div>'
        return html
    
    def _create_trends_section(self, trends):
        """创建趋势部分"""
        html = '<div class="trends-grid">'
        
        # 热门公司
        html += '<div class="trend-card"><h3>🏢 热门公司</h3><ul class="trend-list">'
        for company, count in trends['top_companies'][:5]:
            html += f'<li class="trend-item"><span class="trend-rank">•</span>{company} ({count})</li>'
        html += '</ul></div>'
        
        # 热门地点
        html += '<div class="trend-card"><h3>📍 制造热点</h3><ul class="trend-list">'
        for loc, count in trends['top_locations'][:5]:
            html += f'<li class="trend-item"><span class="trend-rank">•</span>{loc.title()} ({count})</li>'
        html += '</ul></div>'
        
        # 热门技术
        html += '<div class="trend-card"><h3>🔬 新兴技术</h3><ul class="trend-list">'
        for tech, count in trends['top_technologies'][:5]:
            html += f'<li class="trend-item"><span class="trend-rank">•</span>{tech} ({count})</li>'
        html += '</ul></div>'
        
        html += '</div>'
        return html
    
    def _generate_executive_summary(self, news_items, trends, factory_news, tech_news, research_news):
        """使用AI生成高管摘要"""
        try:
            locations = ', '.join([loc[0].title() for loc in trends['top_locations'][:2]]) if trends['top_locations'] else '东南亚'
            companies = ', '.join([comp[0].title() for comp in trends['top_companies'][:2]]) if trends['top_companies'] else '主要品牌'
            technologies = ', '.join([tech[0] for tech in trends['top_technologies'][:2]]) if trends['top_technologies'] else '新兴技术'
            
            prompt = f"""Write a 4-sentence executive summary in English about consumer electronics manufacturing and innovation in Southeast Asia.

Today's highlights:
- Research breakthroughs: {len(research_news)} articles on cutting-edge technologies
- Manufacturing projects: {len(factory_news)} new factory/investment announcements
- Technology news: {len(tech_news)} articles on new products and innovations
- Key locations: {locations}
- Active companies: {companies}
- Emerging technologies: {technologies}

Make it professional, data-driven, and impactful for a company director. Focus on strategic implications for the consumer electronics industry in Southeast Asia."""
            
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
            return f"Today's report covers {len(news_items)} articles on consumer electronics in Southeast Asia. Highlights include {len(research_news)} research breakthroughs, {len(factory_news)} manufacturing projects, and {len(tech_news)} new technology developments. Key activity in {locations} from companies including {companies}, with emerging focus on {technologies}."
    
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
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = EMAIL_CONFIG["sender_email"]
            msg['To'] = ', '.join(recipients)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 尝试使用SSL（端口465）
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
                
                # 尝试TLS（端口587）
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
        
        # 步骤1：获取新闻
        news_items = self.fetch_all_news()
        if not news_items:
            self.log("❌ 未找到相关新闻", "ERROR")
            return
        
        # 步骤2：翻译中文新闻
        translated = self.translate_chinese_news()
        all_news = news_items + translated
        
        # 步骤3：分析趋势
        trends = self.analyze_trends(all_news)
        
        # 步骤4：生成仪表板
        html_content = self.generate_executive_dashboard(all_news, trends)
        
        # 步骤5：发送邮件
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
