"""
╔══════════════════════════════════════════════════════════════╗
║                    بوت دليل - Daleel Bot                      ║
║              Q&A Bot for ARC Raiders Community                ║
║                     By: SPECTRE Leader                        ║
║                   Fixed & Improved Version                    ║
╚══════════════════════════════════════════════════════════════╝
"""

import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import asyncio
import aiohttp
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from difflib import SequenceMatcher
import re

# ═══════════════════════════════════════════════════════════════
# التهيئة - Configuration
# ═══════════════════════════════════════════════════════════════

# Environment Variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_GUILD_ID = int(os.getenv('ALLOWED_GUILD_ID', '621014916173791288'))
ALLOWED_CHANNEL_ID = int(os.getenv('ALLOWED_CHANNEL_ID', '1459709364301594848'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '1459724977346445429'))
OWNER_ID = int(os.getenv('OWNER_ID', '595228721946820614'))

# API Keys
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Bot Settings
BOT_NAME = "دليل"
BOT_VERSION = "2.1.0"  # Updated version

AI_MODE = os.getenv("AI_MODE", "ai_only").lower()

# ═══════════════════════════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Daleel')

# ═══════════════════════════════════════════════════════════════
# Wiki Fetching - محسّن
# ═══════════════════════════════════════════════════════════════

def slugify_for_docs(name: str) -> str:
    """تحويل الاسم لـ slug مناسب للويكي"""
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[^A-Za-z0-9 _-]', '', name)
    return name.replace(' ', '_')


async def fetch_doc_snippet(raw_name: str, max_chars: int = 2500) -> dict:
    """
    يجيب معلومات منظمة من ويكي ARC Raiders
    يرجع dict فيه: sources, guide, summary, sell_price, weight, rarity
    """
    if not raw_name:
        return {}
    
    slug = slugify_for_docs(raw_name)
    result = {
        "item_name": raw_name,
        "sources": [],
        "guide": "",
        "summary": "",
        "sell_price": "",
        "weight": "",
        "rarity": "",
        "found": False  # علامة إذا لقينا الصفحة
    }
    
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        url = f"https://arcraiders.wiki/wiki/{slug}"
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return result
                
                html = await resp.text()
                result["found"] = True
                
                # استخراج Sources
                sources_match = re.search(
                    r'<h2[^>]*>.*?Sources.*?</h2>(.*?)(?=<h2|$)',
                    html,
                    re.DOTALL | re.IGNORECASE
                )
                if sources_match:
                    sources_html = sources_match.group(1)
                    # استخراج من القوائم
                    list_items = re.findall(r'<li[^>]*>(.*?)</li>', sources_html, re.DOTALL)
                    for li in list_items:
                        # استخراج النص من الروابط
                        link_match = re.search(r'>([^<]+)</a>', li)
                        if link_match:
                            text = link_match.group(1).strip()
                            if text and text.lower() not in ['edit', 'scavenging']:
                                result["sources"].append(text)
                        else:
                            # نص بدون رابط
                            text = re.sub(r'<[^>]+>', '', li).strip()
                            if text and len(text) > 2:
                                result["sources"].append(text)
                
                # استخراج Guide
                guide_match = re.search(
                    r'<h2[^>]*>.*?Guide.*?</h2>(.*?)(?=<h2|$)',
                    html,
                    re.DOTALL | re.IGNORECASE
                )
                if guide_match:
                    guide_html = guide_match.group(1)
                    # تنظيف النص
                    guide_text = re.sub(r'<[^>]+>', ' ', guide_html)
                    guide_text = re.sub(r'\s+', ' ', guide_text).strip()
                    result["guide"] = guide_text[:1500]
                
                # استخراج Sell Price
                price_match = re.search(r'Sell Price[^>]*>.*?(\d[\d,]+)', html, re.DOTALL | re.IGNORECASE)
                if price_match:
                    result["sell_price"] = price_match.group(1)
                
                # استخراج Weight
                weight_match = re.search(r'Weight[^>]*>.*?([\d.]+)', html, re.DOTALL | re.IGNORECASE)
                if weight_match:
                    result["weight"] = weight_match.group(1)
                
                # استخراج Rarity
                rarity_match = re.search(r'(Common|Uncommon|Rare|Epic|Legendary)', html, re.IGNORECASE)
                if rarity_match:
                    result["rarity"] = rarity_match.group(1)
                
                # استخراج الوصف الأول
                desc_match = re.search(
                    r'<p><b>([^<]+)</b>\s*is\s+([^<]+)</p>',
                    html
                )
                if desc_match:
                    result["summary"] = f"{desc_match.group(1)} is {desc_match.group(2)}"
                
        except Exception as e:
            logger.error(f"Error fetching wiki for '{raw_name}': {e}")
    
    return result


def build_wiki_context(wiki_data: dict) -> str:
    """
    يبني نص السياق من بيانات الويكي
    """
    if not wiki_data or not wiki_data.get("found"):
        return ""
    
    parts = []
    
    if wiki_data.get("summary"):
        parts.append(f"الوصف: {wiki_data['summary']}")
    
    if wiki_data.get("rarity"):
        parts.append(f"الندرة: {wiki_data['rarity']}")
    
    if wiki_data.get("sell_price"):
        parts.append(f"سعر البيع: {wiki_data['sell_price']}")
    
    if wiki_data.get("weight"):
        parts.append(f"الوزن: {wiki_data['weight']}")
    
    if wiki_data.get("sources"):
        sources_list = ", ".join(wiki_data["sources"][:10])
        parts.append(f"مصادر الحصول عليه: {sources_list}")
    
    if wiki_data.get("guide"):
        parts.append(f"دليل اللاعب: {wiki_data['guide']}")
    
    if parts:
        return "=== معلومات الويكي ===\n" + "\n".join(parts)
    
    return ""


# ═══════════════════════════════════════════════════════════════
# قاموس عربي-إنجليزي للكلمات الشائعة
# ═══════════════════════════════════════════════════════════════

