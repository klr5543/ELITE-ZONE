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
BOT_VERSION = "2.0.0"

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
    'ادوات': 'materials',
    'أدوات': 'materials',
    'متطلبات': 'requirements',
    'مواد': 'materials',
    'عطني': '',
    'اعطني': '',
    'ابي': '',
    'ابغى': '',
    
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


def should_use_ai(text: str) -> bool:
    if is_comparative_question(text):
        return True
    if is_strategy_question(text):
        return True
    if is_explanatory_question(text):
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
            searchable_fields = ['name', 'title', 'displayName', 'description', 
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
1. رد بالعربي دائماً
2. كن مختصراً ومفيداً
3. لو ما تعرف الجواب، قل ذلك بصراحة
4. ركز على معلومات اللعبة فقط

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
            'كم', 'how much', 'الندرة', 'rarity', 'كيف', 'how',
            'طيب', 'وش', 'ايش', 'ليش', 'متى', 'هل', 'فين'
        ]
        
        question_lower = question.lower()
        is_follow_up = any(keyword in question_lower for keyword in follow_up_keywords)
        
        # إذا السؤال قصير أو يحتوي كلمات متابعة
        if is_follow_up or len(question.split()) <= 3:
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
        
        # لو dict (ترجمات متعددة)
        if isinstance(value, dict):
            return value.get('en') or value.get('ar') or str(list(value.values())[0]) if value else None
        
        # لو string أو رقم
        return str(value) if value else None
    
    @staticmethod
    def get_image_url(item: dict) -> str:
        """الحصول على رابط صورة العنصر"""
        # أولاً: لو في رابط صورة مباشر
        img_url = item.get('image') or item.get('icon') or item.get('imageUrl')
        if img_url and isinstance(img_url, str) and img_url.startswith('http'):
            return img_url
        
        # ثانياً: بناء الرابط من الـ id
        item_id = item.get('id') or item.get('itemId') or item.get('slug')
        if item_id:
            # تحديد نوع المجلد
            item_type = item.get('type') or item.get('category') or ''
            if isinstance(item_type, dict):
                item_type = item_type.get('en', '')
            
            item_type_lower = str(item_type).lower()
            
            # تحديد المجلد المناسب
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
        """إنشاء Embed لعنصر من اللعبة - الاسم إنجليزي والباقي عربي"""
        # استخراج الاسم - الإنجليزي
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
        
        # استخدم الوصف المترجم لو موجود
        if translated_desc:
            description = translated_desc
        else:
            # استخراج الوصف الأصلي
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
        
        # إضافة الحقول - العناوين عربي
        category = EmbedBuilder.extract_field(item, 'category')
        if category:
            embed.add_field(name="📁 الفئة", value=category, inline=True)
        
        item_type = EmbedBuilder.extract_field(item, 'type')
        if item_type:
            embed.add_field(name="🏷️ النوع", value=item_type, inline=True)
        
        rarity = EmbedBuilder.extract_field(item, 'rarity')
        if rarity:
            # ترجمة الندرة للعربي
            rarity_ar = {
                'common': 'عادي ⚪',
                'uncommon': 'غير شائع 🟢', 
                'rare': 'نادر 🔵',
                'epic': 'ملحمي 🟣',
                'legendary': 'أسطوري 🟡'
            }.get(rarity.lower(), rarity)
            embed.add_field(name="💎 الندرة", value=rarity_ar, inline=True)
        
        # الموقع مع رابط الخريطة
        location = EmbedBuilder.extract_field(item, 'location')
        if location:
            embed.add_field(name="📍 الموقع", value=location, inline=True)
        
        spawn_rate = item.get('spawnRate') or item.get('spawn_rate')
        if spawn_rate:
            embed.add_field(name="📊 نسبة الظهور", value=f"{spawn_rate}%", inline=True)
        
        price = item.get('price') or item.get('value')
        if price:
            embed.add_field(name="💰 السعر", value=str(price), inline=True)
        
        # صورة العنصر المصغرة (Thumbnail)
        img_url = EmbedBuilder.get_image_url(item)
        if img_url:
            embed.set_thumbnail(url=img_url)
        
        embed.set_footer(text=f"🤖 {BOT_NAME} | ARC Raiders")
        return embed
    
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
    
    # تجاهل البوتات
    if message.author.bot:
        return
    
    # تجاهل الرسائل خارج السيرفر والقناة المحددة
    if message.guild and message.guild.id != ALLOWED_GUILD_ID:
        return
    
    if message.channel.id != ALLOWED_CHANNEL_ID:
        await bot.process_commands(message)
        return
    
    # تنظيف الرسالة
    content = message.content.strip()
    content_lower = content.lower()
    
    # كلمات نتجاهلها (اسم البوت، تحيات قصيرة، إلخ)
    ignore_words = [
        'دليل', 'daleel', 'bot', 'بوت',
        'هاي', 'hi', 'hello', 'مرحبا', 'السلام',
        'هلا', 'اهلا', 'hey', 'yo'
    ]
    
    # تجاهل الرسائل القصيرة جداً أو اللي هي بس اسم البوت
    if len(content) < 5 or content_lower in ignore_words:
        return
    
    # إزالة اسم البوت من بداية الرسالة لو موجود
    for word in ['دليل', 'daleel']:
        if content_lower.startswith(word):
            content = content[len(word):].strip()
            break
    
    # لو بعد الإزالة صارت فاضية أو قصيرة جداً
    if len(content) < 3:
        return
    
    # ردود سريعة
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
    
    # فحص السبام
    allowed, wait_time = bot.anti_spam.check(message.author.id)
    if not allowed:
        embed = EmbedBuilder.warning(
            "انتظر قليلاً",
            f"⏰ انتظر **{wait_time}** ثانية"
        )
        await message.reply(embed=embed, delete_after=10)
        return
    
    # حقن السياق
    question = bot.context_manager.inject_context(message.author.id, content)
    
    # البحث في قاعدة البيانات
    ai_configured = is_ai_configured()
    use_ai = should_use_ai(question) and ai_configured
    results = bot.search_engine.search(question, limit=1)
    
    if results and results[0]['score'] > 0.6:
        # وجدنا نتيجة جيدة!
        result = results[0]
        item = result['item']
        
        # تحقق إضافي: لو السؤال فيه اسم محدد، نتأكد النتيجة تطابقه
        item_name = bot.search_engine.extract_name(item).lower()
        
        # استخراج الكلمات الإنجليزية من السؤال (أسماء العناصر)
        english_words = re.findall(r'[a-zA-Z]+', content)
        
        # لو في اسم إنجليزي بالسؤال، نتأكد موجود بالنتيجة
        skip_result = False
        if english_words:
            main_word = max(english_words, key=len).lower()  # أطول كلمة إنجليزية
            if len(main_word) > 3 and main_word not in item_name:
                # الاسم المطلوب مو موجود بالنتيجة - نعتبرها غلط
                skip_result = True
        
        if not skip_result:
            # استخراج الوصف وترجمته
            description = None
            if 'description' in item:
                desc_val = item['description']
                if isinstance(desc_val, dict):
                    description = desc_val.get('en') or desc_val.get('ar') or list(desc_val.values())[0]
                else:
                    description = str(desc_val)
            
            # ترجمة الوصف للعربي
            translated_desc = None
            if description and description != 'لا يوجد وصف':
                translated_desc = await bot.ai_manager.translate_to_arabic(description)
            
            embed = EmbedBuilder.item_embed(item, translated_desc)
            
            # كشف لو السؤال عن موقع
            location_keywords = ['وين', 'اين', 'أين', 'مكان', 'موقع', 'القى', 'الاقي', 'احصل', 'where', 'location', 'find']
            is_location_question = any(keyword in content_lower for keyword in location_keywords)
            
            # إرسال الرد الأول (معلومات العنصر)
            reply = await message.reply(embed=embed)
            
            # لو سؤال عن موقع، نرسل صورة الخريطة
            if is_location_question:
                location = item.get('location') or item.get('spawn_location') or item.get('map')
                if location:
                    if isinstance(location, dict):
                        location = location.get('en') or list(location.values())[0]
                    
                    # إرسال صورة الخريطة
                    map_embed = EmbedBuilder.map_embed(str(location), item)
                    await message.channel.send(embed=map_embed)
            
            # حفظ السياق
            name = bot.search_engine.extract_name(item)
            bot.context_manager.set_context(message.author.id, name, item)
            
            # إضافة reactions بسيطة
            await reply.add_reaction('✅')  # إجابة صحيحة
            await reply.add_reaction('❌')  # إجابة خاطئة
            
            bot.questions_answered += 1
            return
    
    if results and results[0]['score'] > 0.3:
        suggestions = bot.search_engine.find_similar(question, limit=3)
        if suggestions:
            suggestion_text = "\n".join([f"• {s}" for s in suggestions])
            embed = EmbedBuilder.warning(
                "هل تقصد..؟",
                f"ما لقيت **{content}** بالضبط\n\nهل تقصد:\n{suggestion_text}"
            )
            reply = await message.reply(embed=embed)
            await reply.add_reaction('✅')
            await reply.add_reaction('❌')
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
    """سؤال الـ AI والرد"""
    thinking_msg = await message.reply("🔍 أبحث لك...")
    
    context = ""
    user_context = bot.context_manager.get_context(message.author.id)
    if user_context:
        context = f"المستخدم كان يسأل عن: {user_context['item']}"
    
    ai_result = await bot.ai_manager.ask_ai(question, context)
    
    await thinking_msg.delete()
    
    if ai_result['success']:
        embed = EmbedBuilder.success(
            "جواب من AI",
            ai_result['answer']
        )
        embed.set_footer(text=f"via {ai_result['provider']} • 🤖 {BOT_NAME}")
    else:
        embed = EmbedBuilder.error(
            "عذراً",
            "ما قدرت ألقى جواب.\n\n💡 جرب صياغة السؤال بطريقة مختلفة!"
        )
    
    reply = await message.reply(embed=embed)
    await reply.add_reaction('✅')
    await reply.add_reaction('❌')

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
