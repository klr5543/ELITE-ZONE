"""
╔══════════════════════════════════════════════════════════════╗
║                    بوت دليل - Daleel Bot                      ║
║              Q&A Bot for ARC Raiders Community                ║
║                     By: SPECTRE Leader                        ║
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
BOT_VERSION = "2.0.1"

# وضع عمل الذكاء الاصطناعي
# "hybrid" = يستخدم الداتا + AI (الوضع القديم)
# "ai_only" = يتجاهل الداتا ويستخدم AI فقط
AI_MODE = os.getenv("AI_MODE", "ai_only").lower()

# قاموس عربي-إنجليزي للكلمات الشائعة
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


def is_comparative_question(text: str) -> bool:
    lowered = text.lower()
    tokens = [
        " vs ",
        "vs ",
        " افضل ",
        "أفضل",
        "احسن",
        "أحسن",
        " or ",
        " or",
        "or ",
        "ولا",
        "مقارنة",
        "better",
        "best",
    ]
    return any(token in lowered for token in tokens)


def is_strategy_question(text: str) -> bool:
    lowered = text.lower()
    tokens = [
        "استراتيجية",
        "strategy",
        "كيف العب",
        "كيف ألعب",
        "build",
        "بيلد",
        "meta",
        "ميتا",
        "طريقة اللعب",
    ]
    return any(token in lowered for token in tokens)


def is_explanatory_question(text: str) -> bool:
    lowered = text.lower()
    tokens = [
        "ليش",
        "لماذا",
        "why",
        "سبب",
        "اشرح",
        "شرح",
        "explain",
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

# روابط الصور من GitHub
IMAGES_BASE_URL = "https://raw.githubusercontent.com/RaidTheory/arcraiders-data/main/images"

# Colors
COLORS = {
    "success": 0x2ecc71,    # أخضر
    "error": 0xe74c3c,      # أحمر
    "warning": 0xf39c12,    # برتقالي
    "info": 0x3498db,       # أزرق
    "primary": 0x9b59b6,    # بنفسجي
}

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Daleel')

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
            # ═══════════════════════════════════════════════════
            # تحميل المجلدات
            # ═══════════════════════════════════════════════════
            
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
            
            # ═══════════════════════════════════════════════════
            # تحميل ملفات JSON الرئيسية
            # ═══════════════════════════════════════════════════
            
            # bots.json - الأعداء
            bots_file = base_path / 'bots.json'
            if bots_file.exists():
                try:
                    with open(bots_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.bots = data
                        elif isinstance(data, dict):
                            self.bots = [data]
                    logger.info(f"✅ تم تحميل {len(self.bots)} بوت/عدو")
                except Exception as e:
                    logger.error(f"خطأ في تحميل bots.json: {e}")
            
            # maps.json - الخرائط
            maps_file = base_path / 'maps.json'
            if maps_file.exists():
                try:
                    with open(maps_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.maps = data
                        elif isinstance(data, dict):
                            self.maps = [data]
                    logger.info(f"✅ تم تحميل {len(self.maps)} خريطة")
                except Exception as e:
                    logger.error(f"خطأ في تحميل maps.json: {e}")
            
            # trades.json - التجارة
            trades_file = base_path / 'trades.json'
            if trades_file.exists():
                try:
                    with open(trades_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.trades = data
                        elif isinstance(data, dict):
                            self.trades = [data]
                    logger.info(f"✅ تم تحميل {len(self.trades)} تجارة")
                except Exception as e:
                    logger.error(f"خطأ في تحميل trades.json: {e}")
            
            # skillNodes.json - المهارات
            skills_file = base_path / 'skillNodes.json'
            if skills_file.exists():
                try:
                    with open(skills_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.skills = data
                        elif isinstance(data, dict):
                            self.skills = [data]
                    logger.info(f"✅ تم تحميل {len(self.skills)} مهارة")
                except Exception as e:
                    logger.error(f"خطأ في تحميل skillNodes.json: {e}")
            
            # projects.json - المشاريع
            projects_file = base_path / 'projects.json'
            if projects_file.exists():
                try:
                    with open(projects_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.projects = data
                        elif isinstance(data, dict):
                            self.projects = [data]
                    logger.info(f"✅ تم تحميل {len(self.projects)} مشروع")
                except Exception as e:
                    logger.error(f"خطأ في تحميل projects.json: {e}")
            
            # ═══════════════════════════════════════════════════
            # دمج كل البيانات
            # ═══════════════════════════════════════════════════
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
        # إزالة الأحرف الخاصة
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
        # توحيد المسافات
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
        
        # تطابق تام
        if query == text:
            return 1.0
        
        # يحتوي على الاستعلام كامل
        if query in text:
            return 0.85 + (len(query) / len(text)) * 0.1
        
        # كل كلمات البحث موجودة
        query_words = query.split()
        text_lower = text.lower()
        matches = sum(1 for word in query_words if word in text_lower)
        if matches == len(query_words) and query_words:
            return 0.8 + (matches / len(query_words)) * 0.15
        
        # بعض الكلمات موجودة
        if matches > 0 and query_words:
            return 0.5 + (matches / len(query_words)) * 0.3
        
        # تشابه جزئي
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
            
            # البحث في الحقول المختلفة
            searchable_fields = ['id', 'name', 'title', 'displayName', 'description', 
                                'category', 'type', 'location', 'nameKey', 'rarity']
            
            for field in searchable_fields:
                if field not in item or not item[field]:
                    continue
                
                field_value = item[field]
                
                # لو القيمة dict (ترجمات متعددة)
                if isinstance(field_value, dict):
                    for lang, text in field_value.items():
                        if not text or not isinstance(text, str):
                            continue
                        
                        text_normalized = self.normalize_text(text)
                        
                        # بحث بالكلمة الأصلية
                        s1 = self._calculate_match_score(query_normalized, text_normalized)
                        # بحث بالكلمة المترجمة
                        s2 = self._calculate_match_score(query_translated, text_normalized)
                        
                        current_score = max(s1, s2)
                        if current_score > score:
                            score = current_score
                            matched_field = field
                    
                    if score >= 0.95:
                        break
                
                # لو القيمة string عادي
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
        """استخراج الاسم من العنصر - الإنجليزي للأسماء"""
        name_fields = ['name', 'title', 'displayName', 'nameKey']
        
        for field in name_fields:
            if field in item:
                value = item[field]
                
                # لو القيمة dict (ترجمات متعددة) - الإنجليزي أولاً
                if isinstance(value, dict):
                    return value.get('en') or value.get('ar') or list(value.values())[0]
                
                # لو القيمة string عادي
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
        # كاش للترجمات عشان ما نكرر
        self.translation_cache = {}
    
    async def translate_to_arabic(self, text: str) -> str:
        """ترجمة نص للعربي - سريع بـ Groq"""
        if not text or len(text) < 3:
            return text
        
        # تحقق من الكاش
        cache_key = text[:100]  # أول 100 حرف كـ key
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        # لو النص عربي أصلاً
        if any('\u0600' <= c <= '\u06FF' for c in text):
            return text
        
        try:
            # استخدم Groq للترجمة السريعة
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
                                {'role': 'system', 'content': 'أنت مترجم. ترجم النص التالي للعربية فقط بدون أي إضافات أو شرح. لو النص قصير جداً أو اسم، اكتبه كما هو.'},
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
                            # حفظ في الكاش
                            self.translation_cache[cache_key] = translated
                            return translated
        except Exception as e:
            logger.warning(f"خطأ في الترجمة: {e}")
        
        return text  # رجع النص الأصلي لو فشلت الترجمة
    
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
5. لو ما تعرف الجواب بدقة، استخدم أفضل معرفتك وخبرتك عن اللعبة، وقل لو المعلومة تقريبية أو غير مؤكدة، واستعمل عبارات مثل: غالباً، عادةً، حسب تجربة اللاعبين.
6. ركز على لعبة ARC Raiders فقط، ولا تتكلم عن ألعاب ثانية.
7. لا تكرر نصوصاً طويلة أو شروحات مملة؛ كن عملياً ومباشراً.
{f'السياق: {context}' if context else ''}"""
        
        # ترتيب المزودين (نفضل OpenAI و Anthropic أولاً لو المفاتيح متوفرة)
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
        """DeepSeek API"""
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
        """Groq API"""
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
        """OpenAI API"""
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
        """Anthropic Claude API"""
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
        """Google Gemini API"""
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
    """مدير سياق المحادثات - يتذكر آخر سؤال لكل مستخدم"""
    
    def __init__(self, timeout_minutes: int = 5):
        self.contexts = {}  # {user_id: {'item': ..., 'timestamp': ...}}
        self.timeout = timedelta(minutes=timeout_minutes)
    
    def set_context(self, user_id: int, item_name: str, item_data: dict = None):
        """حفظ السياق للمستخدم"""
        self.contexts[user_id] = {
            'item': item_name,
            'data': item_data,
            'timestamp': datetime.now()
        }
    
    def get_context(self, user_id: int) -> dict:
        """جلب السياق للمستخدم"""
        if user_id not in self.contexts:
            return None
        
        context = self.contexts[user_id]
        if datetime.now() - context['timestamp'] > self.timeout:
            del self.contexts[user_id]
            return None
        
        return context
    
    def clear_context(self, user_id: int):
        """مسح السياق"""
        if user_id in self.contexts:
            del self.contexts[user_id]
    
    def inject_context(self, user_id: int, question: str) -> str:
        """حقن السياق في السؤال"""
        context = self.get_context(user_id)
        if not context:
            return question
        
        # كلمات تدل على سؤال متابعة
        follow_up_keywords = [
            'نسبة', 'spawn', 'الموقع', 'location', 'وين', 'where',
            'كم', 'how much', 'الندرة', 'rarity',
            'طريقة', 'افضل طريقة', 'أفضل طريقة',
            'استراتيجية', 'strategy',
            'how to', 'how do', 'use', 'استعمل'
        ]
        
        question_lower = question.lower()
        is_follow_up = any(keyword in question_lower for keyword in follow_up_keywords)
        
        # إذا السؤال قصير جداً ويبدو متابعة
        if is_follow_up and len(question.split()) <= 5:
            return f"{context['item']} {question}"
        
        return question