ARABIC_TO_ENGLISH = {
    # أسلحة
    'سلاح': 'weapon',
    'اسلحة': 'weapons',
    'بندقية': 'rifle',
    'مسدس': 'pistol',
    'رشاش': 'smg',
    'قناص': 'sniper',
    'شوتقن': 'shotgun',
    
    # مخططات
    'مخطوطة': 'blueprint',
    'مخطوطه': 'blueprint',
    'مخطط': 'blueprint',
    'بلوبرنت': 'blueprint',
    
    # صناعة
    'تصنيع': 'craft',
    'صناعة': 'craft',
    'صنع': 'craft',
    'طاولة تصنيع': 'workbench',
    'طاولة تصليح': 'workbench',
    'طاولة تطوير': 'workbench',
    'طاولة': 'bench',
    'طاولات': 'bench',
    'ادوات': 'materials',
    'أدوات': 'materials',
    'متطلبات': 'requirements',
    'مواد': 'materials',
    'عطني': '',
    'اعطني': '',
    'ابي': '',
    'ابغى': '',
    'وش': '',
    'كيف': '',
    'وين': '',
    'اين': '',
    'أين': '',
    'مكان': '',
    'موقع': '',
    'طرق': '',
    'طريقة': '',
    'طريق': '',
    'اسرع': '',
    'أسرع': '',
    'سبون': 'spawn',
    'السبون': 'spawn',
    'rate': '',
    'spawnrate': '',
    'دليل': '',
    
    # فليرات
    'فلير': 'flare',
    'الفلير': 'flare',
    'فلارات': 'flare',
    'الفلارات': 'flare',
    
    # بوس THE QUEEN
    'كوين': 'queen',
    'الكوين': 'queen',
    
    # ندرة
    'ذهبي': 'legendary',
    'ذهبية': 'legendary',
    'ذهبيه': 'legendary',
    'اسطوري': 'legendary',
    'أسطوري': 'legendary',
    'بنفسجي': 'epic',
    'ملحمي': 'epic',
    'ازرق': 'rare',
    'أزرق': 'rare',
    'نادر': 'rare',
    'اخضر': 'uncommon',
    'أخضر': 'uncommon',
    'ابيض': 'common',
    'أبيض': 'common',
    'عادي': 'common',
    
    # مكونات
    'مكونات': 'components',
    'كهربائية': 'electrical',
    'كهربائي': 'electrical',
    'ميكانيكية': 'mechanical',
    'متقدم': 'advanced',
    'متقدمة': 'advanced',
    'خام': 'raw',
    
    # أماكن
    'خريطة': 'map',
    'منطقة': 'zone',
    'مصنع': 'factory',
    'مستودع': 'warehouse',
    
    # عناصر
    'درع': 'armor',
    'خوذة': 'helmet',
    'صدرية': 'vest',
    'حقيبة': 'backpack',
    'شنطة': 'backpack',
    
    # أعداء
    'روبوت': 'bot',
    'عدو': 'enemy',
    'زعيم': 'boss',
    
    # مهارات
    'مهارة': 'skill',
    'مهارات': 'skills',
    'شجرة': 'tree',
    
    # تجارة
    'تاجر': 'trader',
    'متجر': 'shop',
    'شراء': 'buy',
    'بيع': 'sell'
}

# ═══════════════════════════════════════════════════════════════
# المناطق الرسمية في ARC Raiders
# ═══════════════════════════════════════════════════════════════

VALID_LOCATIONS = {
    # الخرائط الرئيسية
    "dam battlegrounds": "Dam Battlegrounds",
    "the spaceport": "The Spaceport",
    "spaceport": "The Spaceport",
    "buried city": "Buried City",
    "the blue gate": "The Blue Gate",
    "blue gate": "The Blue Gate",
    "stella montis": "Stella Montis",
    
    # مناطق Dam Battlegrounds
    "scrap yard": "Scrap Yard (Dam Battlegrounds)",
    "hydroponic dome": "Hydroponic Dome (Dam Battlegrounds)",
    "water treatment": "Water Treatment Control (Dam Battlegrounds)",
    "power generation": "Power Generation Complex (Dam Battlegrounds)",
    
    # مناطق The Spaceport
    "rocket assembly": "Rocket Assembly (Spaceport)",
    "vehicle maintenance": "Vehicle Maintenance (Spaceport)",
    
    # مناطق Buried City
    "parking garage": "Parking Garage (Buried City)",
    "warehouse": "Warehouse (Buried City)",
    
    # مناطق The Blue Gate
    "checkpoint": "Checkpoint (The Blue Gate)",
}

# المناطق الوهمية الشائعة اللي الـ AI يخترعها
FAKE_LOCATIONS = [
    "industrial zone",
    "mechanical zone",
    "industrial area",
    "mechanical area",
    "factory zone",
    "resource zone",
    "loot zone",
]


def validate_location(location: str) -> str | None:
    """يتحقق إذا المنطقة صحيحة ويرجع الاسم الرسمي إن وجد"""
    if not location:
        return None
    
    location_lower = location.lower().strip()
    
    if location_lower in VALID_LOCATIONS:
        return VALID_LOCATIONS[location_lower]
    
    for key, value in VALID_LOCATIONS.items():
        if key in location_lower or location_lower in key:
            return value
    
    return None


def validate_ai_response(response: str, wiki_data: dict | None) -> str:
    """
    يتحقق من صحة رد الـ AI ويصحح الأخطاء الشائعة في أسماء المناطق
    """
    if not response:
        return response
    
    response_lower = response.lower()
    
    # تحقق إذا الرد يحتوي على مناطق وهمية
    for fake in FAKE_LOCATIONS:
        if fake in response_lower:
            # إذا عندنا بيانات ويكي موثوقة، نستخدمها
            if wiki_data and wiki_data.get("guide"):
                guide_text = str(wiki_data["guide"])[:600]
                # نبني رد بديل من الويكي
                sources = wiki_data.get("sources", [])
                sources_text = ", ".join(sources[:5]) if sources else ""
                
                replacement = f"حسب ويكي ARC Raiders: {guide_text}"
                if sources_text:
                    replacement = f"يطلع من: {sources_text}. {replacement}"
                
                return replacement
            break
    
    return response


# ═══════════════════════════════════════════════════════════════
# دوال مساعدة للتحليل
# ═══════════════════════════════════════════════════════════════

def is_comparative_question(text: str) -> bool:
    lowered = text.lower()
    tokens = [
        " vs ", "vs ", " افضل ", "أفضل", "احسن", "أحسن",
        " or ", " or", "or ", "ولا", "مقارنة", "better", "best",
    ]
    return any(token in lowered for token in tokens)


def is_strategy_question(text: str) -> bool:
    lowered = text.lower()
    tokens = [
        "استراتيجية", "strategy", "كيف العب", "كيف ألعب",
        "build", "بيلد", "meta", "ميتا", "طريقة اللعب",
    ]
    return any(token in lowered for token in tokens)


def is_explanatory_question(text: str) -> bool:
    lowered = text.lower()
    tokens = [
        "ليش", "لماذا", "why", "سبب", "اشرح", "شرح", "explain",
    ]
    return any(token in lowered for token in tokens)


def extract_intents(text: str) -> list:
    intents = []
    lowered = text.lower()
    if any(token in lowered for token in ["أفضل", "أقوى", "أحسن", "أسرع", "أرخص", "أكثر", "vs", "مقارنة", "يستحق", "ولا", "or", "better", "best"]):
        intents.append("comparative")
    if any(token in lowered for token in ["استراتيجية", "strategy", "كيف العب", "كيف ألعب", "build", "بيلد", "طريقة اللعب", "نصائح", "أواجه", "أتعامل", "أفوز", "أهرب", "أقتل"]):
        intents.append("strategy")
    if any(token in lowered for token in ["ليش", "لماذا", "why", "سبب", "اشرح", "شرح", "explain", "يعني", "معنى", "تعريف", "وش", "ايش"]):
        intents.append("explanation")
    if any(token in lowered for token in ["بديل", "بدائل", "حل", "إذا ما لقيت", "ما حصلت", "ما عندي", "alternative"]):
        intents.append("alternatives")
    if any(token in lowered for token in ["مبتدئ", "محترف", "نصائح للمبتدئين", "نصائح للمحترفين", "مستوى"]):
        intents.append("player_level")
    if any(token in lowered for token in ["ميتا", "meta", "تحديث", "باتش", "patch", "تغييرات", "أقوى حالياً"]):
        intents.append("meta")
    if any(token in lowered for token in ["مجتمع", "لاعبين", "تجارب", "وش رأيكم", "أفضل طريقة جربتوها"]):
        intents.append("community")
    if not intents:
        intents.append("general")
    return intents


