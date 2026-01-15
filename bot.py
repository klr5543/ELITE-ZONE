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


# دالة تحليل السؤال وفهم السياق المركب (NLP أعمق)
def extract_intents(text: str) -> list:
    """
    تستخرج قائمة intents من السؤال بناءً على كلمات مفتاحية وسياق لغوي مركب
    """
    intents = []
    lowered = text.lower()
    # intent: مقارنة
    if any(token in lowered for token in ["أفضل", "أقوى", "أحسن", "أسرع", "أرخص", "أكثر", "vs", "مقارنة", "يستحق", "ولا", "or", "better", "best"]):
        intents.append("comparative")
    # intent: استراتيجية
    if any(token in lowered for token in ["استراتيجية", "strategy", "كيف العب", "كيف ألعب", "build", "بيلد", "طريقة اللعب", "نصائح", "أواجه", "أتعامل", "أفوز", "أهرب", "أقتل"]):
        intents.append("strategy")
    # intent: شرح/تعريف
    if any(token in lowered for token in ["ليش", "لماذا", "why", "سبب", "اشرح", "شرح", "explain", "يعني", "معنى", "تعريف", "وش", "ايش"]):
        intents.append("explanation")
    # intent: بدائل/حلول
    if any(token in lowered for token in ["بديل", "بدائل", "حل", "إذا ما لقيت", "ما حصلت", "ما عندي", "alternative"]):
        intents.append("alternatives")
    # intent: مستوى اللاعب
    if any(token in lowered for token in ["مبتدئ", "محترف", "نصائح للمبتدئين", "نصائح للمحترفين", "مستوى"]):
        intents.append("player_level")
    # intent: ميتا/تحديثات
    if any(token in lowered for token in ["ميتا", "meta", "تحديث", "باتش", "patch", "تغييرات", "أقوى حالياً"]):
        intents.append("meta")
    # intent: تجارب مجتمع
    if any(token in lowered for token in ["مجتمع", "لاعبين", "تجارب", "وش رأيكم", "أفضل طريقة جربتوها"]):
        intents.append("community")
    # intent: عام
    if not intents:
        intents.append("general")
    return intents


# حذف الدوال القديمة:
# def is_comparative_question(text: str) -> bool:
# def is_strategy_question(text: str) -> bool:
# def is_explanatory_question(text: str) -> bool:
# def extract_intent(text: str) -> str:
# واستبدال كل استخدامات extract_intent(text) بـ extract_intents(text)[0] أو extract_intents(text) حسب الحاجة
# واستبدال كل if is_comparative_question(text): ... إلخ بمنطق يعتمد على extract_intents