# ═══════════════════════════════════════════════════════════════
# نظام الحماية - Anti-Spam
# ═══════════════════════════════════════════════════════════════

class AntiSpam:
    """نظام منع السبام - 3 أسئلة/دقيقة"""
    
    def __init__(self, max_messages: int = 3, window_seconds: int = 60):
        self.user_messages = {}  # {user_id: [timestamps]}
        self.max_messages = max_messages
        self.window = timedelta(seconds=window_seconds)
    
    def check(self, user_id: int) -> tuple:
        """فحص إذا المستخدم يقدر يرسل"""
        now = datetime.now()
        
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        # تنظيف الرسائل القديمة
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
        """استخراج قيمة حقل - الإنجليزي للأسماء"""
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
        """الحصول على رابط صورة العنصر"""
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
    def clean_description(text: str) -> str:
        """تنظيف الوصف من النصوص الروسية والشوائب"""
        if not text:
            return text
        text = text.replace('запасية', 'احتياطية')
        return text

    @staticmethod
    def item_embed(item: dict, translated_desc: str = None) -> discord.Embed:
        """إنشاء Embed لعنصر من اللعبة - الاسم إنجليزي والباقي عربي"""
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
            description = EmbedBuilder.clean_description(translated_desc)
        else:
            description = None
            if 'description' in item:
                desc_val = item['description']
                if isinstance(desc_val, dict):
                    description = desc_val.get('en') or desc_val.get('ar') or list(desc_val.values())[0]
                else:
                    description = str(desc_val)
            description = EmbedBuilder.clean_description(description or 'لا يوجد وصف')
        
        minimal_mode = False
        if description:
            td = str(description)
            if any(x in td for x in ["المنطقة:", "الموقع:", "المنطقة العامة:", "نسبة الظهور", "التجار", "السعر"]):
                minimal_mode = True
        
        embed = discord.Embed(
            title=f"📦 {name}",
            description=description[:500] if description else "لا يوجد وصف",
            color=COLORS["primary"],
            timestamp=datetime.now()
        )
        
        if not minimal_mode:
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
            
            location = EmbedBuilder.extract_field(item, 'location')
            if location:
                embed.add_field(name="📍 الموقع", value=location, inline=True)
            
            spawn_rate = item.get('spawnRate') or item.get('spawn_rate')
            if spawn_rate:
                embed.add_field(name="📊 نسبة الظهور", value=f"{spawn_rate}%", inline=True)
            
            price = item.get('price') or item.get('value')
            if price:
                embed.add_field(name="💰 السعر", value=str(price), inline=True)
        
        suppress_obtain_field = False
        if translated_desc:
            td = str(translated_desc)
            if any(x in td for x in ["المنطقة:", "الموقع:", "نسبة الظهور", "التجار", "السعر"]):
                suppress_obtain_field = True
                if minimal_mode:
                    suppress_obtain_field = True
        
        obtain_lines = []
        found_in = item.get('foundIn')
        if found_in:
            obtain_lines.append(f"- يوجد في: {found_in}")
        craft_bench = item.get('craftBench')
        if craft_bench:
            obtain_lines.append(f"- يتصنع في: {craft_bench}")
        recipe = item.get('recipe')
        if isinstance(recipe, dict) and recipe:
            obtain_lines.append("- له وصفة تصنيع، شوف تفاصيل التصنيع")
        drops = item.get('drops')
        if isinstance(drops, list) and drops:
            obtain_lines.append(f"- يسقط من: {len(drops)} عدو/بوس")
        traders = item.get('traders') or item.get('soldBy')
        if traders:
            obtain_lines.append("- متوفر عند التجار")
        if obtain_lines and not suppress_obtain_field:
            embed.add_field(name="طرق الحصول", value="\n".join(obtain_lines), inline=False)
        
        img_url = EmbedBuilder.get_image_url(item)
        if img_url:
            embed.set_thumbnail(url=img_url)
        
        embed.set_footer(text=f"🤖 {BOT_NAME} | ARC Raiders")
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
    
    @staticmethod
    def map_embed(map_name: str, map_data: dict = None) -> discord.Embed:
        """إنشاء Embed للخريطة مع الصورة"""
        embed = discord.Embed(
            title=f"🗺️ خريطة: {map_name}",
            color=COLORS["info"],
            timestamp=datetime.now()
        )
        
        # صورة الخريطة الكبيرة
        map_id = map_data.get('id') if map_data else map_name.lower().replace(' ', '_')
        map_url = f"{IMAGES_BASE_URL}/maps/{map_id}.png"
        embed.set_image(url=map_url)
        
        if map_data:
            if map_data.get('description'):
                desc = map_data['description']
                if isinstance(desc, dict):
                    desc = desc.get('en', '')
                embed.description = desc[:500]
        
        embed.set_footer(text=f"🤖 {BOT_NAME} | ARC Raiders")
        return embed
    
    @staticmethod
    def stats_embed(db_stats: dict, ai_stats: dict, uptime: str) -> discord.Embed:
        """إنشاء Embed للإحصائيات"""
        embed = discord.Embed(
            title="📊 إحصائيات دليل",
            color=COLORS["info"],
            timestamp=datetime.now()
        )
        
        # إحصائيات قاعدة البيانات
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
        
        # إحصائيات AI
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
        
        # المكونات
        self.database = DatabaseManager()
        self.search_engine = None
        self.ai_manager = AIManager()
        self.context_manager = ContextManager()
        self.anti_spam = AntiSpam()
        
        # الإحصائيات
        self.start_time = None
        self.questions_answered = 0
        
    async def setup_hook(self):
        """إعداد البوت"""
        # تحميل قاعدة البيانات
        self.database.load_all()
        self.search_engine = SearchEngine(self.database)
        
        # مزامنة الأوامر
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ تم مزامنة {len(synced)} أمر")
        except Exception as e:
            logger.error(f"خطأ في المزامنة: {e}")
    
    async def on_ready(self):
        """عند جاهزية البوت"""
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
        
        # إرسال رسالة للقناة
        await self.send_startup_message()
        
        # تحديث الحالة
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="أسئلتكم عن ARC Raiders"
            )
        )
    
    async def send_startup_message(self):
        """إرسال رسالة بدء التشغيل"""
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