def should_use_ai(text: str) -> bool:
    intents = extract_intents(text)
    for intent in intents:
        if intent in ["comparative", "strategy", "explanation", "alternatives", "player_level", "meta"]:
            return True
    return False


def is_ai_configured() -> bool:
    return any([
        DEEPSEEK_API_KEY,
        GROQ_API_KEY,
        OPENAI_API_KEY,
        ANTHROPIC_API_KEY,
        GOOGLE_API_KEY,
    ])


# ═══════════════════════════════════════════════════════════════
# روابط الصور والألوان
# ═══════════════════════════════════════════════════════════════

IMAGES_BASE_URL = "https://raw.githubusercontent.com/RaidTheory/arcraiders-data/main/images"

COLORS = {
    "success": 0x2ecc71,
    "error": 0xe74c3c,
    "warning": 0xf39c12,
    "info": 0x3498db,
    "primary": 0x9b59b6,
}

# ═══════════════════════════════════════════════════════════════
# قاعدة البيانات - Database Manager
# ═══════════════════════════════════════════════════════════════

class DatabaseManager:
    """مدير قاعدة البيانات - يحمل كل بيانات اللعبة"""
    
    def __init__(self):
        self.items = []
        self.quests = []
        self.hideout = []
        self.bots = []
        self.maps = []
        self.trades = []
        self.skills = []
        self.projects = []
        self.all_data = []
        self.loaded = False
        
    def load_all(self):
        """تحميل كل البيانات من المجلدات"""
        base_path = Path('arcraiders-data')
        
        if not base_path.exists():
            logger.warning("مجلد arcraiders-data غير موجود!")
            return False
        
        try:
            # تحميل Items
            items_path = base_path / 'items'
            if items_path.exists():
                for file in items_path.glob('*.json'):
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                self.items.extend(data)
                            elif isinstance(data, dict):
                                self.items.append(data)
                    except Exception as e:
                        logger.error(f"خطأ في تحميل {file}: {e}")
            
            # تحميل Quests
            quests_path = base_path / 'quests'
            if quests_path.exists():
                for file in quests_path.glob('*.json'):
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                self.quests.extend(data)
                            elif isinstance(data, dict):
                                self.quests.append(data)
                    except Exception as e:
                        logger.error(f"خطأ في تحميل {file}: {e}")
            
            # تحميل Hideout
            hideout_path = base_path / 'hideout'
            if hideout_path.exists():
                for file in hideout_path.glob('*.json'):
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                self.hideout.extend(data)
                            elif isinstance(data, dict):
                                self.hideout.append(data)
                    except Exception as e:
                        logger.error(f"خطأ في تحميل {file}: {e}")
            
            # تحميل Map Events
            mapevents_path = base_path / 'map-events'
            if mapevents_path.exists():
                for file in mapevents_path.glob('*.json'):
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                self.maps.extend(data)
                            elif isinstance(data, dict):
                                self.maps.append(data)
                    except Exception as e:
                        logger.error(f"خطأ في تحميل {file}: {e}")
            
            # تحميل ملفات JSON الرئيسية
            json_files = [
                ('bots.json', 'bots'),
                ('maps.json', 'maps'),
                ('trades.json', 'trades'),
                ('skillNodes.json', 'skills'),
                ('projects.json', 'projects'),
            ]
            
            for filename, attr in json_files:
                file_path = base_path / filename
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                setattr(self, attr, data)
                            elif isinstance(data, dict):
                                setattr(self, attr, [data])
                        logger.info(f"✅ تم تحميل {len(getattr(self, attr))} من {filename}")
                    except Exception as e:
                        logger.error(f"خطأ في تحميل {filename}: {e}")
            
            # دمج كل البيانات
            self.all_data.extend(self.items)
            self.all_data.extend(self.quests)
            self.all_data.extend(self.hideout)
            self.all_data.extend(self.bots)
            self.all_data.extend(self.maps)
            self.all_data.extend(self.trades)
            self.all_data.extend(self.skills)
            self.all_data.extend(self.projects)
            
            self.loaded = True
            logger.info(f"✅ تم تحميل {len(self.all_data)} عنصر من قاعدة البيانات")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تحميل قاعدة البيانات: {e}")
            return False
    
    def get_stats(self):
        """إحصائيات قاعدة البيانات"""
        return {
            'items': len(self.items),
            'quests': len(self.quests),
            'hideout': len(self.hideout),
            'bots': len(self.bots),
            'maps': len(self.maps),
            'trades': len(self.trades),
            'skills': len(self.skills),
            'projects': len(self.projects),
            'total': len(self.all_data)
        }

# ═══════════════════════════════════════════════════════════════
# محرك البحث - Search Engine
# ═══════════════════════════════════════════════════════════════