# مثال استبدال:
# intent = extract_intent(text)
# يصبح:
## مثال فقط، لا تستخدم خارج دوال أو أحداث البوت
# ...existing code...

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
        
        return "لا يوجد اسم واضح لهذا الغرض في قاعدة البيانات. إذا عندك معلومة أو اسم أدق شاركها مع المجتمع ليستفيد الجميع."
    
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
2. كن مختصراً ومباشراً قدر الإمكان.
3. لو ما تعرف الجواب بدقة أو ما عندك مصدر موثوق، قل بصراحة إن المعلومات غير مؤكدة ولا تؤلف أرقاماً أو أماكن أو أسماء.
4. ركز على لعبة ARC Raiders فقط، ولا تتكلم عن ألعاب ثانية.
5. لا تكرر نصوصاً طويلة أو قوائم مملة؛ استخدم جمل قليلة مفيدة.
{f'السياق: {context}' if context else ''}"""
        
        # ترتيب المزودين
        providers = [
            ('deepseek', self._ask_deepseek),
            ('groq', self._ask_groq),
            ('openai', self._ask_openai),
            ('anthropic', self._ask_anthropic),
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
            title=title,
            description=description,
            color=COLORS["success"],
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"🤖 {BOT_NAME}")
        return embed
    @staticmethod
    def error(title: str, description: str) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=COLORS["error"],
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"🤖 {BOT_NAME}")
        return embed
    
    @staticmethod
    def warning(title: str, description: str) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=COLORS["info"],
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"🤖 {BOT_NAME}")
        return embed

# دالة مستقلة لتوليد النص الذكي بناءً على البيانات والسياق
def generate_item_response(item, name=None, drops=None, location=None, recipe=None, intent=None):
    # منطق الردود الذكية هنا
    if drops and name:
        return f"🔍 تحصل على {name} من: {', '.join(drops[:6])} وغيرها."
    elif location:
        if name:
            return f"📍 موقع {name}: {location}."
        else:
            return f"📍 موقع غير محدد: {location}."
    elif found_in := (item.get('foundIn') or item.get('location')):
        if name:
            return f"📦 {name} غالبًا تلقاه في: {found_in}."
        else:
            return f"📦 غرض بدون اسم غالبًا تلقاه في: {found_in}."
    elif isinstance(recipe, dict) and recipe:
        parts = [f"{v}× {k}" for k, v in recipe.items()]
        body = '، '.join(parts)
        return f"🛠️ لتصنيع {name} تحتاج: {body}."
    elif intent == 'requirements':
        return "🛠️ متطلبات هذا الغرض غير واضحة. جرب تسأل مجتمع اللاعبين أو تراجع قائمة التصنيع في الورشة."
    elif intent == 'definition':
        return "ℹ️ لا يوجد وصف دقيق لهذا الغرض. اسأل مجتمع اللاعبين عن فائدة أو استخداماته."
    elif intent == 'location':
        return "📍 مكان هذا الغرض غير محدد. جرب تسأل مجتمع اللاعبين أو تدور عليه في أماكن اللوت الشائعة."
    elif intent == 'loot':
        return "🔎 لا توجد معلومات كافية عن طريقة الحصول. جرب تدور عليه في مناطق اللوت الصناعية أو اسأل مجتمع اللاعبين عن تجاربهم."
    elif recipe:
        bp = item.get('blueprint') or item.get('craftBench')
        if bp:
            return f"🛠️ {name} يتصنع في: {bp}."
        else:
            return "🛠️ لا توجد معلومات تصنيع مفصّلة لهذا الغرض. جرب تسأل مجتمع اللاعبين عن وصفة التصنيع أو مكان الورشة المناسب."
    else:
        rarity = item.get('rarity')
        itype = item.get('type')
        parts = []
        if itype:
            parts.append(str(itype))
        if rarity:
            parts.append(str(rarity))
        if parts:
            return f"{name} — {' | '.join(parts)}"
        return "🔎 إذا ما لقيت مكان واضح، جرب تسأل مجتمع اللاعبين أو تدور عليه في أماكن اللوت الشائعة."
# إذا أردت رسالة إضافية للمجتمع:
# return "🔎 لا توجد معلومات كافية عن هذا الغرض. إذا عندك تجربة أو معلومة شاركها ليستفيد المجتمع."
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
        text = text.replace('запасные', 'احتياطية')
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
        # استخدم اسم العنصر من id إذا لم يوجد أي اسم نصي
        if not name:
            if 'id' in item and isinstance(item['id'], str):
                name = item['id'].replace('_', ' ').title()
            else:
                name = None

        # إذا لم يوجد اسم، استخدم وصف منطقي في العنوان
        if not name:
            name = None

        # منطق الرد الذكي حسب نوع السؤال
        if intent == 'loot':
            drops = item.get('drops') or []
            found_in = item.get('foundIn') or item.get('location')
            type_str = (item.get('type') or '').lower()
            rarity_str = (item.get('rarity') or '').lower()
            # منطق مستوحى من مصادر الإنترنت
            if drops:
                text = f"يمكنك الحصول على {name} من: {', '.join(drops[:6])} وغيرها."
            elif found_in:
                text = f"غالبًا تجد {name} في منطقة: {found_in}."
            elif any(word in type_str for word in ['mechanical', 'electrical', 'industrial', 'component', 'parts']) or rarity_str in ['common', 'uncommon', 'rare']:
                text = f"🔧 نصيحة خبير: القطع الميكانيكية والكهربائية غالبًا تلقاها في المناطق الصناعية مثل Dam Battlegrounds وSpaceport أو صناديق الميكانيك. جرب تركز على قتل الأعداء الميكانيكيين أو فتح صناديق الورش."
            elif 'quest' in type_str:
                text = f"📝 نصيحة خبير: {name} غالبًا مرتبط بمهمة أو حدث خاص. جرب تراجع قائمة المهام أو تحدث مع لاعبين أنهوا المهمة. أحيانًا تحتاج شرط معين أو تقدم في القصة."
            elif 'consumable' in type_str or 'food' in type_str:
                text = f"🍎 نصيحة خبير: {name} غالبًا تحصل عليه من الصناديق العامة أو عند استكشاف المناطق السكنية أو عند التجار. جرب تفتش في المناطق الآمنة أو تسأل لاعبين عن أماكن اللوت السريع."
            elif name and not name.startswith('غرض بدون اسم'):
                text = f"🔎 نصيحة خبير: إذا ما لقيت {name} في مكان محدد، جرب تبحث في مناطق اللوت المتقدمة أو صناديق خاصة أو بعد أحداث معينة. أحيانًا يحتاج شرط أو مهمة أو قتل بوس معين. إذا عندك تجربة أو معلومة شاركها ليستفيد المجتمع."
            else:
                text = "🔎 نصيحة خبير: هذا النوع غالبًا يكون نادر أو مرتبط بمهمة أو حدث خاص أو يحتاج شرط معين. جرب تبحث في مناطق اللوت المتقدمة أو اسأل مجتمع اللاعبين عن تجاربهم. إذا عندك معلومة أو تجربة شاركها ليستفيد الجميع."
        elif intent == 'location':
            location = item.get('location') or item.get('foundIn')
            if location:
                text = f"غالبًا يوجد {name} في: {location}."
            elif name and not name.startswith('غرض بدون اسم'):
                text = f"🔎 خبرة المطوّر: الغرض اللي ماله مكان محدد غالبًا يكون له احتمالية ظهور في مناطق اللوت الشائعة أو صناديق خاصة أو بعد أحداث معينة. جرب تدور عليه في Buried City أو Blue Gate أو اسأل مجتمع اللاعبين عن تجاربهم. إذا عندك تجربة أو معلومة شاركها ليستفيد الجميع."
            else:
                text = "🔎 خبرة المطوّر: هذا النوع غالبًا يكون نادر أو مرتبط بمهمة أو حدث خاص. جرب تبحث في مناطق اللوت المتقدمة أو اسأل مجتمع اللاعبين عن تجاربهم. إذا عندك معلومة أو تجربة شاركها ليستفيد الجميع."
        
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

    @staticmethod
    def concise_item_response(item: dict, intent: str = None) -> discord.Embed:
        """إنشاء رد مختصر وطبيعي يعتمد على نية السؤال (مثلاً: 'requirements', 'location', 'definition', 'loot')."""
        name = None
        for field in ['name', 'title', 'displayName', 'nameKey']:
            if field in item and isinstance(item[field], str):
                name = item[field]
                break
        if not name or name.strip() == '' or name == 'غير معروف':
            name = 'غرض بدون اسم (لم يتم تعريفه في الداتا)'

        # Default short description
        desc = item.get('description') or item.get('shortDescription') or ''
        if isinstance(desc, dict):
            desc = desc.get('en') or next(iter(desc.values()), '')

        # Crafting / requirements intent
        if intent == 'requirements' or 'recipe' in item or 'blueprint' in (item.get('type') or '').lower():
            recipe = item.get('recipe') or item.get('components') or {}
            if isinstance(recipe, dict) and recipe:
                parts = []
                for k, v in recipe.items():
                    parts.append(f"{v}× {k}")
                body = '، '.join(parts)
                text = f"لتصنيع {name} تحتاج: {body}."
            else:
                # check blueprint link
                bp = item.get('blueprint') or item.get('craftBench')
                if bp:
                    text = f"{name} يَصنع على: {bp}."
                else:
                    text = f"لا توجد معلومات تصنيع مفصّلة لـ {name} في الداتا."

        # Loot / obtain intent
        elif intent == 'loot' or item.get('drops'):
            drops = item.get('drops') or []
            if drops:
                text = f"يمكن الحصول على {name} من: {', '.join(drops[:6])}"
            else:
                found_in = item.get('foundIn') or item.get('location')
                if found_in:
                    text = f"عادةً يُوجد {name} في: {found_in}."
                else:
                    text = f"لا يوجد مكان محدد لهذا الغرض في قاعدة البيانات. إذا عندك تجربة أو معلومة شاركها مع المجتمع ليستفيد الجميع. جرب أيضًا سؤال اللاعبين أو البحث في الويكي الرسمي."

        # Location / zone intent
        elif intent == 'location' or item.get('location'):
            location = item.get('location') or item.get('foundIn')
            if location:
                text = f"{name} يُوجد عادة في: {location}."
            else:
                text = f"لا يوجد مكان محدد لهذا الغرض في قاعدة البيانات. إذا عندك تجربة أو معلومة شاركها مع المجتمع ليستفيد الجميع. جرب أيضًا سؤال اللاعبين أو البحث في الويكي الرسمي."

        # Definition or fallback
        else:
            short = desc.strip()[:300]
            if short:
                text = short
            else:
                # fallback ذكي مستوحى من مصادر الإنترنت وخبرة اللاعبين
                if intent == 'requirements':
                    text = f"متطلبات {name} غير واضحة في قاعدة البيانات. عادةً، المتطلبات تظهر عند محاولة التصنيع أو الترقية. اسأل المجتمع أو راجع الويكي الرسمي لمزيد من التفاصيل."
                elif intent == 'definition':
                    text = f"{name}: لا يوجد وصف دقيق في قاعدة البيانات. جرب البحث في arcraiders.com/wiki أو اسأل مجتمع اللاعبين عن فائدة هذا الغرض."
                elif intent == 'location':
                    text = f"مكان {name} غير محدد في قاعدة البيانات. جرب سؤال اللاعبين أو البحث في مصادر الإنترنت مثل IGN أو الويكي الرسمي."
                elif intent == 'loot':
                    text = f"لا توجد معلومات كافية عن {name} في قاعدة البيانات. إذا عندك تفاصيل أو تجربة، شاركها مع المجتمع ليستفيد الجميع. جرب أيضًا البحث في arcraiders.com/wiki أو سؤال اللاعبين في الديسكورد."
                else:
                    rarity = item.get('rarity')
                    itype = item.get('type')
                    parts = []
                    if itype:
                        parts.append(str(itype))
                    if rarity:
                        parts.append(str(rarity))
                    if parts:
                        text = f"{name} — {' | '.join(parts)}"
                    else:
                        text = f"لا توجد معلومات كافية عن {name} في قاعدة البيانات. إذا عندك تفاصيل أو تجربة، شاركها مع المجتمع ليستفيد الجميع. جرب أيضًا البحث في arcraiders.com/wiki أو سؤال اللاعبين في الديسكورد."

        # Emoji by type
        emoji = "📦"
        if 'weapon' in (item.get('type') or '').lower():
            emoji = "🔫"
        elif 'armor' in (item.get('type') or '').lower():
            emoji = "🛡️"
        elif 'key' in (item.get('type') or '').lower():
            emoji = "🗝️"
        elif 'component' in (item.get('type') or '').lower():
            emoji = "⚙️"
        elif 'consumable' in (item.get('type') or '').lower():
            emoji = "💊"
        elif 'quest' in (item.get('type') or '').lower():
            emoji = "📜"
        # إذا لم يوجد اسم، لا تضعه في العنوان
        # تصفية أي تكرار أو بلبلة في العنوان
        if name and name.strip() != '' and not name.startswith('غرض بدون اسم'):
            title = f"{emoji} {name}"
        else:
            title = f"{emoji} غرض غير معرف"
        embed = discord.Embed(
            title=title,
            description=text.strip(),
            color=COLORS['primary'],
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"🤖 {BOT_NAME}")
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
            return "لا يوجد اسم واضح لهذا الغرض في قاعدة البيانات. إذا عندك معلومة أو اسم أدق شاركها مع المجتمع ليستفيد الجميع."
        
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
                # concise response for obtain/location questions
                intent = 'loot' if is_obtain_question else 'location' if is_location_question else None
                embed = EmbedBuilder.concise_item_response(item, intent=intent)
            else:
                # concise definition / fallback
                embed = EmbedBuilder.concise_item_response(item, intent=None)
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
    
    if is_queen_query:
        embed = EmbedBuilder.warning(
            "تلميح للملكة",
            "يبدو أنك تسأل عن الـ Queen. تأكد أنك مستعد جيداً قبل المواجهة!\n\n🔗 [معلومات أكثر عن الـ Queen](https://arcraiders.com/wiki/Queen)"
        )
        await message.reply(embed=embed)
        return
    
    if (is_obtain_question or is_location_question or is_crafting_question) and (not results or results[0]['score'] <= match_threshold):
        if ai_configured:
            safe_context = (
                "سؤال عن مكان أو طريقة الحصول أو التصنيع في ARC Raiders "
                "لكن الداتا الرسمية ما أعطت نتيجة واضحة. "
                "لا تعطي مواقع أو نسب سبون أو أسماء أعداء من عندك. "
                "لو ما عندك مصدر مؤكد، قل بصراحة إن المعلومات غير متوفرة، "
                "واكتفِ بنصائح عامة جداً أو اقتراح أن اللاعب يجرب يسأل المجتمع."
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