⏰ **وقت التشغيل:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """,
                    color=COLORS["success"],
                    timestamp=datetime.now()
                )
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"خطأ في إرسال رسالة البدء: {e}")
    
    def get_uptime(self) -> str:
        """حساب وقت التشغيل"""
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
    """أمر المساعدة"""
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
• `وين أحصل Rusted Gear؟`
• `كيف أهزم الـ Queen؟`
• `وش أفضل سلاح للمبتدئين؟`
• `spawn rate للـ Ferro Handgun`
        """,
        inline=False
    )
    
    embed.add_field(
        name="⚡ الأوامر:",
        value="""
• `/help` - عرض المساعدة
• `/stats` - إحصائيات البوت
• `/search [كلمة]` - بحث في قاعدة البيانات
        """,
        inline=False
    )
    
    embed.set_footer(text=f"🤖 {BOT_NAME} v{BOT_VERSION}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stats", description="عرض إحصائيات البوت")
async def stats_command(interaction: discord.Interaction):
    """أمر الإحصائيات"""
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
    """أمر البحث"""
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
        
        # استخراج الفئة
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
        
        ignore_words = [
            'دليل', 'daleel', 'bot', 'بوت',
            'هاي', 'hi', 'hello', 'مرحبا', 'السلام',
            'هلا', 'اهلا', 'hey', 'yo'
        ]
        
        if len(content) < 5 or content_lower in ignore_words:
            return
        
        for word in ['دليل', 'daleel']:
            if content_lower.startswith(word):
                content = content[len(word):].strip()
                break
        
        if len(content) < 3:
            return
        
        quick_responses = {
            'شكراً': 'العفو! 💚',
            'شكرا': 'العفو! 💚',
            'thanks': "You're welcome! 💚",
            'thank you': "You're welcome! 💚",
            'ممتاز': 'سعيد إني ساعدتك! 😊',
            'رائع': 'دائماً في الخدمة! 🎮',
            'تمام': 'أي خدمة! 👍',
            'حلو': 'شكراً! 😊',
            'good': 'Thanks! 😊'
        }
        
        if content_lower in quick_responses:
            await message.reply(quick_responses[content_lower])
            return
        
        allowed, wait_time = bot.anti_spam.check(message.author.id)
        if not allowed:
            embed = EmbedBuilder.warning(
                "انتظر قليلاً",
                f"⏰ انتظر **{wait_time}** ثانية"
            )
            await message.reply(embed=embed, delete_after=10)
            return
        
        requires_prefix = False
        if requires_prefix:
            is_reply_to_bot = False
            if message.reference:
                ref_msg = getattr(message.reference, 'resolved', None)
                if not ref_msg and getattr(message.reference, 'message_id', None):
                    try:
                        ref_msg = await message.channel.fetch_message(message.reference.message_id)
                    except Exception:
                        ref_msg = None
                if ref_msg and ref_msg.author and bot.user and ref_msg.author.id == bot.user.id:
                    is_reply_to_bot = True
            if not (content_lower.startswith('دليل') or content_lower.startswith('daleel') or (bot.user in message.mentions) or is_reply_to_bot):
                await bot.process_commands(message)
                return
        
        user_ctx = bot.context_manager.get_context(message.author.id)
        if not user_ctx and message.reference:
            ref_msg = getattr(message.reference, 'resolved', None)
            if not ref_msg and getattr(message.reference, 'message_id', None):
                try:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                except Exception:
                    ref_msg = None
            if ref_msg and ref_msg.author and bot.user and ref_msg.author.id == bot.user.id:
                ref_embeds = getattr(ref_msg, 'embeds', []) or []
                ref_title = ref_embeds[0].title if ref_embeds else None
                if ref_title:
                    t = ref_title.strip()
                    if t.startswith("🧭 منطقة اللوت: "):
                        zone_display = t.split(": ", 1)[1].strip()
                        bot.context_manager.set_context(message.author.id, zone_display, None)
                    elif t.startswith("🗺️ خريطة: "):
                        map_name = t.split(": ", 1)[1].strip()
                        bot.context_manager.set_context(message.author.id, map_name, None)
                    elif t.startswith("📦 "):
                        item_name = t[2:].strip()
                        bot.context_manager.set_context(message.author.id, item_name, None)
                    elif t.startswith("⚖️ مقارنة: "):
                        comp_part = t.split(": ", 1)[1].strip()
                        left_name = comp_part.split(" vs ", 1)[0].strip() if " vs " in comp_part else comp_part
                        if left_name:
                            bot.context_manager.set_context(message.author.id, left_name, None)
                    else:
                        guess_results = bot.search_engine.search(t, limit=1)
                        if guess_results:
                            gitem = guess_results[0]['item']
                            gname = bot.search_engine.extract_name(gitem)
                            bot.context_manager.set_context(message.author.id, gname, gitem)
                        else:
                            bot.context_manager.set_context(message.author.id, t, None)
        
        original_content = content
        question = bot.context_manager.inject_context(message.author.id, content)
        if question != original_content and message.reference:
            ref_msg = getattr(message.reference, 'resolved', None)
            if not ref_msg and getattr(message.reference, 'message_id', None):
                try:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                except Exception:
                    ref_msg = None
            if ref_msg and ref_msg.author and bot.user and ref_msg.author.id == bot.user.id:
                try:
                    await message.add_reaction('👀')
                except Exception:
                    pass
        if question.startswith('دليل '):
            question = question[5:]
    except Exception as e:
        logger.error(f"خطأ في on_message: {e}", exc_info=True)
        try:
            embed = EmbedBuilder.error(
                "خطأ غير متوقع",
                "صار خطأ داخل البوت.\nلو تكرر، بلغ الإدارة مع صورة من الرسالة."
            )
            await message.reply(embed=embed)
        except Exception:
            pass
        return
    
    if AI_MODE == "ai_only":
        await ask_ai_and_reply(message, question)
        return
    
    crafting_keywords = [
        'ادوات', 'أدوات',
        'تصنع', 'تصنيع',
        'تسوي', 'أسوي', 'اسوي',
        'أصنع', 'اصنع', 'أصنعه', 'اصنعه', 'أصنعها', 'اصنعها',
        'recipe', 'craft',
        'مكونات', 'مخطط',
        'متطلبات', 'متطلباته', 'متطلباتها'
    ]
    is_crafting_question = any(keyword in content_lower for keyword in crafting_keywords)
    
    location_keywords = ['وين', 'اين', 'أين', 'مكان', 'موقع', 'القى', 'الاقي', 'احصل', 'where', 'location', 'find']
    is_location_question = any(keyword in content_lower for keyword in location_keywords)
    
    obtain_keywords = [
        'كيف احصل', 'كيف أجيب', 'كيف اجيب',
        'من وين', 'من وين اجيب', 'من وين احصل',
        'وين القا', 'وين القى', 'وين القاء',
        'الفلارات', 'فلارات',
        'drop', 'drops', 'loot',
        'يطيح', 'يطيحه', 'يندر', 'يطلع'
    ]
    is_obtain_question = any(keyword in content_lower for keyword in obtain_keywords)
    
    is_queen_query = any(
        term in content_lower for term in ['queen', 'كوين', 'الكوين']
    )
    
    if is_queen_query:
        queen_candidates = [
            b for b in bot.database.bots
            if isinstance(b, dict)
            and 'name' in b
            and isinstance(b['name'], str)
            and 'queen' in b['name'].lower()
        ]
        if queen_candidates:
            item = queen_candidates[0]
            description = None
            if 'description' in item:
                desc_val = item['description']
                if isinstance(desc_val, dict):
                    description = desc_val.get('en') or desc_val.get('ar') or list(desc_val.values())[0]
                else:
                    description = str(desc_val)
            translated_desc = None
            if description and description != 'لا يوجد وصف':
                translated_desc = await bot.ai_manager.translate_to_arabic(description)
            if is_obtain_question or is_location_question:
                obtain_info = []
                found_in = item.get('foundIn')
                if found_in:
                    obtain_info.append(f"📍 المنطقة: {found_in}")
                location_field = item.get('location') or item.get('spawn_location') or item.get('map')
                if location_field and location_field != found_in:
                    if isinstance(location_field, dict):
                        location_field = location_field.get('en') or location_field.get('ar') or list(location_field.values())[0]
                    obtain_info.append(f"🗺️ الموقع: {location_field}")
                spawn_rate = item.get('spawnRate') or item.get('spawn_rate')
                if spawn_rate:
                    obtain_info.append(f"📊 نسبة الظهور: {spawn_rate}%")
                craft_bench = item.get('craftBench')
                recipe = item.get('recipe') if isinstance(item.get('recipe'), dict) else None
                if craft_bench or recipe:
                    if craft_bench:
                        obtain_info.append(f"🔨 التصنيع: {craft_bench}")
                    else:
                        obtain_info.append("🔨 التصنيع: متاح (شوف تفاصيل الوصفة)")
                drops_list = item.get('drops')
                if isinstance(drops_list, list) and len(drops_list) > 0:
                    obtain_info.append(f"💀 يسقط من: {len(drops_list)} عدو/بوس")
                traders = item.get('traders') or item.get('soldBy')
                if traders:
                    obtain_info.append("💰 التجار: متوفر للشراء")
                price = item.get('price') or item.get('value')
                if price:
                    obtain_info.append(f"💵 السعر: {price}")
                if not obtain_info:
                    obtain_info.append("⚠️ معلومات المكان غير متوفرة في الداتا")
                    if translated_desc and translated_desc != 'لا يوجد وصف':
                        obtain_info.append(f"📝 {translated_desc[:150]}")
                custom_desc = "\n".join(obtain_info)
                embed = EmbedBuilder.item_embed(item, custom_desc)
            else:
                embed = EmbedBuilder.item_embed(item, translated_desc)
            drops = item.get('drops') or []
            if drops and isinstance(drops, list):
                drop_lines = []
                for drop_id in drops:
                    drop_item = next(
                        (it for it in bot.database.items if isinstance(it, dict) and it.get('id') == drop_id),
                        None
                    )
                    if drop_item:
                        drop_name = bot.search_engine.extract_name(drop_item)
                        drop_lines.append(f"- {drop_name}")
                    else:
                        drop_lines.append(f"- {drop_id}")
                if drop_lines:
                    embed.add_field(
                        name="القطع التي تسقط منها",
                        value="\n".join(drop_lines),
                        inline=False
                    )
            reply = await reply_with_feedback(message, embed)
            if use_ai and (is_crafting_question or is_obtain_question or is_location_question):
                ai_context_parts = []
                name_for_ai = bot.search_engine.extract_name(item)
                ai_context_parts.append(f"الآيتم: {name_for_ai}")
                ai_context_parts.append("تنبيه للنظام: المستخدم رأى بالفعل بطاقة المعلومات الكاملة (الدروب، الموقع، الوصف) من قاعدة البيانات.")
                ai_context_parts.append("مهم جداً: لا تكرر قائمة العناصر أو الدروب أو المعلومات الموجودة في البطاقة أبداً.")
                ai_context_parts.append("لا ترسل إيموجيات قوائم أو تكرر المحتوى.")
                ai_context_parts.append("المطلوب: قدم فقط نصيحة استراتيجية ذكية ومختصرة (سطرين كحد أقصى) عن كيفية القتال أو الاستخدام الأمثل.")
                
                if is_obtain_question:
                    ai_context_parts.append("السؤال عن استراتيجية الحصول.")
                if is_crafting_question:
                    ai_context_parts.append("السؤال عن نصائح التصنيع.")
                if is_location_question:
                    ai_context_parts.append("السؤال عن كيفية الوصول للموقع.")

                ai_context = " | ".join(ai_context_parts)
                await ask_ai_and_reply(
                    message,
                    f"{ai_context}\n\nسؤال اللاعب: {question}"
                )
            name = bot.search_engine.extract_name(item)
            bot.context_manager.set_context(message.author.id, name, item)
            # الأزرار تغني عن ردود ✅❌
            bot.questions_answered += 1
            return
    
    if is_comparative_question(content):
        names = re.findall(r'[A-Za-z][A-Za-z ]+', content)
        unique = []
        for n in names:
            nn = n.strip()
            if nn and nn.lower() not in [x.lower() for x in unique]:
                unique.append(nn)
        if len(unique) >= 2:
            left_name, right_name = unique[0], unique[1]
            left_results = bot.search_engine.search(left_name, limit=1)
            right_results = bot.search_engine.search(right_name, limit=1)
            if left_results and right_results:
                left_item = left_results[0]['item']
                right_item = right_results[0]['item']
                def summarize(it):
                    n = bot.search_engine.extract_name(it)
                    cat = EmbedBuilder.extract_field(it, 'category') or ''
                    typ = EmbedBuilder.extract_field(it, 'type') or ''
                    rar = EmbedBuilder.extract_field(it, 'rarity') or ''
                    price = it.get('price') or it.get('value') or ''
                    found = it.get('foundIn') or ''
                    bench = it.get('craftBench') or ''
                    recipe = it.get('recipe') if isinstance(it.get('recipe'), dict) else None
                    rcount = len(recipe) if recipe else 0
                    parts = []
                    if cat: parts.append(f"الفئة: {cat}")
                    if typ: parts.append(f"النوع: {typ}")
                    if rar: parts.append(f"الندرة: {rar}")
                    if price: parts.append(f"السعر: {price}")
                    if found: parts.append(f"يوجد في: {found}")
                    if bench: parts.append(f"يتصنع في: {bench}")
                    if rcount: parts.append(f"تعقيد التصنيع: {rcount} جزء")
                    return n, "\n".join(parts) if parts else "لا توجد بيانات كافية"
                ln, ltext = summarize(left_item)
                rn, rtext = summarize(right_item)
                embed = discord.Embed(
                    title=f"⚖️ مقارنة: {ln} vs {rn}",
                    color=COLORS["info"],
                    timestamp=datetime.now()
                )
                embed.add_field(name=ln, value=ltext, inline=True)
                embed.add_field(name=rn, value=rtext, inline=True)
                def rarity_score(r):
                    m = {'common':1,'uncommon':2,'rare':3,'epic':4,'legendary':5}
                    rv = str(r).lower()
                    return m.get(rv, 0)
                ls = rarity_score(EmbedBuilder.extract_field(left_item, 'rarity') or '')
                rs = rarity_score(EmbedBuilder.extract_field(right_item, 'rarity') or '')
                lp = left_item.get('price') or left_item.get('value') or 0
                rp = right_item.get('price') or right_item.get('value') or 0
                lrc = len(left_item.get('recipe')) if isinstance(left_item.get('recipe'), dict) else 0
                rrc = len(right_item.get('recipe')) if isinstance(right_item.get('recipe'), dict) else 0
                choice = ln
                reason = "ندرة أعلى" if ls>rs else ("سعر أعلى عادة أقوى" if lp>rp else ("تصنيع أبسط" if lrc<rrc else "تقارب، اختر حسب أسلوبك"))
                if rs>ls or (lp>rp and rs>=ls) or (rrc<lrc and rs>=ls):
                    choice = rn
                    reason = "ندرة أعلى" if rs>ls else ("سعر أعلى عادة أقوى" if rp>lp else ("تصنيع أبسط" if rrc<lrc else "تقارب، اختر حسب أسلوبك"))
                embed.add_field(name="الرأي المختصر", value=f"أنصح بـ {choice} ({reason}).", inline=False)
                reply = await reply_with_feedback(message, embed)
                bot.context_manager.set_context(message.author.id, choice, left_item if choice==ln else right_item)
                bot.questions_answered += 1
                return

    # تصحيح أخطاء إملائية شائعة
    typo_corrections = {
        'have': 'heavy',
        'heve': 'heavy',
        'hevy': 'heavy',
        'ligh': 'light',
        'lit': 'light',
        'complx': 'complex',
        'cmplex': 'complex'
    }
    
    english_words = re.findall(r'[a-zA-Z_]+', content)
    english_words_lower = [typo_corrections.get(w.lower(), w.lower()) for w in english_words]
    search_query = question
    main_word = None
    if (is_crafting_question or is_location_question or is_obtain_question) and english_words_lower:
        id_like = next((w for w in english_words_lower if '_' in w), None)
        if id_like:
            main_word = id_like
            search_query = main_word
        else:
            query_words = {'spawn', 'rate', 'drop', 'drops', 'location', 'where', 'find', 'how', 'much', 'spawnrate'}
            item_words = [w for w in english_words_lower if w not in query_words]
            if item_words:
                main_word = max(item_words, key=len)
                search_query = main_word
            else:
                main_word = " ".join(english_words_lower)
                search_query = main_word

    zone_query = False
    zone_name_lower = None
    if english_words_lower:
        if not hasattr(bot, "zone_names"):
            zones = set()
            for it in bot.database.items:
                if isinstance(it, dict):
                    fi = it.get('foundIn')
                    if isinstance(fi, str):
                        for part in fi.split(','):
                            part = part.strip()
                            if part:
                                zones.add(part)
            bot.zone_names = zones
        zone_names_lower = {z.lower() for z in bot.zone_names}
        for w in english_words_lower:
            lw = w.lower()
            if lw in zone_names_lower:
                zone_name_lower = lw
                break
        if zone_name_lower:
            other_words = [w.lower() for w in english_words_lower if w.lower() != zone_name_lower]
            filler_words = {'zone', 'area', 'type', 'region'}
            if not other_words or all(w in filler_words for w in other_words):
                zone_query = True

    if zone_query and not is_crafting_question and not is_obtain_question:
        matched_items = []
        for it in bot.database.items:
            if not isinstance(it, dict):
                continue
            fi = it.get('foundIn')
            if not isinstance(fi, str):
                continue
            parts = [p.strip().lower() for p in fi.split(',') if p.strip()]
            if zone_name_lower in parts:
                matched_items.append(it)
        if matched_items:
            matched_items_sorted = sorted(
                matched_items,
                key=lambda it: bot.search_engine.extract_name(it)
            )
            limited_items = matched_items_sorted[:10]
            zone_display = next(
                (z for z in getattr(bot, "zone_names", []) if z.lower() == zone_name_lower),
                zone_name_lower.capitalize()
            )
            embed = discord.Embed(
                title=f"🧭 منطقة اللوت: {zone_display}",
                description=f"أمثلة على القطع التي تلقاها في منطقة {zone_display}:",
                color=COLORS["info"],
                timestamp=datetime.now()
            )
            lines = []
            for it in limited_items:
                name = bot.search_engine.extract_name(it)
                rarity = EmbedBuilder.extract_field(it, 'rarity') or ''
                text = name
                if rarity:
                    text = f"{name} ({rarity})"
                lines.append(f"- {text}")
            extra_count = len(matched_items_sorted) - len(limited_items)
            if extra_count > 0:
                lines.append(f"+ {extra_count} قطع أخرى في هذه المنطقة")
            embed.add_field(
                name="اللوت في المنطقة",
                value="\n".join(lines),
                inline=False
            )
        else:
            zone_display = zone_name_lower.capitalize() if zone_name_lower else question
            embed = EmbedBuilder.warning(
                "منطقة غير معروفة",
                f"ما لقيت منطقة لوت باسم {zone_display} في الداتا."
            )
        reply = await reply_with_feedback(message, embed)
        bot.context_manager.set_context(message.author.id, zone_display, None)
        bot.questions_answered += 1
        return
    
    gun_parts_modifier = None
    if is_obtain_question and 'gun' in english_words_lower and 'parts' in english_words_lower:
        for w in english_words_lower:
            if w in ['light', 'heavy', 'complex']:
                gun_parts_modifier = w
                break
        if gun_parts_modifier:
            search_query = f"{gun_parts_modifier} gun parts"

    gun_parts_family_query = (
        is_obtain_question
        and 'gun' in english_words_lower
        and 'parts' in english_words_lower
        and gun_parts_modifier is None
    )
    if gun_parts_family_query:
        search_query = "gun parts"
    
    ai_configured = is_ai_configured()
    use_ai = should_use_ai(question) and ai_configured
    
    results = bot.search_engine.search(search_query, limit=5 if (is_crafting_question or is_obtain_question or is_location_question) else 1)
    
    if is_crafting_question and results and not gun_parts_family_query:
        recipe_candidates = []
        for r in results:
            item_candidate = r['item']
            recipe_candidate = item_candidate.get('recipe') if isinstance(item_candidate, dict) else None
            if isinstance(recipe_candidate, dict) and recipe_candidate:
                recipe_candidates.append(r)
        if recipe_candidates:
            best = max(recipe_candidates, key=lambda x: x['score'])
            results = [best]
        else:
            results = [results[0]]
    
    # تفضيل العنصر الأساسي على البلوبربنت في أسئلة الطرق/المكان
    if (is_obtain_question or is_location_question) and results:
        non_blueprints = [
            r for r in results
            if 'blueprint' not in bot.search_engine.extract_name(r['item']).lower()
            and 'Blueprint' not in r['item'].get('type', '')
        ]
        if non_blueprints:
            results = non_blueprints
    
    # عتبة المطابقة: أقل في أسئلة الدروب/المكان/التصنيع
    match_threshold = 0.6
    if is_crafting_question or is_obtain_question or is_location_question:
        match_threshold = 0.3
    
    if results and results[0]['score'] > match_threshold:
        result = results[0]
        item = result['item']
        
        item_name = bot.search_engine.extract_name(item).lower()
        
        skip_result = False
        if (not is_crafting_question and not is_obtain_question and not is_location_question) and english_words:
            main_word = max(english_words, key=len).lower()
            if len(main_word) > 3 and main_word not in item_name:
                skip_result = True
        
        if not skip_result:
            description = None
            if 'description' in item:
                desc_val = item['description']
                if isinstance(desc_val, dict):
                    description = desc_val.get('en') or desc_val.get('ar') or list(desc_val.values())[0]
                else:
                    description = str(desc_val)
            
            item_name_display = bot.search_engine.extract_name(item)
            item_type = EmbedBuilder.extract_field(item, 'type') or ''
            rarity = EmbedBuilder.extract_field(item, 'rarity') or ''
            found_in = item.get('foundIn') or ''
            location_field = item.get('location') or item.get('spawn_location') or item.get('map')
            if isinstance(location_field, dict):
                location_field = location_field.get('en') or location_field.get('ar') or list(location_field.values())[0]
            spawn_rate = item.get('spawnRate') or item.get('spawn_rate') or ''
            price = item.get('price') or item.get('value') or ''
            recipe = item.get('recipe') if isinstance(item.get('recipe'), dict) else None
            drops_list = item.get('drops') if isinstance(item.get('drops'), list) else []
            traders = item.get('traders') or item.get('soldBy') or []

            has_recipe_data = bool(recipe)
            has_location_data = bool(found_in or location_field or spawn_rate or drops_list or traders)

            if is_crafting_question and has_recipe_data:
                embed = EmbedBuilder.item_embed(item, None)
                reply = await reply_with_feedback(message, embed)
                name = bot.search_engine.extract_name(item)
                bot.context_manager.set_context(message.author.id, name, item)
                bot.questions_answered += 1
                return

            if (is_obtain_question or is_location_question) and has_location_data:
                obtain_sentences = []
                base_name = item_name_display or bot.search_engine.extract_name(item)
                
                if found_in and price:
                    obtain_sentences.append(f"{base_name} تلقاه غالباً في منطقة {found_in}، وسعره المقدر في الداتا حوالي {price}.")
                elif found_in:
                    obtain_sentences.append(f"{base_name} تلقاه غالباً في منطقة {found_in}.")
                elif price:
                    obtain_sentences.append(f"سعر {base_name} المقدر في الداتا حوالي {price}.")
                
                if location_field and location_field != found_in:
                    obtain_sentences.append(f"الموقع التفصيلي حسب الداتا: {location_field}.")
                if spawn_rate:
                    obtain_sentences.append(f"معدل الظهور في الداتا تقريباً: {spawn_rate}.")
                if traders:
                    if isinstance(traders, list):
                        trader_names = [str(t) for t in traders if t]
                        if trader_names:
                            obtain_sentences.append("يتوفر عند بعض التجار مثل: " + ", ".join(trader_names) + ".")
                    else:
                        obtain_sentences.append(f"يتوفر عند التاجر: {traders}.")
                if drops_list:
                    obtain_sentences.append(f"يسقط من أكثر من {len(drops_list)} عدو أو بوس مذكورين في الداتا.")

                custom_desc = "\n".join(obtain_sentences) if obtain_sentences else None
                embed = EmbedBuilder.item_embed(item, custom_desc)
                reply = await reply_with_feedback(message, embed)

                if is_obtain_question and gun_parts_family_query:
                    extra_results = []
                    for r in results[1:]:
                        extra_item = r['item']
                        extra_name = bot.search_engine.extract_name(extra_item).lower()
                        if 'gun parts' in extra_name:
                            extra_results.append(extra_item)
                    for extra_item in extra_results:
                        extra_description = None
                        if 'description' in extra_item:
                            desc_val = extra_item['description']
                            if isinstance(desc_val, dict):
                                extra_description = desc_val.get('en') or desc_val.get('ar') or list(desc_val.values())[0]
                            else:
                                extra_description = str(desc_val)
                        extra_translated_desc = None
                        if extra_description and extra_description != 'لا يوجد وصف':
                            extra_translated_desc = await bot.ai_manager.translate_to_arabic(extra_description)
                        extra_embed = EmbedBuilder.item_embed(extra_item, extra_translated_desc)
                        extra_obtain_lines = []
                        found_in_extra = extra_item.get('foundIn')
                        if found_in_extra:
                            extra_obtain_lines.append(f"- يوجد في: {found_in_extra}")
                        craft_bench_extra = extra_item.get('craftBench')
                        if craft_bench_extra:
                            extra_obtain_lines.append(f"- يتصنع في: {craft_bench_extra}")
                        if not is_crafting_question:
                            recipe_extra = extra_item.get('recipe')
                            if isinstance(recipe_extra, dict) and recipe_extra:
                                extra_obtain_lines.append("- له وصفة تصنيع، شوف تفاصيل التصنيع")
                        if extra_obtain_lines:
                            extra_embed.add_field(
                                name="طرق الحصول",
                                value="\n".join(extra_obtain_lines),
                                inline=False
                            )
                        await message.channel.send(embed=extra_embed)
            
                if is_location_question:
                    location = item.get('location') or item.get('spawn_location') or item.get('map')
                    if location:
                        if isinstance(location, dict):
                            location = location.get('en') or list(location.values())[0]
                        map_embed = EmbedBuilder.map_embed(str(location), item)
                        await message.channel.send(embed=map_embed)

                name = bot.search_engine.extract_name(item)
                bot.context_manager.set_context(message.author.id, name, item)
                bot.questions_answered += 1
                return

            context_parts = []
            if item_name_display:
                context_parts.append(f"الاسم: {item_name_display}")
            if description and not (is_obtain_question or is_location_question):
                context_parts.append(f"الوصف: {description}")
            if item_type:
                context_parts.append(f"النوع: {item_type}")
            if rarity:
                context_parts.append(f"الندرة: {rarity}")
            if found_in:
                context_parts.append(f"المنطقة العامة: {found_in}")
            if location_field and location_field != found_in:
                context_parts.append(f"الموقع التفصيلي: {location_field}")
            if spawn_rate:
                context_parts.append(f"نسبة الظهور (إن وجدت في الداتا): {spawn_rate}")
            if price:
                context_parts.append(f"السعر في الداتا: {price}")
            if recipe and not is_crafting_question:
                recipe_text = ", ".join(f"{k}: {v}" for k, v in recipe.items() if v is not None)
                if recipe_text:
                    context_parts.append(f"وصفة التصنيع: {recipe_text}")
            if drops_list:
                context_parts.append(f"يسقط من عدد أعداء/بوس مذكور في الداتا: {len(drops_list)}")
            if traders:
                context_parts.append("متوفر لدى بعض التجار في الداتا.")

            db_summary = " | ".join(context_parts) if context_parts else "لا توجد بيانات تفصيلية عن هذا الغرض في الداتا."
            
            ai_context = (
                "هذه بيانات من داتا ARC Raiders عن الغرض المذكور، استخدمها كمصدر أساسي، "
                "لكن مسموح لك تستفيد من معرفتك عن اللعبة وتضيف أماكن أو نصائح منطقية حتى لو ما كانت مكتوبة حرفياً في الداتا. "
                "لو حسيت المعلومة تقريبية أو مو مؤكدة، وضّح ذلك للاعب.\n"
                f"{db_summary}"
            )
            
            ai_question = (
                f"سؤال اللاعب: {question}\n\n"
                "اكتب إجابة واحدة قصيرة وواضحة بالعربي تشرح للاعب المطلوب حسب السؤال "
                "(مثلاً أين يجد القطعة أو كيف تُستخدم)، بدون قوائم طويلة."
            )
            
            ai_result = await bot.ai_manager.ask_ai(ai_question, context=ai_context)

            if ai_result['success']:
                embed = EmbedBuilder.success(
                    item_name_display or "إجابة",
                    ai_result['answer']
                )
            else:
                embed = EmbedBuilder.error(
                    "عذراً",
                    "ما قدرت ألقى جواب واضح حتى بعد استخدام الداتا والذكاء الاصطناعي."
                )

            reply = await reply_with_feedback(message, embed)

            name = bot.search_engine.extract_name(item)
            bot.context_manager.set_context(message.author.id, name, item)
            bot.questions_answered += 1
            return
    
    if (is_obtain_question or is_location_question or is_crafting_question) and (not results or results[0]['score'] <= match_threshold):
        if ai_configured:
            safe_context = (
                "سؤال عن مكان أو طريقة الحصول أو التصنيع في ARC Raiders "
                "لكن الداتا المحلية ما أعطت نتيجة واضحة. "
                "استخدم معرفتك العامة عن اللعبة وقدّم أفضل أماكن أو طرق أو نصائح تعرفها، "
                "ولو كانت المعلومة تقريبية أو مبنية على خبرة اللاعبين فاذكر أنها تقريبية."
            )
            await ask_ai_and_reply(
                message,
                f"{safe_context}\n\nسؤال اللاعب: {question}"
            )
            return
        embed = EmbedBuilder.warning(
            "ما لقيت في الداتا",
            "ما قدرت ألقى شيء واضح في داتا ARC Raiders يطابق سؤالك.\nجرّب تغير صياغة السؤال أو تكتب اسم الآيتم مباشرة."
        )
        await message.reply(embed=embed)
        return
    
    if results and results[0]['score'] > 0.3 and not (is_obtain_question or is_location_question or is_crafting_question):
        suggestions = bot.search_engine.find_similar(question, limit=3)
        if suggestions:
            suggestion_text = "\n".join([f"• {s}" for s in suggestions])
            embed = EmbedBuilder.warning(
                "هل تقصد..؟",
                f"ما لقيت **{content}** بالضبط\n\nهل تقصد:\n{suggestion_text}"
            )
            reply = await reply_with_feedback(message, embed)
            return
        if use_ai:
            await ask_ai_and_reply(message, question)
            return
        embed = EmbedBuilder.warning(
            "ما لقيت جواب واضح",
            "ما قدرت ألقى إجابة دقيقة من داتا ARC Raiders.\nجرّب تكتب اسم الآيتم مباشرة أو صياغة أبسط."
        )
        await message.reply(embed=embed)
        return
    
    if use_ai:
        await ask_ai_and_reply(message, question)
        return
    
    embed = EmbedBuilder.warning(
        "ما لقيت في الداتا",
        "ما قدرت ألقى شيء واضح في داتا ARC Raiders يطابق سؤالك.\nجرّب تغير صياغة السؤال أو تكتب اسم الآيتم مباشرة."
    )
    await message.reply(embed=embed)