class SearchEngine:
    """محرك البحث الذكي - يدعم العربي والإنجليزي"""
    
    def __init__(self, database: DatabaseManager):
        self.db = database
        self.search_history = {}
        
    def normalize_text(self, text: str) -> str:
        """تنظيف وتوحيد النص"""
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def translate_arabic_query(self, query: str) -> str:
        """ترجمة الكلمات العربية للإنجليزية"""
        words = query.split()
        translated = []
        
        for word in words:
            word_lower = word.lower()
            if word_lower in ARABIC_TO_ENGLISH:
                translated.append(ARABIC_TO_ENGLISH[word_lower])
            else:
                translated.append(word)
        
        return ' '.join(translated)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """حساب نسبة التشابه بين نصين"""
        return SequenceMatcher(None, 
                               self.normalize_text(text1), 
                               self.normalize_text(text2)).ratio()
    
    def _calculate_match_score(self, query: str, text: str) -> float:
        """حساب درجة التطابق"""
        if not query or not text:
            return 0
        
        if query == text:
            return 1.0
        
        if query in text:
            return 0.85 + (len(query) / len(text)) * 0.1
        
        query_words = query.split()
        text_lower = text.lower()
        matches = sum(1 for word in query_words if word in text_lower)
        if matches == len(query_words) and query_words:
            return 0.8 + (matches / len(query_words)) * 0.15
        
        if matches > 0 and query_words:
            return 0.5 + (matches / len(query_words)) * 0.3
        
        similarity = self.calculate_similarity(query, text)
        return similarity * 0.7
    
    def search(self, query: str, limit: int = 5) -> list:
        """البحث في قاعدة البيانات"""
        if not self.db.loaded:
            return []
        
        query_normalized = self.normalize_text(query)
        query_translated = self.translate_arabic_query(query_normalized)
        
        results = []
        
        for item in self.db.all_data:
            if not isinstance(item, dict):
                continue
                
            score = 0
            matched_field = None
            
            searchable_fields = ['id', 'name', 'title', 'displayName', 'description', 
                                'category', 'type', 'location', 'nameKey', 'rarity']
            
            for field in searchable_fields:
                if field not in item or not item[field]:
                    continue
                
                field_value = item[field]
                
                if isinstance(field_value, dict):
                    for lang, text in field_value.items():
                        if not text or not isinstance(text, str):
                            continue
                        
                        text_normalized = self.normalize_text(text)
                        
                        s1 = self._calculate_match_score(query_normalized, text_normalized)
                        s2 = self._calculate_match_score(query_translated, text_normalized)
                        
                        current_score = max(s1, s2)
                        if current_score > score:
                            score = current_score
                            matched_field = field
                    
                    if score >= 0.95:
                        break
                
                elif isinstance(field_value, str):
                    field_normalized = self.normalize_text(field_value)
                    
                    s1 = self._calculate_match_score(query_normalized, field_normalized)
                    s2 = self._calculate_match_score(query_translated, field_normalized)
                    
                    current_score = max(s1, s2)
                    if current_score > score:
                        score = current_score
                        matched_field = field
            
            if score > 0.3:
                results.append({
                    'item': item,
                    'score': score,
                    'matched_field': matched_field
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def extract_name(self, item: dict) -> str:
        """استخراج الاسم من العنصر"""
        name_fields = ['name', 'title', 'displayName', 'nameKey']
        
        for field in name_fields:
            if field in item:
                value = item[field]
                
                if isinstance(value, dict):
                    return value.get('en') or value.get('ar') or list(value.values())[0]
                
                elif isinstance(value, str) and value:
                    return value
        
        return "غير معروف"
    
    def find_similar(self, query: str, limit: int = 3) -> list:
        """إيجاد عناصر مشابهة للاقتراحات"""
        results = self.search(query, limit=limit)
        suggestions = []
        
        for r in results:
            item = r['item']
            name = self.extract_name(item)
            if name and name != "Unknown" and name not in suggestions:
                suggestions.append(name)
        
        return suggestions

# ═══════════════════════════════════════════════════════════════
# نظام AI - AI Manager
# ═══════════════════════════════════════════════════════════════

class AIManager:
    """مدير الذكاء الاصطناعي - 5 مستويات احتياطية"""
    
    def __init__(self):
        self.daily_usage = 0
        self.daily_limit = 50
        self.last_reset = datetime.now().date()
        self.usage_stats = {
            'deepseek': 0,
            'groq': 0,
            'openai': 0,
            'anthropic': 0,
            'google': 0
        }
        self.translation_cache = {}
    
    async def translate_to_arabic(self, text: str) -> str:
        """ترجمة نص للعربي - سريع بـ Groq"""
        if not text or len(text) < 3:
            return text
        
        cache_key = text[:100]
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        if any('\u0600' <= c <= '\u06FF' for c in text):
            return text
        
        try:
            if GROQ_API_KEY:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        'https://api.groq.com/openai/v1/chat/completions',
                        headers={
                            'Authorization': f'Bearer {GROQ_API_KEY}',
                            'Content-Type': 'application/json'
                        },
                        json={
                            'model': 'llama-3.3-70b-versatile',
                            'messages': [
                                {'role': 'system', 'content': 'أنت مترجم. ترجم النص التالي للعربية فقط بدون أي إضافات أو شرح.'},
                                {'role': 'user', 'content': text}
                            ],
                            'max_tokens': 300,
                            'temperature': 0.3
                        },
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            translated = data['choices'][0]['message']['content'].strip()
                            self.translation_cache[cache_key] = translated
                            return translated
        except Exception as e:
            logger.warning(f"خطأ في الترجمة: {e}")
        
        return text
    
    def check_daily_limit(self) -> bool:
        """فحص الحد اليومي"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.daily_usage = 0
            self.last_reset = today
        return self.daily_usage < self.daily_limit
    
    async def ask_ai(self, question: str, context: str = "") -> dict:
        """سؤال الـ AI مع نظام الاحتياطي"""
        
        if not is_ai_configured():
            return {
                'success': False,
                'answer': "الذكاء الاصطناعي غير مفعّل حالياً.",
                'provider': None
            }
        
        if not self.check_daily_limit():
            return {
                'success': False,
                'answer': "⚠️ تم الوصول للحد اليومي من استخدام AI",
                'provider': None
            }
        
        system_prompt = f"""أنت "دليل" - بوت مساعد لمجتمع ARC Raiders العربي.
قواعد الرد:
1. رد بالعربي دائماً.
2. ابدأ دائماً بجملة مباشرة تجيب على السؤال.
3. اجعل الإجابة من سطرين إلى ثلاثة كحد أقصى.
4. لا تستخدم نقاط أو قوائم أو تعداد؛ استخدم نصاً متصلاً قصيراً.
5. لو ما تعرف الجواب بدقة، استخدم أفضل معرفتك عن اللعبة.
6. ركز على لعبة ARC Raiders فقط.
7. لا تكرر نصوصاً طويلة أو شروحات مملة؛ كن عملياً ومباشراً.
8. ⚠️ مهم: استخدم فقط أسماء المناطق الحقيقية من الويكي. لا تخترع أسماء مثل "Industrial Zone" أو "Mechanical Zone".
9. المناطق الرئيسية: Dam Battlegrounds, The Spaceport, Buried City, The Blue Gate, Stella Montis.
{f'السياق: {context}' if context else ''}"""
        
        providers = [
            ('openai', self._ask_openai),
            ('anthropic', self._ask_anthropic),
            ('deepseek', self._ask_deepseek),
            ('groq', self._ask_groq),
            ('google', self._ask_google),
        ]
        
        for provider_name, provider_func in providers:
            try:
                result = await provider_func(question, system_prompt)
                if result:
                    self.daily_usage += 1
                    self.usage_stats[provider_name] += 1
                    return {
                        'success': True,
                        'answer': result,
                        'provider': provider_name
                    }
            except Exception as e:
                logger.warning(f"فشل {provider_name}: {e}")
                continue
        
        return {
            'success': False,
            'answer': "عذراً، حدث خطأ في الاتصال بالـ AI",
            'provider': None
        }
    
    async def _ask_deepseek(self, question: str, system_prompt: str) -> str:
        if not DEEPSEEK_API_KEY:
            return None
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.deepseek.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'deepseek-chat',
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': question}
                    ],
                    'max_tokens': 500,
                    'temperature': 0.7
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
        return None
    
    async def _ask_groq(self, question: str, system_prompt: str) -> str:
        if not GROQ_API_KEY:
            return None
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {GROQ_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.3-70b-versatile',
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': question}
                    ],
                    'max_tokens': 500,
                    'temperature': 0.7
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
        return None
    
    async def _ask_openai(self, question: str, system_prompt: str) -> str:
        if not OPENAI_API_KEY:
            return None
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {OPENAI_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gpt-4o-mini',
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': question}
                    ],
                    'max_tokens': 500,
                    'temperature': 0.7
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
        return None
    
    async def _ask_anthropic(self, question: str, system_prompt: str) -> str:
        if not ANTHROPIC_API_KEY:
            return None
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': ANTHROPIC_API_KEY,
                    'Content-Type': 'application/json',
                    'anthropic-version': '2023-06-01'
                },
                json={
                    'model': 'claude-3-haiku-20240307',
                    'max_tokens': 500,
                    'system': system_prompt,
                    'messages': [
                        {'role': 'user', 'content': question}
                    ]
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['content'][0]['text']
        return None
    
    async def _ask_google(self, question: str, system_prompt: str) -> str:
        if not GOOGLE_API_KEY:
            return None
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}',
                headers={'Content-Type': 'application/json'},
                json={
                    'contents': [{
                        'parts': [{'text': f"{system_prompt}\n\nسؤال: {question}"}]
                    }],
                    'generationConfig': {
                        'maxOutputTokens': 500,
                        'temperature': 0.7
                    }
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['candidates'][0]['content']['parts'][0]['text']
        return None

# ═══════════════════════════════════════════════════════════════
# نظام السياق - Context Manager
# ═══════════════════════════════════════════════════════════════

class ContextManager:
    """مدير سياق المحادثات"""
    
    def __init__(self, timeout_minutes: int = 5):
        self.contexts = {}
        self.timeout = timedelta(minutes=timeout_minutes)
    
    def set_context(self, user_id: int, item_name: str, item_data: dict = None):
        self.contexts[user_id] = {
            'item': item_name,
            'data': item_data,
            'timestamp': datetime.now()
        }
    
    def get_context(self, user_id: int) -> dict:
        if user_id not in self.contexts:
            return None
        
        context = self.contexts[user_id]
        if datetime.now() - context['timestamp'] > self.timeout:
            del self.contexts[user_id]
            return None
        
        return context
    
    def clear_context(self, user_id: int):
        if user_id in self.contexts:
            del self.contexts[user_id]
    
    def inject_context(self, user_id: int, question: str) -> str:
        context = self.get_context(user_id)
        if not context:
            return question
        
        follow_up_keywords = [
            'نسبة', 'spawn', 'الموقع', 'location', 'وين', 'where',
            'كم', 'how much', 'الندرة', 'rarity',
            'طريقة', 'افضل طريقة', 'أفضل طريقة',
            'استراتيجية', 'strategy',
            'how to', 'how do', 'use', 'استعمل'
        ]
        
        question_lower = question.lower()
        is_follow_up = any(keyword in question_lower for keyword in follow_up_keywords)
        
        if is_follow_up and len(question.split()) <= 5:
            return f"{context['item']} {question}"
        
        return question

# ═══════════════════════════════════════════════════════════════
# نظام الحماية - Anti-Spam
# ═══════════════════════════════════════════════════════════════

class AntiSpam:
    """نظام منع السبام - 3 أسئلة/دقيقة"""
    
    def __init__(self, max_messages: int = 3, window_seconds: int = 60):
        self.user_messages = {}
        self.max_messages = max_messages
        self.window = timedelta(seconds=window_seconds)
    
    def check(self, user_id: int) -> tuple:
        now = datetime.now()
        
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        self.user_messages[user_id] = [
            ts for ts in self.user_messages[user_id]
            if now - ts < self.window
        ]
        
        if len(self.user_messages[user_id]) >= self.max_messages:
            oldest = min(self.user_messages[user_id])
            wait_time = int((oldest + self.window - now).total_seconds())
            return False, wait_time
        
        self.user_messages[user_id].append(now)
        return True, 0

# ═══════════════════════════════════════════════════════════════
# منشئ الـ Embeds
# ═══════════════════════════════════════════════════════════════

class EmbedBuilder:
    """منشئ الـ Embeds الجميلة"""
    
    @staticmethod
    def success(title: str, description: str) -> discord.Embed:
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=COLORS["success"],
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"🤖 {BOT_NAME}")
        return embed

    @staticmethod
    def error(title: str, description: str) -> discord.Embed:
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=COLORS["error"],
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"🤖 {BOT_NAME}")
        return embed
    
    @staticmethod
    def warning(title: str, description: str) -> discord.Embed:
        embed = discord.Embed(
            title=f"⚠️ {title}",
            description=description,
            color=COLORS["warning"],
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"🤖 {BOT_NAME}")
        return embed
    
    @staticmethod
    def info(title: str, description: str) -> discord.Embed:
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=COLORS["info"],
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"🤖 {BOT_NAME}")
        return embed

    @staticmethod
    def extract_field(item: dict, field: str) -> str:
        if field not in item:
            return None
        
        value = item[field]
        
        if isinstance(value, dict):
            if not value:
                return None
            primary = value.get('en') or value.get('ar')
            if primary:
                return primary
            first = next(iter(value.values()), None)
            return str(first) if first is not None else None
        
        return str(value) if value else None
    
    @staticmethod
    def get_image_url(item: dict) -> str:
        img_url = item.get('image') or item.get('icon') or item.get('imageUrl')
        if img_url and isinstance(img_url, str) and img_url.startswith('http'):
            return img_url
        
        filename = item.get('imageFilename')
        if filename and isinstance(filename, str):
            if filename.startswith('http'):
                return filename
            if filename.startswith('/'):
                filename = filename.lstrip('/')
            return f"{IMAGES_BASE_URL}/{filename}"
        
        item_id = item.get('id') or item.get('itemId') or item.get('slug')
        if item_id:
            item_type = item.get('type') or item.get('category') or ''
            if isinstance(item_type, dict):
                item_type = item_type.get('en', '')
            
            item_type_lower = str(item_type).lower()
            
            if 'bot' in item_type_lower or 'enemy' in item_type_lower:
                folder = 'bots'
            elif 'map' in item_type_lower:
                folder = 'maps'
            elif 'trader' in item_type_lower:
                folder = 'traders'
            elif 'workshop' in item_type_lower:
                folder = 'workshop'
            else:
                folder = 'items'
            
            return f"{IMAGES_BASE_URL}/{folder}/{item_id}.png"
        
        return None

    @staticmethod
    def item_embed(item: dict, translated_desc: str = None) -> discord.Embed:
        name = None
        for field in ['name', 'title', 'displayName', 'nameKey']:
            if field in item:
                value = item[field]
                if isinstance(value, dict):
                    name = value.get('en') or value.get('ar') or list(value.values())[0]
                elif value:
                    name = str(value)
                if name:
                    break
        name = name or 'غير معروف'
        
        if translated_desc:
            description = translated_desc
        else:
            description = None
            if 'description' in item:
                desc_val = item['description']
                if isinstance(desc_val, dict):
                    description = desc_val.get('en') or desc_val.get('ar') or list(desc_val.values())[0]
                else:
                    description = str(desc_val)
            description = description or 'لا يوجد وصف'
        
        embed = discord.Embed(
            title=f"📦 {name}",
            description=description[:500] if description else "لا يوجد وصف",
            color=COLORS["primary"],
            timestamp=datetime.now()
        )
        
        category = EmbedBuilder.extract_field(item, 'category')
        if category:
            embed.add_field(name="📁 الفئة", value=category, inline=True)
        
        item_type = EmbedBuilder.extract_field(item, 'type')
        if item_type:
            embed.add_field(name="🏷️ النوع", value=item_type, inline=True)
        
        rarity = EmbedBuilder.extract_field(item, 'rarity')
        if rarity:
            rarity_ar = {
                'common': 'عادي ⚪',
                'uncommon': 'غير شائع 🟢', 
                'rare': 'نادر 🔵',
                'epic': 'ملحمي 🟣',
                'legendary': 'أسطوري 🟡'
            }.get(rarity.lower(), rarity)
            embed.add_field(name="💎 الندرة", value=rarity_ar, inline=True)
        
        img_url = EmbedBuilder.get_image_url(item)
        if img_url:
            embed.set_thumbnail(url=img_url)
        
        embed.set_footer(text=f"🤖 {BOT_NAME} | ARC Raiders")
        return embed
    
    @staticmethod
    def stats_embed(db_stats: dict, ai_stats: dict, uptime: str) -> discord.Embed:
        embed = discord.Embed(
            title="📊 إحصائيات دليل",
            color=COLORS["info"],
            timestamp=datetime.now()
        )
        
        db_text = f"""
📦 العناصر: **{db_stats['items']:,}**
📜 المهمات: **{db_stats['quests']:,}**
🏠 الملاجئ: **{db_stats['hideout']:,}**
🤖 البوتات: **{db_stats['bots']:,}**
🗺️ الخرائط: **{db_stats['maps']:,}**
💰 التجارة: **{db_stats['trades']:,}**
⚡ المهارات: **{db_stats['skills']:,}**
🔧 المشاريع: **{db_stats['projects']:,}**
━━━━━━━━━━━━━━━
📚 المجموع: **{db_stats['total']:,}**
"""
        embed.add_field(name="🗄️ قاعدة البيانات", value=db_text, inline=True)
        
        ai_text = f"""
🧠 DeepSeek: **{ai_stats.get('deepseek', 0)}**
⚡ Groq: **{ai_stats.get('groq', 0)}**
🤖 OpenAI: **{ai_stats.get('openai', 0)}**
🎭 Claude: **{ai_stats.get('anthropic', 0)}**
🌐 Google: **{ai_stats.get('google', 0)}**
"""
        embed.add_field(name="🤖 استخدام AI", value=ai_text, inline=True)
        
        embed.add_field(name="⏱️ وقت التشغيل", value=uptime, inline=False)
        embed.set_footer(text=f"🤖 {BOT_NAME} v{BOT_VERSION}")
        
        return embed

# ═══════════════════════════════════════════════════════════════
# أزرار التقييم - Feedback Buttons
# ═══════════════════════════════════════════════════════════════

class FeedbackView(discord.ui.View):
    def __init__(self, author_id: int, source_question: str, embed_title: str):
        super().__init__(timeout=600)
        self.author_id = author_id
        self.source_question = source_question
        self.embed_title = embed_title or ""
    
    async def _send_log(self, interaction: discord.Interaction, status: str):
        try:
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(
                    f"📝 تقييم: {status}\n"
                    f"👤 المرسل: <@{interaction.user.id}>\n"
                    f"📦 العنوان: {self.embed_title}\n"
                    f"🗨️ السؤال: {self.source_question}"
                )
        except Exception:
            pass
    
    @discord.ui.button(label="إجابة صحيحة", style=discord.ButtonStyle.success, emoji="✅")
    async def feedback_ok(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("تم تسجيل: إجابة صحيحة ✅", ephemeral=True)
        await self._send_log(interaction, "صحيحة")
    
    @discord.ui.button(label="إجابة خاطئة", style=discord.ButtonStyle.danger, emoji="❌")
    async def feedback_bad(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("تم تسجيل: إجابة خاطئة ❌ — أبلغنا الفريق.", ephemeral=True)
        await self._send_log(interaction, "خاطئة")


async def reply_with_feedback(message: discord.Message, embed: discord.Embed):
    view = FeedbackView(message.author.id, message.content, getattr(embed, "title", "") or "")
    return await message.reply(embed=embed, view=view)

# ═══════════════════════════════════════════════════════════════
# البوت الرئيسي
# ═══════════════════════════════════════════════════════════════

class DaleelBot(commands.Bot):
    """البوت الرئيسي"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.database = DatabaseManager()
        self.search_engine = None
        self.ai_manager = AIManager()
        self.context_manager = ContextManager()
        self.anti_spam = AntiSpam()
        
        self.start_time = None
        self.questions_answered = 0
        
    async def setup_hook(self):
        self.database.load_all()
        self.search_engine = SearchEngine(self.database)
        
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ تم مزامنة {len(synced)} أمر")
        except Exception as e:
            logger.error(f"خطأ في المزامنة: {e}")
    
    async def on_ready(self):
        self.start_time = datetime.now()
        
        logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║                    ✅ البوت شغال!                             ║
╠══════════════════════════════════════════════════════════════╣
║  الاسم: {self.user.name}
║  الـ ID: {self.user.id}
║  السيرفرات: {len(self.guilds)}
║  البيانات: {self.database.get_stats()['total']} عنصر
╚══════════════════════════════════════════════════════════════╝
        """)
        
        await self.send_startup_message()
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="أسئلتكم عن ARC Raiders"
            )
        )
    
    async def send_startup_message(self):
        try:
            channel = self.get_channel(LOG_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🚀 البوت شغال!",
                    description=f"""
✅ **دليل** جاهز للخدمة!

📊 **الإحصائيات:**
• العناصر: {self.database.get_stats()['total']:,}
• الحالة: متصل ✅
• الإصدار: {BOT_VERSION}

⏰ **وقت التشغيل:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """,
                    color=COLORS["success"],
                    timestamp=datetime.now()
                )
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"خطأ في إرسال رسالة البدء: {e}")
    
    def get_uptime(self) -> str:
        if not self.start_time:
            return "غير معروف"
        
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours} ساعة, {minutes} دقيقة, {seconds} ثانية"


# إنشاء البوت
bot = DaleelBot()

# ═══════════════════════════════════════════════════════════════
# الأوامر - Commands
# ═══════════════════════════════════════════════════════════════

@bot.tree.command(name="help", description="عرض المساعدة")
async def help_command(interaction: discord.Interaction):
    if interaction.channel and interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("استخدم قناة الأسئلة المخصصة فقط.", ephemeral=True)
        return
        
    embed = discord.Embed(
        title="📖 مساعدة دليل",
        description="أنا **دليل** - مساعدك الذكي لعالم ARC Raiders!",
        color=COLORS["info"]
    )
    
    embed.add_field(
        name="💬 كيف تسألني؟",
        value="اكتب سؤالك مباشرة في القناة وراح أجاوبك!",
        inline=False
    )
    
    embed.add_field(
        name="📝 أمثلة أسئلة:",
        value="""
• `دليل وين أحصل Rusted Gear؟`
• `دليل كيف أهزم الـ Queen؟`
• `دليل وش أفضل سلاح للمبتدئين؟`
        """,
        inline=False
    )
    
    embed.add_field(
        name="⚡ الأوامر:",
        value="""
• `/help` - عرض المساعدة
• `/stats` - إحصائيات البوت
• `/search [كلمة]` - بحث في قاعدة البيانات
• `/checkwiki` - فحص اتصال الويكي
        """,
        inline=False
    )
    
    embed.set_footer(text=f"🤖 {BOT_NAME} v{BOT_VERSION}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="stats", description="عرض إحصائيات البوت")
async def stats_command(interaction: discord.Interaction):
    if interaction.channel and interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("استخدم قناة الأسئلة المخصصة فقط.", ephemeral=True)
        return
        
    embed = EmbedBuilder.stats_embed(
        bot.database.get_stats(),
        bot.ai_manager.usage_stats,
        bot.get_uptime()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="search", description="بحث في قاعدة البيانات")
@app_commands.describe(query="كلمة البحث")
async def search_command(interaction: discord.Interaction, query: str):
    if interaction.channel and interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("استخدم قناة الأسئلة المخصصة فقط.", ephemeral=True)
        return
        
    await interaction.response.defer()
    
    results = bot.search_engine.search(query, limit=5)
    
    if not results:
        embed = EmbedBuilder.warning(
            "لا نتائج",
            f"ما لقيت نتائج لـ **{query}**\n\nجرب كلمات مختلفة!"
        )
        await interaction.followup.send(embed=embed)
        return
    
    embed = discord.Embed(
        title=f"🔍 نتائج البحث: {query}",
        color=COLORS["info"],
        timestamp=datetime.now()
    )
    
    for i, result in enumerate(results, 1):
        item = result['item']
        name = bot.search_engine.extract_name(item)
        score = int(result['score'] * 100)
        
        category = item.get('category') or item.get('type')
        if isinstance(category, dict):
            category = category.get('en') or list(category.values())[0]
        category = category or 'غير محدد'
        
        embed.add_field(
            name=f"{i}. {name}",
            value=f"📁 {category} | 🎯 تطابق: {score}%",
            inline=False
        )
    
    embed.set_footer(text=f"🤖 {BOT_NAME}")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="checkwiki", description="فحص اتصال البوت بويكي ARC Raiders")
async def check_wiki_command(interaction: discord.Interaction):
    if interaction.channel and interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("استخدم قناة الأسئلة المخصصة فقط.", ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    
    try:
        # نجرب نجيب صفحة معروفة
        wiki_data = await fetch_doc_snippet("Rusted_Gear")
        
        if wiki_data.get("found"):
            sources = wiki_data.get("sources", [])
            guide = wiki_data.get("guide", "")[:200]
            
            response = f"✅ **أقدر أوصل لويكي ARC Raiders!**\n\n"
            response += f"**اختبار على Rusted Gear:**\n"
            
            if sources:
                response += f"• المصادر: {', '.join(sources[:5])}\n"
            if guide:
                response += f"• الدليل: {guide}...\n"
            if wiki_data.get("rarity"):
                response += f"• الندرة: {wiki_data['rarity']}\n"
            
            await interaction.followup.send(response, ephemeral=True)
        else:
            await interaction.followup.send(
                "⚠️ حاولت أوصل لويكي ARC Raiders بس ما لقيت الصفحة. ممكن يكون في مشكلة بالموقع.",
                ephemeral=True
            )
    except Exception as e:
        await interaction.followup.send(
            f"❌ ما قدرت أوصل لويكي ARC Raiders.\nالخطأ: {e}",
            ephemeral=True
        )

# ═══════════════════════════════════════════════════════════════
# معالجة الرسائل
# ═══════════════════════════════════════════════════════════════

@bot.event
async def on_message(message: discord.Message):
    """معالجة الرسائل"""
    try:
        if message.author.bot:
            return
        
        if message.guild and message.guild.id != ALLOWED_GUILD_ID:
            return
        
        if message.channel.id != ALLOWED_CHANNEL_ID:
            await bot.process_commands(message)
            return
        
        content = message.content.strip()
        content_lower = content.lower()
        
        # تجاهل الرسائل القصيرة جداً
        if len(content) < 5:
            return
        
        # إزالة بادئة "دليل"
        for word in ['دليل', 'daleel']:
            if content_lower.startswith(word):
                content = content[len(word):].strip()
                break
        
        if len(content) < 3:
            return
        
        # ردود سريعة
        quick_responses = {
            'شكراً': 'العفو! 💚',
            'شكرا': 'العفو! 💚',
            'thanks': "You're welcome! 💚",
            'ممتاز': 'سعيد إني ساعدتك! 😊',
            'تمام': 'أي خدمة! 👍',
        }
        
        if content_lower in quick_responses:
            await message.reply(quick_responses[content_lower])
            return
        
        # فحص السبام
        allowed, wait_time = bot.anti_spam.check(message.author.id)
        if not allowed:
            embed = EmbedBuilder.warning(
                "انتظر قليلاً",
                f"⏰ انتظر **{wait_time}** ثانية"
            )
            await message.reply(embed=embed, delete_after=10)
            return
        
        # التحقق من البادئة أو المنشن
        is_valid_trigger = (
            content_lower.startswith('دليل') or 
            content_lower.startswith('daleel') or 
            (bot.user in message.mentions)
        )
        
        # التحقق من الرد على البوت
        if message.reference:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                if ref_msg.author.id == bot.user.id:
                    is_valid_trigger = True
            except:
                pass
        
        if not is_valid_trigger:
            await bot.process_commands(message)
            return
        
        # معالجة السؤال
        question = bot.context_manager.inject_context(message.author.id, content)
        
        # استخدام AI للإجابة
        await ask_ai_and_reply(message, question)
        
    except Exception as e:
        logger.error(f"خطأ في on_message: {e}", exc_info=True)
        try:
            embed = EmbedBuilder.error(
                "خطأ غير متوقع",
                "صار خطأ داخل البوت. لو تكرر، بلغ الإدارة."
            )
            await message.reply(embed=embed)
        except:
            pass


async def ask_ai_and_reply(message: discord.Message, question: str):
    """سؤال الـ AI والرد"""
    thinking_msg = await message.reply("🔍 أبحث لك...")
    
    context = ""
    wiki_data = None  # نحفظ بيانات الويكي للتحقق لاحقاً
    
    # سياق المحادثة السابقة
    user_context = bot.context_manager.get_context(message.author.id)
    if user_context:
        context = f"المستخدم كان يسأل عن: {user_context['item']}"
    
    q_lower = question.lower()
    
    # البحث في قاعدة البيانات
    focus_item = None
    focus_item_name = None
    
    try:
        search_results = bot.search_engine.search(question, limit=1)
        if search_results and search_results[0]['score'] > 0.4:
            focus_item = search_results[0]['item']
            focus_item_name = bot.search_engine.extract_name(focus_item)
    except:
        pass
    
    # ═══════════════════════════════════════════════════════════
    # إضافة سياق ثابت للمواضيع المعروفة
    # ═══════════════════════════════════════════════════════════
    
    static_contexts = {
        'expedition': (
            ['expedition project', 'expedition', 'البروجيكت', 'بروجيكت'],
            "Expedition Project ينفتح عند ليفل 20 كنظام يعيد تقدم الرايدر بشكل اختياري. "
            "كل دورة ثمانية أسابيع؛ سبعة للتحضير والثامن لإنهاء البروجيكت."
        ),
        'speranza': (
            ['speranza', 'سبيرانزا', 'الملجأ'],
            "Speranza مستوطنة تحت الأرض آمنة من تهديد ARC على السطح، "
            "ترجع لها بعد المهمات للمكافآت والتجار والتطوير."
        ),
        'workshop': (
            ['workshop', 'الوركشوب', 'الورشة'],
            "الـ Workshop مكان تطوير العتاد والأسلحة وتصليحها وفتح وصفات جديدة."
        ),
        'traders': (
            ['traders', 'trader', 'التجار', 'تاجر'],
            "التُجّار في Speranza يقدمون مهمات ومكافآت وبيع وشراء الأغراض."
        ),
        'scrappy': (
            ['scrappy', 'الديك', 'ديكي'],
            "Scrappy رفيقك الديك اللي يجمع الأغراض ويلقط اللوت حتى لو خسرت."
        ),
    }
    
    for key, (keywords, ctx_text) in static_contexts.items():
        if any(k in q_lower for k in keywords):
            if context:
                context = context + " | " + ctx_text
            else:
                context = ctx_text
            break
    
    # ═══════════════════════════════════════════════════════════
    # جلب معلومات من الويكي (المحسّن)
    # ═══════════════════════════════════════════════════════════
    
    focus_name = focus_item_name
    if not focus_name:
        # استخراج الكلمات الإنجليزية من السؤال
        matches = re.findall(r'[A-Za-z][A-Za-z0-9\s\-_]+', question)
        if matches:
            focus_name = max(matches, key=len).strip()
    
    if focus_name:
        wiki_data = await fetch_doc_snippet(focus_name)
        wiki_context = build_wiki_context(wiki_data)
        
        if wiki_context:
            if context:
                context = context + "\n\n" + wiki_context
            else:
                context = wiki_context
    
    # ═══════════════════════════════════════════════════════════
    # تحديد نوع السؤال وبناء الـ Prompt
    # ═══════════════════════════════════════════════════════════
    
    location_keywords = ['وين', 'اين', 'أين', 'فين', 'location', 'where', 'place', 'spot', 'spawn']
    obtain_keywords = ['كيف احصل', 'كيف أجيب', 'من وين', 'drop', 'drops', 'loot', 'يطيح']
    crafting_keywords = ['recipe', 'craft', 'تصنع', 'تصنيع', 'مخطط', 'متطلبات', 'مكونات']
    
    is_location_question = any(k in q_lower for k in location_keywords)
    is_obtain_question = any(k in q_lower for k in obtain_keywords)
    is_crafting_question = any(k in q_lower for k in crafting_keywords)
    
    # بناء style_hint حسب نوع السؤال
    if is_location_question or is_obtain_question:
        style_hint = (
            "هذا سؤال عن مكان الحصول على غرض في ARC Raiders.\n"
            "جاوب بأسلوب لاعب خبير مختصر بثلاث جمل:\n"
            "1) اذكر الحاويات/المصادر اللي يطلع منها (مثل: Car Hoods, Buses, Metal Crates).\n"
            "2) اذكر أسماء المناطق الحقيقية بالإنجليزي كما في الويكي.\n"
            "3) نصيحة سريعة للاعب.\n\n"
            "⚠️ مهم: استخدم فقط أسماء المناطق من الويكي. لا تخترع أسماء مثل 'Industrial Zone'.\n"
            "المناطق الرئيسية: Dam Battlegrounds, The Spaceport, Buried City, The Blue Gate, Stella Montis."
        )
    elif is_crafting_question:
        style_hint = (
            "هذا سؤال عن التصنيع. أجب بثلاث جمل:\n"
            "1) متى ولماذا يحتاج اللاعب هذا الغرض.\n"
            "2) فكرة سريعة عن نوع الموارد المطلوبة.\n"
            "3) نصيحة مختصرة عن التصنيع."
        )
    else:
        style_hint = (
            "اشرح الفكرة بأسلوب لاعب خبير لكن بسيط.\n"
            "إجابتك بين جملتين وثلاث جمل فقط، تركز على أهم معلومة."
        )
    
    ai_prompt = (
        f"{style_hint}\n\n"
        f"سؤال اللاعب: {question}\n\n"
        "اكتب الإجابة بالعربي البسيط بدون قوائم أو تعداد."
    )
    
    # ═══════════════════════════════════════════════════════════
    # سؤال الـ AI
    # ═══════════════════════════════════════════════════════════
    
    ai_result = await bot.ai_manager.ask_ai(ai_prompt, context)
    
    await thinking_msg.delete()
    
    if ai_result['success']:
        answer = ai_result['answer']
        
        # ✅ التحقق من صحة الرد (المناطق الوهمية)
        answer = validate_ai_response(answer, wiki_data)
        
        embed = discord.Embed(
            description=answer,
            color=COLORS["success"],
            timestamp=datetime.now()
        )
        
        # إضافة صورة لو موجودة
        if focus_item:
            img_url = EmbedBuilder.get_image_url(focus_item)
            if img_url:
                embed.set_thumbnail(url=img_url)
        
        embed.set_footer(text=f"🤖 {BOT_NAME}")
    else:
        embed = EmbedBuilder.error(
            "عذراً",
            "ما قدرت ألقى جواب.\n\n💡 جرب صياغة السؤال بطريقة مختلفة!"
        )
    
    await reply_with_feedback(message, embed)
    
    # حفظ السياق
    if focus_item_name and focus_item:
        bot.context_manager.set_context(message.author.id, focus_item_name, focus_item)
    
    bot.questions_answered += 1

# ═══════════════════════════════════════════════════════════════
# التشغيل
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN غير موجود!")
        exit(1)
    
    logger.info("🚀 جاري تشغيل البوت...")
    bot.run(DISCORD_TOKEN)
