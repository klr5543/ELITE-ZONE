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
            if drops and name:
                text = f"🔍 تحصل على {name} من: {', '.join(drops[:6])} وغيرها."
            elif found_in := (item.get('foundIn') or item.get('location')):
                if name:
                    text = f"📦 {name} غالبًا تلقاه في: {found_in}."
                else:
                    text = f"📦 غرض بدون اسم غالبًا تلقاه في: {found_in}."
            else:
                text = "🔎 إذا ما لقيت مكان واضح، جرب تدور عليه في مناطق اللوت الصناعية أو اسأل مجتمع اللاعبين."
    @staticmethod
    def error(title: str, description: str) -> discord.Embed:
        embed = discord.Embed(
            if location:
                if name:
                    text = f"📍 موقع {name}: {location}."
                else:
                    text = f"📍 موقع غير محدد: {location}."
            else:
                text = "🔎 إذا ما لقيت مكان واضح، جرب تسأل مجتمع اللاعبين أو تدور عليه في أماكن اللوت الشائعة."
    
    @staticmethod
    def warning(title: str, description: str) -> discord.Embed:
            if isinstance(recipe, dict) and recipe:
                parts = []
                for k, v in recipe.items():
                    parts.append(f"{v}× {k}")
                body = '، '.join(parts)
                text = f"🛠️ لتصنيع {name} تحتاج: {body}."
            else:
                bp = item.get('blueprint') or item.get('craftBench')
                if bp:
                    text = f"🛠️ {name} يتصنع في: {bp}."
                else:
                    text = f"🛠️ لا توجد معلومات تصنيع مفصّلة لهذا الغرض. جرب تسأل مجتمع اللاعبين عن وصفة التصنيع أو مكان الورشة المناسب."
            description=description,
            color=COLORS["info"],
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"🤖 {BOT_NAME}")
        return embed
                if intent == 'requirements':
                    text = f"🛠️ متطلبات هذا الغرض غير واضحة. جرب تسأل مجتمع اللاعبين أو تراجع قائمة التصنيع في الورشة."
                elif intent == 'definition':
                    text = f"ℹ️ لا يوجد وصف دقيق لهذا الغرض. اسأل مجتمع اللاعبين عن فائدة أو استخداماته."
                elif intent == 'location':
                    text = f"📍 مكان هذا الغرض غير محدد. جرب تسأل مجتمع اللاعبين أو تدور عليه في أماكن اللوت الشائعة."
                elif intent == 'loot':
                    text = f"🔎 لا توجد معلومات كافية عن طريقة الحصول. جرب تدور عليه في مناطق اللوت الصناعية أو اسأل مجتمع اللاعبين عن تجاربهم."
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
                        text = f"🔎 لا توجد معلومات كافية عن هذا الغرض. إذا عندك تجربة أو معلومة شاركها ليستفيد المجتمع."
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
    english_words_raw_lower = [w.lower() for w in english_words]
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
                "منطقة غير معروفة (لم يتم تعريفها في الداتا)",
                f"ما لقيت منطقة لوت باسم {zone_display} في الداتا."
            )
        reply = await reply_with_feedback(message, embed)
        bot.context_manager.set_context(message.author.id, zone_display, None)
        bot.questions_answered += 1
        return
    
    gun_parts_family_query = (
        is_obtain_question
        and 'gun' in english_words_lower
        and 'parts' in english_words_lower
        and not any(w in ['light', 'heavy', 'complex'] for w in english_words_raw_lower)
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
            
            translated_desc = None
            if description and description != 'لا يوجد وصف':
                translated_desc = await bot.ai_manager.translate_to_arabic(description)

            if is_obtain_question or is_location_question:
                obtain_info = []
                found_in = item.get('foundIn')
                if found_in:
                    obtain_info.append(f"📍 **المنطقة:** {found_in}")
                location_field = item.get('location') or item.get('spawn_location') or item.get('map')
                if location_field and location_field != found_in:
                    if isinstance(location_field, dict):
                        location_field = location_field.get('en') or location_field.get('ar') or list(location_field.values())[0]
                    obtain_info.append(f"🗺️ **الموقع:** {location_field}")
                spawn_rate = item.get('spawnRate') or item.get('spawn_rate')
                if spawn_rate:
                    obtain_info.append(f"📊 **نسبة الظهور:** {spawn_rate}%")
                craft_bench = item.get('craftBench')
                recipe = item.get('recipe')
                if craft_bench or (isinstance(recipe, dict) and recipe):
                    if craft_bench:
                        obtain_info.append(f"🔨 **التصنيع:** متاح في {craft_bench}")
                    else:
                        obtain_info.append("🔨 **التصنيع:** متاح (شوف تفاصيل الوصفة)")
                drops_list = item.get('drops')
                if isinstance(drops_list, list) and len(drops_list) > 0:
                    obtain_info.append(f"💀 **يسقط من:** {len(drops_list)} عدو/بوس")
                traders = item.get('traders') or item.get('soldBy')
                if traders:
                    obtain_info.append("💰 **التجار:** متوفر للشراء")
                price = item.get('price') or item.get('value')
                if price:
                    obtain_info.append(f"💵 **السعر:** {price}")
                if not obtain_info:
                    obtain_info.append("⚠️ **معلومات المكان غير متوفرة في الداتا**")
                    if translated_desc and translated_desc != 'لا يوجد وصف':
                        obtain_info.append(f"\n📝 {translated_desc[:150]}")
                custom_desc = "\n\n".join(obtain_info)
                intent = 'loot' if is_obtain_question else 'location' if is_location_question else None
                embed = EmbedBuilder.concise_item_response(item, intent=intent)
            else:
                embed = EmbedBuilder.concise_item_response(item, intent=None)

            if is_crafting_question:
                recipe = item.get('recipe')
                if isinstance(recipe, dict) and recipe:
                    lines = []
                    for key, amount in recipe.items():
                        if amount is None:
                            continue
                        name = str(key).replace('_', ' ')
                        lines.append(f"- {name}: {amount}")
                    if lines:
                        embed.add_field(name="مكونات التصنيع", value="\n".join(lines), inline=False)
            
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
                    extra_embed = EmbedBuilder.concise_item_response(extra_item, intent='loot')
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
            
            if use_ai:
                ai_context_parts = []
                # إضافة العنصر الأساسي
                name_for_ai = bot.search_engine.extract_name(item)
                ai_context_parts.append(f"الآيتم الأساسي: {name_for_ai}")
                
                # لو كان بحث عائلة أسلحة، نضيف الباقين للسياق
                if is_obtain_question and gun_parts_family_query:
                     ai_context_parts.append("تنبيه: تم عرض عائلة Gun Parts كاملة (Light, Heavy, Complex).")

                ai_context_parts.append("تنبيه للنظام: المستخدم رأى بطاقة المعلومات الرسمية (الندرة، السعر، الوصف، الموقع، الكرافت).")
                ai_context_parts.append("مهم: لا تكرر هذه المعلومات أبداً. لا تضع قوائم.")
                ai_context_parts.append("المطلوب: قدم نصيحة استراتيجية ذكية ومختصرة (سطرين) فقط إذا كان هناك فائدة إضافية غير موجودة في الداتا.")
                
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
            "وفيه إشاعة عن منطقة اسمها Stella Montis لكن الوصول لها غير محدد أو موثق في الداتا."
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
            "جواب من AI",
            ai_result['answer']
        )
        embed.set_footer(text=f"via {ai_result['provider']} • 🤖 {BOT_NAME}")
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