async def ask_ai_and_reply(message: discord.Message, question: str):
    thinking_msg = await message.reply("🔍 أبحث لك...")
    
    context = ""
    user_context = bot.context_manager.get_context(message.author.id)
    if user_context:
        context = f"المستخدم كان يسأل عن: {user_context['item']}"
    
    q_lower = question.lower()
    
    expedition_keywords = [
        'expedition project',
        'expedition',
        'البروجيكت',
        'البروجكت',
        'بروجيكت الاكسبديشن',
        'بروجكت الاكسبديشن',
        'بروجيكت الإكسبيديشن',
        'بروجكت الإكسبيديشن'
    ]
    if any(k in q_lower for k in expedition_keywords):
        expedition_context = (
            "معلومة رسمية عن Expedition Project في ARC Raiders: "
            "ينفتح عند ليفل 20 كنظام يعيد تقدم الرايدر بشكل اختياري. "
            "كل دورة تستمر ثمانية أسابيع؛ سبعة أسابيع للتحضير والأسبوع الثامن لإنهاء البروجيكت. "
            "يعيد الليفل والمهارات والـ XP والإنفنتوري وتقدم التصنيع، "
            "ويحافظ على الكوزمِتكس والمشتريات وRaider Tokens وCred وتقدم Raider Decks والكودكس والخرائط "
            "وبونسات الإكسبيديشن من الرنات السابقة. "
            "إنهاء البروجيكت يعطي جوائز تجميلية دائمة وبفات حساب للمواسم التالية."
        )
        if context:
            context = context + " | " + expedition_context
        else:
            context = expedition_context
    
    game_info_keywords = [
        'arc raiders',
        'arc raider',
        'اركرين',
        'آرك ريدرز',
        'عن اللعبة',
        'وش هي arc raiders',
        'ما هي arc raiders'
    ]
    if any(k in q_lower for k in game_info_keywords):
        game_info_context = (
            "ARC Raiders هي لعبة مغامرات استخراج جماعية تدور على أرض مستقبلية مدمرة، "
            "تواجه فيها البشرية قوة ميكانيكية غامضة اسمها ARC. "
            "تلعب كرائدر يطلع لسطح الأرض لجمع الموارد وإنهاء المهمات والرجوع سالماً بالغنائم، "
            "مع إمكانية التعاون أو التنافس مع ريدرز آخرين."
        )
        if context:
            context = context + " | " + game_info_context
        else:
            context = game_info_context
    
    arc_force_keywords = [
        'arc نفسها',
        'قوة arc',
        'آرك نفسها',
        'الآرك',
        'arc machines'
    ]
    if any(k in q_lower for k in arc_force_keywords):
        arc_force_context = (
            "ARC هي قوة ميكانيكية غامضة دمّرت العالم، "
            "تتضمن آليّات صغيرة مثل Ticks وSnitches وصولاً إلى زعماء كبار من نوع Queens."
        )
        if context:
            context = context + " | " + arc_force_context
        else:
            context = arc_force_context
    
    speranza_keywords = [
        'speranza',
        'سبيرانزا',
        'سبرنزا',
        'المدينة تحت الأرض',
        'الملجأ'
    ]
    if any(k in q_lower for k in speranza_keywords):
        speranza_context = (
            "Speranza هي مستوطنة تحت الأرض تعتبر مركز آمن للبشر بعيداً عن تهديد ARC على السطح، "
            "وفيها ترجع بعد المهمات لتستلم المكافآت وتتعامل مع التجار وتطوّر شخصيتك ومساحتك الخاصة."
        )
        if context:
            context = context + " | " + speranza_context
        else:
            context = speranza_context
    
    workshop_keywords = [
        'workshop',
        'الوركشوب',
        'الورشة',
        'ورشة التصنيع',
        'تطوير الاسلحة',
        'ترقية الاسلحة'
    ]
    if any(k in q_lower for k in workshop_keywords):
        workshop_context = (
            "الـ Workshop هو المكان اللي تطور فيه العتاد والأسلحة، "
            "وتصلحها وتفتح وصفات تصنيع جديدة. "
            "تقدر بعد تطور الورشة نفسها عشان تفتح تجهيزات وأدوات أقوى."
        )
        if context:
            context = context + " | " + workshop_context
        else:
            context = workshop_context
    
    traders_keywords = [
        'traders',
        'trader',
        'التجار',
        'تاجر',
        'التاجر'
    ]
    if any(k in q_lower for k in traders_keywords):
        traders_context = (
            "التُجّار في Speranza شخصيات مهمة يقدمون مهمات تحكي قصص من الـ Rust Belt، "
            "ويعطونك مكافآت على مساعدتهم، بالإضافة لبيع وشراء الأغراض منك."
        )
        if context:
            context = context + " | " + traders_context
        else:
            context = traders_context
    
    scrappy_keywords = [
        'scrappy',
        'الديك',
        'ديكي',
        'rooster',
        'الديك المساعد'
    ]
    if any(k in q_lower for k in scrappy_keywords):
        scrappy_context = (
            "Scrappy هو رفيقك الديك اللي يساعدك يجمع الأغراض، "
            "وله سلوك أنه يلقط اللوت لك حتى لو خسرت، "
            "وتقدر تدربه وتعطيه كوزمِتكس خاصة فيه."
        )
        if context:
            context = context + " | " + scrappy_context
        else:
            context = scrappy_context
    
    rust_belt_keywords = [
        'rust belt',
        'دام باتلجراوندز',
        'dam battlegrounds',
        'buried city',
        'spaceport',
        'blue gate',
        'stella montis'
    ]
    if any(k in q_lower for k in rust_belt_keywords):
        rust_belt_context = (
            "مناطق الاستكشاف اسمها Rust Belt، "
            "وتشمل Dam Battlegrounds (غابات ومستَنقعات ومرافق أبحاث)، "
            "وBuried City (مدينة منهارة مغطاة بالرمل)، "
            "وSpaceport (منشأة إطلاق قديمة)، "
            "وBlue Gate (جبال وأنفاق ومدن ومجمعات تحت الأرض). "
            "وفيه إشاعة عن منطقة اسمها Stella Montis لكن الوصول لها غير معروف."
        )
        if context:
            context = context + " | " + rust_belt_context
        else:
            context = rust_belt_context
    
    specs_keywords = [
        'متطلبات التشغيل',
        'متطلبات اللعبة',
        'المواصفات المطلوبة',
        'specs',
        'requirements',
        'minimum specs',
        'recommended specs'
    ]
    if any(k in q_lower for k in specs_keywords):
        specs_context = (
            "متطلبات ARC Raiders على البي سي: "
            "الحد الأدنى تقريباً Windows 10 64-bit مع معالج i5-6600K أو Ryzen 5 1600، "
            "و12GB رام وكرت مثل GTX 1050 Ti أو RX 580، وDirectX 12. "
            "الموصى به i5-9600K أو Ryzen 5 3600، و16GB رام، "
            "وكرت مثل RTX 2070 أو RX 5700 XT."
        )
        if context:
            context = context + " | " + specs_context
        else:
            context = specs_context
    
    ping_keywords = [
        'ping system',
        'البنق',
        'البينق',
        'ping',
        'نظام البينق',
        'نظام العلامات',
        'كيف أعلِّم على الأعداء',
        'مارك'
    ]
    if any(k in q_lower for k in ping_keywords):
        ping_context = (
            "نظام الـ Ping يسمح لك تعلم على اللاعبين أو ARC أو الأغراض أو المواقع، "
            "باستخدام زر الماوس الأوسط على البي سي، أو R1/RT على البلايستيشن والإكس بوكس، "
            "وتقدر تعدّل الأزرار من الإعدادات."
        )
        if context:
            context = context + " | " + ping_context
        else:
            context = ping_context
    
    ai_result = await bot.ai_manager.ask_ai(question, context)
    
    await thinking_msg.delete()
    
    if ai_result['success']:
        embed = EmbedBuilder.success(
            "إجابة",
            ai_result['answer']
        )
        embed.set_footer(text=f"🤖 {BOT_NAME}")
    else:
        embed = EmbedBuilder.error(
            "عذراً",
            "ما قدرت ألقى جواب.\n\n💡 جرب صياغة السؤال بطريقة مختلفة!"
        )
    
    reply = await reply_with_feedback(message, embed)

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    """معالجة الـ Reactions - تسجيل التقييمات"""
    
    if user.bot:
        return
    
    if reaction.message.author != bot.user:
        return
    
    emoji = str(reaction.emoji)
    
    # تسجيل في اللوق
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    
    if emoji == '❌' and log_channel:
        # إجابة خاطئة - نسجل في اللوق
        embed = discord.Embed(
            title="❌ تقييم: إجابة خاطئة",
            color=COLORS["error"],
            timestamp=datetime.now()
        )
        
        # محتوى الرسالة الأصلية
        original_content = ""
        if reaction.message.embeds:
            original_embed = reaction.message.embeds[0]
            original_content = f"**{original_embed.title}**\n{original_embed.description[:200] if original_embed.description else ''}"
        
        embed.add_field(name="👤 من", value=user.mention, inline=True)
        embed.add_field(name="📝 الرد", value=original_content[:500] or "Embed", inline=False)
        
        # السؤال الأصلي (الرسالة اللي رد عليها البوت)
        if reaction.message.reference:
            try:
                original_msg = await reaction.message.channel.fetch_message(reaction.message.reference.message_id)
                embed.add_field(name="❓ السؤال", value=original_msg.content[:200], inline=False)
            except:
                pass
        
        await log_channel.send(embed=embed)
    
    elif emoji == '✅':
        # إجابة صحيحة - ممكن نسجلها للإحصائيات
        pass

# ═══════════════════════════════════════════════════════════════
# التشغيل
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN غير موجود!")
        exit(1)
    
    logger.info("🚀 جاري تشغيل البوت...")
    bot.run(DISCORD_TOKEN)
