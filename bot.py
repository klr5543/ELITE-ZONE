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
    
    # مستويات وتطوير
    'لفل': 'level',
    'ليفل': 'level',
    'مستوى': 'level',
    'مستويات': 'levels',
    'طور': 'upgrade',
    'تطوير': 'upgrade',
    'ترقية': 'upgrade',
    'طورها': 'upgrade',
    'طورها': 'upgrade',
    'طوره': 'upgrade',
    'فل': 'max',
    'فلها': 'max',
    'مفلل': 'max',
    
    # أماكن
    'خريطة': 'map',
    'منطقة': 'zone',
    'مصنع': 'factory',
    'مستودع': 'warehouse',
    'وين': 'where',
    'فين': 'where',
    'اين': 'where',
    'أين': 'where',
    'مكان': 'location',
    
    # عناصر
    'درع': 'armor',
    'خوذة': 'helmet',
    'صدرية': 'vest',
    'حقيبة': 'backpack',
    'شنطة': 'backpack',
    
    # أعداء
    'روبوت': 'bot',
    'عدو': 'enemy',
    'اعداء': 'enemies',
    'زعيم': 'boss',
    'بوس': 'boss',
    
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
        # تحويل الأرقام الرومانية والعادية لمستويات
        # "4" -> "iv", "III" -> "iii", "الى 4" -> "iv"
        roman_map = {'1': 'i', '2': 'ii', '3': 'iii', '4': 'iv', '5': 'v'}
        for num, roman in roman_map.items():
            text = re.sub(rf'\b{num}\b', roman, text)
        # إزالة الأحرف الخاصة (لكن نحتفظ بـ _ للـ id)
        text = re.sub(r'[^\w\s\u0600-\u06FF_]', ' ', text)
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
    
    def _extract_tier_from_text(self, text: str) -> int:
        """استخراج مستوى العنصر من النص (I, II, III, IV, V)"""
        if not text:
            return 0
        text = str(text).lower()
        match = re.search(r'\b(i{1,3}|iv|v)\b', text)
        if not match:
            return 0
        roman = match.group(1)
        mapping = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5}
        return mapping.get(roman, 0)
    
    def _base_name_without_tier(self, text: str) -> str:
        """إرجاع اسم العنصر بدون مستوى"""
        if not text:
            return ""
        text = str(text).strip()
        return re.sub(r'\s+(i{1,3}|iv|v)\s*$', '', text.lower())
    
    def _prefer_highest_tier_variant(self, item: dict) -> dict:
        """اختيار أعلى مستوى لنفس العنصر"""
        if not isinstance(item, dict):
            return item
        name = self.extract_name(item)
        base_name = self._base_name_without_tier(name)
        if not base_name:
            return item
        best_item = item
        best_tier = self._extract_tier_from_text(name)
        for candidate in self.db.all_data:
            if not isinstance(candidate, dict):
                continue
            candidate_name = self.extract_name(candidate)
            if not candidate_name or candidate_name == "غير معروف":
                continue
            if self._base_name_without_tier(candidate_name) != base_name:
                continue
            tier = self._extract_tier_from_text(candidate_name)
            if tier > best_tier:
                best_tier = tier
                best_item = candidate
        return best_item

    def find_quests_rewarding_item(self, item_id: str) -> list:
        """إيجاد المهام التي تعطي هذا العنصر كجائزة"""
        if not self.db or not self.db.quests:
            return []
        rewards_quests = []
        for quest in self.db.quests:
            if not isinstance(quest, dict):
                continue
            rewards = quest.get("rewardItemIds") or quest.get("grantedItemIds")
            if not isinstance(rewards, list):
                continue
            for entry in rewards:
                if not isinstance(entry, dict):
                    continue
                if entry.get("itemId") == item_id:
                    rewards_quests.append(quest)
                    break
        return rewards_quests
    
    def find_hideout_sources_for_item(self, item_id: str) -> list:
        """إيجاد محطات الـ Hideout التي تنتج/تستهلك العنصر"""
        if not self.db or not self.db.hideout:
            return []
        sources = []
        for module in self.db.hideout:
            if not isinstance(module, dict):
                continue
            productions = module.get("produces") or module.get("production") or []
            if isinstance(productions, list):
                for p in productions:
                    if isinstance(p, dict) and p.get("itemId") == item_id:
                        sources.append(module)
                        break
            requirements = module.get("requirements") or []
            if isinstance(requirements, list):
                for r in requirements:
                    if isinstance(r, dict) and r.get("itemId") == item_id:
                        sources.append(module)
                        break
        return sources
    
    def search(self, query: str, limit: int = 5) -> list:
        """البحث في قاعدة البيانات"""
        if not self.db.loaded:
            return []
        
        query_normalized = self.normalize_text(query)
        query_translated = self.translate_arabic_query(query_normalized)
        
        # كشف إذا السؤال عن تطوير/ترقية
        upgrade_keywords = ['تطوير', 'ترقية', 'طور', 'اطور', 'upgrade']
        is_upgrade_question = any(keyword in query_normalized for keyword in upgrade_keywords)
        
        # محاولة تصحيح اسم السلاح/العنصر الإنجليزي لو كان فيه خطأ بسيط (ANVEL -> ANVIL)
        english_words = re.findall(r'[a-zA-Z]+', query)
        if english_words:
            main_word = max(english_words, key=len).lower()
            english_phrase = " ".join(english_words).lower()
            
            # محاولة التقاط آخر نمط "اسم + مستوى" مثل "Anvil IV" من السؤال (مع السياق)
            tier_pattern = re.compile(r'\b([A-Za-z][A-Za-z0-9_]*)\s+(I{1,3}|IV|V)\b', re.IGNORECASE)
            tier_matches = list(tier_pattern.finditer(query))
            tier_phrase = None
            if tier_matches:
                last_match = tier_matches[-1]
                tier_phrase = f"{last_match.group(1)} {last_match.group(2)}".lower()
            
            best_item = None
            best_score = 0.0
            
            for item in self.db.all_data:
                if not isinstance(item, dict):
                    continue
                name = self.extract_name(item)
                if not name or name == "غير معروف":
                    continue
                name_lower = name.lower()
                sim_main = SequenceMatcher(None, main_word, name_lower).ratio()
                sim_phrase = SequenceMatcher(None, english_phrase, name_lower).ratio()
                sim_tier = 0.0
                if tier_phrase:
                    sim_tier = SequenceMatcher(None, tier_phrase, name_lower).ratio()
                sim = max(sim_main, sim_phrase, sim_tier)
                if sim > best_score:
                    best_score = sim
                    best_item = item
            
            # لو في تشابه قوي جداً، نرجّح هذا العنصر مباشرة
            if best_item and best_score >= 0.8:
                if is_upgrade_question:
                    best_item = self._prefer_highest_tier_variant(best_item)
                return [{
                    'item': best_item,
                    'score': 1.0,
                    'matched_field': 'name'
                }]
        
        results = []
        
        for item in self.db.all_data:
            if not isinstance(item, dict):
                continue
                
            score = 0
            matched_field = None
            
            # البحث في الحقول المختلفة (بما فيها id)
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
                        
                        # لو السؤال عن تطوير والنتيجة فيها upgradeCost، نرفع النتيجة
                        if is_upgrade_question and 'upgradeCost' in item:
                            current_score += 0.2
                        
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
                    
                    # لو السؤال عن تطوير والنتيجة فيها upgradeCost، نرفع النتيجة
                    if is_upgrade_question and 'upgradeCost' in item:
                        current_score += 0.2
                    
                    if current_score > score:
                        score = current_score
                        matched_field = field
            
            # بحث خاص في id (مهم جداً)
            item_id = item.get('id', '')
            if item_id:
                item_id_normalized = self.normalize_text(str(item_id))
                # لو الاستعلام يحتوي على id أو جزء منه
                if query_normalized in item_id_normalized or item_id_normalized in query_normalized:
                    id_score = 0.9 if query_normalized == item_id_normalized else 0.7
                    if id_score > score:
                        score = id_score
                        matched_field = 'id'
            
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
    
    async def ask_ai(self, question: str, context: str = "", mode: str = "default") -> dict:
        """سؤال الـ AI مع نظام الاحتياطي
        
        mode:
          - default: إجابة عامة عن اللعبة
          - build: اقتراح بِلْد / لودآوت
          - explain: شرح تفصيلي / تعليم لاعب جديد
        """
        
        if not self.check_daily_limit():
            return {
                'success': False,
                'answer': "⚠️ تم الوصول للحد اليومي من استخدام AI",
                'provider': None
            }
        
        base_prompt = """أنت "دليل" - بوت مساعد لمجتمع ARC Raiders العربي.
أنت خبير في لعبة ARC Raiders وتفاصيلها (الأسلحة، العتاد، المهام، المهارات، الخرائط، أنظمة اللعب).

قواعد عامة:
1. رد بالعربية الفصحى المبسطة أو لهجة سعودية خفيفة بدون مبالغة.
2. كن مختصراً ومباشراً قدر الإمكان، لا تدوّن مقالات.
3. لو ما تعرف الجواب منطقياً، قل ذلك بصراحة وبدون اختراع معلومات.
4. ركّز دائماً على معلومات اللعبة، وتجنب أي مواضيع خارجها.
5. اذكر أسماء الأسلحة والموارد والقطع بالإنجليزية كما هي في اللعبة.
6. لا تعِد نسخ نفس الجداول التي في بطاقة البوت؛ ركّز على الشرح (متى وأين ولماذا).
"""

        # تخصيص الرد حسب الـ mode
        if mode == "build":
            mode_prompt = """
أنت الآن متخصص في اقتراح Builds و Loadouts:
- اقترح سلاحاً / مهارة / Augments / Gear يناسب أسلوب اللعب المطلوب.
- أعطِ السبب لكل اختيار بشكل سطر أو سطرين فقط.
- لا تعطِ أكثر من 3–4 اقتراحات رئيسية حتى لا تُربك اللاعب.
"""
        elif mode == "explain":
            mode_prompt = """
أنت الآن مدرب يشرح للّاعبين العرب:
- اشرح الفكرة أو الميكانيك بهدوء وبخطوات.
- استخدم قوائم نقطية إن احتجت.
- لا تدخل في تفاصيل غير مهمة لو كان السؤال بسيطاً.
"""
        else:
            mode_prompt = ""

        system_prompt = f"""{base_prompt}{mode_prompt}

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
    def _find_resource_name(resource_id: str, database_manager) -> str:
        if not database_manager or not database_manager.loaded:
            return None
        for item in database_manager.items:
            if not isinstance(item, dict):
                continue
            item_id = item.get('id', '')
            if item_id == resource_id:
                name = EmbedBuilder.extract_field(item, 'name')
                if name:
                    return name
        return None
    
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
        img_url = (
            item.get('image')
            or item.get('icon')
            or item.get('imageUrl')
            or item.get('imageFilename')
        )
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
    def item_embed(item: dict, translated_desc: str = None, database_manager=None) -> discord.Embed:
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

        # وصفة التصنيع (Recipe)
        recipe = item.get('recipe')
        if isinstance(recipe, dict) and recipe:
            parts = []
            for res_id, amount in recipe.items():
                resource_name = EmbedBuilder._find_resource_name(res_id, database_manager)
                if resource_name:
                    parts.append(f"{amount}x {resource_name}")
                else:
                    readable_name = str(res_id).replace('_', ' ').title()
                    parts.append(f"{amount}x {readable_name}")
            if parts:
                embed.add_field(
                    name="🧰 وصفة التصنيع",
                    value="\n".join(parts),
                    inline=False
                )

        # تكلفة التطوير (Upgrade Cost)
        upgrade_cost = item.get('upgradeCost')
        if isinstance(upgrade_cost, dict) and upgrade_cost:
            parts = []
            for res_id, amount in upgrade_cost.items():
                # البحث عن اسم المورد الحقيقي في قاعدة البيانات
                resource_name = EmbedBuilder._find_resource_name(res_id, database_manager)
                if resource_name:
                    parts.append(f"{amount}x {resource_name}")
                else:
                    # لو ما لقيناه، نستخدم الاسم المنسق
                    readable_name = str(res_id).replace('_', ' ').title()
                    parts.append(f"{amount}x {readable_name}")
            if parts:
                embed.add_field(
                    name="🛠️ تكلفة التطوير",
                    value="\n".join(parts),
                    inline=False
                )

        # نواتج التفكيك/إعادة التدوير (اختياري لكنها مفيدة)
        recycles_into = item.get('recyclesInto')
        salvages_into = item.get('salvagesInto')
        recycle_lines = []
        if isinstance(recycles_into, dict) and recycles_into:
            recycle_lines.append("♻️ يعاد تدويره إلى:")
            for res_id, amount in recycles_into.items():
                resource_name = EmbedBuilder._find_resource_name(res_id, database_manager)
                if resource_name:
                    recycle_lines.append(f"- {amount}x {resource_name}")
                else:
                    readable_name = str(res_id).replace('_', ' ').title()
                    recycle_lines.append(f"- {amount}x {readable_name}")
        if isinstance(salvages_into, dict) and salvages_into:
            recycle_lines.append("🔧 يتفكك إلى:")
            for res_id, amount in salvages_into.items():
                resource_name = EmbedBuilder._find_resource_name(res_id, database_manager)
                if resource_name:
                    recycle_lines.append(f"- {amount}x {resource_name}")
                else:
                    readable_name = str(res_id).replace('_', ' ').title()
                    recycle_lines.append(f"- {amount}x {readable_name}")
        if recycle_lines:
            embed.add_field(
                name="♻️ التفكيك",
                value="\n".join(recycle_lines)[:500],
                inline=False
            )
        
        # صورة العنصر المصغرة (Thumbnail)
        img_url = EmbedBuilder.get_image_url(item)
        if img_url:
            embed.set_thumbnail(url=img_url)
        
        embed.set_footer(text=f"🤖 {BOT_NAME} | ARC Raiders")
        return embed
    
    @staticmethod
    def resource_preview_embed(item: dict) -> discord.Embed:
        name = EmbedBuilder.extract_field(item, 'name') or "Unknown"
        embed = discord.Embed(
            title=name,
            color=COLORS["primary"],
            timestamp=datetime.now()
        )
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
    def bot_embed(bot_data: dict) -> discord.Embed:
        name_val = bot_data.get("name") or bot_data.get("id") or "Unknown ARC"
        if isinstance(name_val, dict):
            name = name_val.get("en") or list(name_val.values())[0]
        else:
            name = str(name_val)
        
        desc = bot_data.get("description")
        if isinstance(desc, dict):
            desc = desc.get("en") or list(desc.values())[0]
        elif desc:
            desc = str(desc)
        else:
            desc = ""
        
        weakness = bot_data.get("weakness")
        if isinstance(weakness, dict):
            weakness = weakness.get("en") or list(weakness.values())[0]
        elif weakness:
            weakness = str(weakness)
        
        embed = discord.Embed(
            title=f"🤖 ARC: {name}",
            description=desc[:500] if desc else "لا يوجد وصف",
            color=COLORS["primary"],
            timestamp=datetime.now()
        )
        
        bot_type = bot_data.get("type")
        if isinstance(bot_type, dict):
            bot_type = bot_type.get("en") or list(bot_type.values())[0]
        if bot_type:
            embed.add_field(name="🏷️ النوع", value=str(bot_type), inline=True)
        
        threat = bot_data.get("threat")
        if threat:
            embed.add_field(name="⚠️ مستوى التهديد", value=str(threat), inline=True)
        
        if weakness:
            embed.add_field(name="🎯 نقطة الضعف", value=weakness[:300], inline=False)
        
        maps = bot_data.get("maps")
        if isinstance(maps, list) and maps:
            embed.add_field(
                name="🗺️ يظهر في الخرائط",
                value=", ".join(maps)[:300],
                inline=False
            )
        
        destroy_xp = bot_data.get("destroyXp")
        loot_xp = bot_data.get("lootXp")
        if destroy_xp or loot_xp:
            xp_lines = []
            if destroy_xp:
                xp_lines.append(f"- تدمير: {destroy_xp}")
            if loot_xp:
                xp_lines.append(f"- لوت: {loot_xp}")
            embed.add_field(
                name="📊 الخبرة (XP)",
                value="\n".join(xp_lines),
                inline=True
            )
        
        drops = bot_data.get("drops")
        if isinstance(drops, list) and drops:
            drops_text = "\n".join([f"- {d}" for d in drops])[:500]
            embed.add_field(
                name="🎁 اللوت المحتمل",
                value=drops_text,
                inline=False
            )
        
        img_url = EmbedBuilder.get_image_url(bot_data)
        if img_url:
            embed.set_thumbnail(url=img_url)
        
        embed.set_footer(text=f"🤖 {BOT_NAME} | ARC Raiders")
        return embed
    
    @staticmethod
    def quest_embed(quest: dict, database_manager=None) -> discord.Embed:
        name = EmbedBuilder.extract_field(quest, "name") or "Quest"
        
        desc = quest.get("description")
        if isinstance(desc, dict):
            desc = desc.get("en") or list(desc.values())[0]
        elif desc:
            desc = str(desc)
        else:
            desc = ""
        
        embed = discord.Embed(
            title=f"📜 {name}",
            description=desc[:500] if desc else "لا يوجد وصف",
            color=COLORS["info"],
            timestamp=datetime.now()
        )
        
        trader = quest.get("trader")
        if trader:
            embed.add_field(name="🧑‍💼 التاجر", value=str(trader), inline=True)
        
        xp = quest.get("xp")
        if xp is not None:
            embed.add_field(name="📊 الخبرة", value=str(xp), inline=True)
        
        objectives = quest.get("objectives")
        if isinstance(objectives, list) and objectives:
            lines = []
            for obj in objectives:
                if isinstance(obj, dict):
                    text = obj.get("en") or list(obj.values())[0]
                else:
                    text = str(obj)
                if text:
                    lines.append(f"- {text}")
            if lines:
                embed.add_field(
                    name="🎯 الأهداف",
                    value="\n".join(lines)[:500],
                    inline=False
                )
        
        required_items = quest.get("requiredItemIds") or quest.get("requiredItems")
        if isinstance(required_items, list) and required_items:
            parts = []
            for entry in required_items:
                if not isinstance(entry, dict):
                    continue
                item_id = entry.get("itemId")
                quantity = entry.get("quantity", 1)
                display_name = None
                if item_id and database_manager:
                    display_name = EmbedBuilder._find_resource_name(item_id, database_manager)
                if not display_name and item_id:
                    display_name = str(item_id).replace("_", " ").title()
                if display_name:
                    parts.append(f"- {quantity}x {display_name}")
            if parts:
                embed.add_field(
                    name="📦 المتطلبات",
                    value="\n".join(parts)[:500],
                    inline=False
                )
        
        rewards = quest.get("rewardItemIds") or quest.get("grantedItemIds")
        if isinstance(rewards, list) and rewards:
            parts = []
            for entry in rewards:
                if not isinstance(entry, dict):
                    continue
                item_id = entry.get("itemId")
                quantity = entry.get("quantity", 1)
                display_name = None
                if item_id and database_manager:
                    display_name = EmbedBuilder._find_resource_name(item_id, database_manager)
                if not display_name and item_id:
                    display_name = str(item_id).replace("_", " ").title()
                if display_name:
                    parts.append(f"- {quantity}x {display_name}")
            if parts:
                embed.add_field(
                    name="🎁 الجوائز",
                    value="\n".join(parts)[:500],
                    inline=False
                )
        
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
        self.lfg_sessions = {}
        
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

@bot.tree.command(name="item", description="جلب معلومات مفصلة عن عنصر من اللعبة")
@app_commands.describe(name="اسم أو جزء من اسم/ID العنصر")
async def item_command(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    
    if not bot.search_engine or not bot.database or not bot.database.loaded:
        embed = EmbedBuilder.error(
            "خطأ في النظام",
            "قاعدة بيانات اللعبة غير جاهزة حالياً."
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    results = bot.search_engine.search(name, limit=1)
    if not results:
        embed = EmbedBuilder.warning(
            "لا نتائج",
            f"ما لقيت أي عنصر يطابق **{name}**"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    item = results[0]["item"]
    description = None
    if "description" in item:
        desc_val = item["description"]
        if isinstance(desc_val, dict):
            description = desc_val.get("en") or desc_val.get("ar") or list(desc_val.values())[0]
        else:
            description = str(desc_val)
    translated_desc = None
    if description and description != "لا يوجد وصف":
        translated_desc = await bot.ai_manager.translate_to_arabic(description)
    
    embed = EmbedBuilder.item_embed(item, translated_desc, bot.database)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="arc", description="معلومات عن أحد أعداء ARC في اللعبة")
@app_commands.describe(name="اسم العدو (Tick, Queen, Hornet, ...)")
async def arc_command(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    
    if not bot.database or not bot.database.loaded or not bot.database.bots:
        embed = EmbedBuilder.error(
            "خطأ في البيانات",
            "بيانات الأعداء غير متاحة حالياً."
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    candidates = []
    query = name.lower().strip()
    for bot_data in bot.database.bots:
        label = ""
        if isinstance(bot_data, dict):
            bot_name = bot_data.get("name")
            if isinstance(bot_name, dict):
                label = bot_name.get("en") or list(bot_name.values())[0]
            elif isinstance(bot_name, str):
                label = bot_name
            bot_id = str(bot_data.get("id", ""))
            label_full = f"{bot_id} {label}".strip()
            score = bot.search_engine.calculate_similarity(query, label_full)
            if score > 0.3:
                candidates.append((score, bot_data))
    if not candidates:
        embed = EmbedBuilder.warning(
            "لا نتائج",
            f"ما لقيت أي عدو يطابق **{name}**"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    candidates.sort(key=lambda x: x[0], reverse=True)
    best_bot = candidates[0][1]
    embed = EmbedBuilder.bot_embed(best_bot)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="quest", description="عرض تفاصيل مهمة من مهام اللعبة")
@app_commands.describe(name="اسم أو جزء من اسم المهمة")
async def quest_command(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    
    if not bot.database or not bot.database.loaded or not bot.database.quests:
        embed = EmbedBuilder.error(
            "خطأ في البيانات",
            "بيانات المهام غير متاحة حالياً."
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    candidates = []
    query = name.lower().strip()
    for quest in bot.database.quests:
        if not isinstance(quest, dict):
            continue
        quest_name = quest.get("name")
        label = ""
        if isinstance(quest_name, dict):
            label = quest_name.get("en") or list(quest_name.values())[0]
        elif isinstance(quest_name, str):
            label = quest_name
        quest_id = str(quest.get("id", ""))
        label_full = f"{quest_id} {label}".strip()
        score = bot.search_engine.calculate_similarity(query, label_full)
        if score > 0.3:
            candidates.append((score, quest))
    if not candidates:
        embed = EmbedBuilder.warning(
            "لا نتائج",
            f"ما لقيت أي مهمة تطابق **{name}**"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    candidates.sort(key=lambda x: x[0], reverse=True)
    best_quest = candidates[0][1]
    embed = EmbedBuilder.quest_embed(best_quest, bot.database)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="map", description="معلومات عن خريطة من خرائط ARC Raiders")
@app_commands.describe(name="اسم الخريطة")
async def map_command(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    
    if not bot.database or not bot.database.loaded or not bot.database.maps:
        embed = EmbedBuilder.error(
            "خطأ في البيانات",
            "بيانات الخرائط غير متاحة حالياً."
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    candidates = []
    query = name.lower().strip()
    for m in bot.database.maps:
        if not isinstance(m, dict):
            continue
        map_name = m.get("name") or m.get("displayName") or m.get("id")
        label = ""
        if isinstance(map_name, dict):
            label = map_name.get("en") or list(map_name.values())[0]
        elif isinstance(map_name, str):
            label = map_name
        map_id = str(m.get("id", ""))
        label_full = f"{map_id} {label}".strip()
        score = bot.search_engine.calculate_similarity(query, label_full)
        if score > 0.3:
            candidates.append((score, m))
    if not candidates:
        embed = EmbedBuilder.warning(
            "لا نتائج",
            f"ما لقيت أي خريطة تطابق **{name}**"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    candidates.sort(key=lambda x: x[0], reverse=True)
    best_map = candidates[0][1]
    map_name = ""
    name_val = best_map.get("name") or best_map.get("displayName") or best_map.get("id")
    if isinstance(name_val, dict):
        map_name = name_val.get("en") or list(name_val.values())[0]
    elif isinstance(name_val, str):
        map_name = name_val
    else:
        map_name = str(name_val)
    embed = EmbedBuilder.map_embed(map_name, best_map)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="lfg", description="إنشاء إعلان LFG لتكوين فريق لعب")
@app_commands.describe(
    mode="نوع اللعب (مثال: PvE, PvP, Chill)",
    slots="عدد اللاعبين المطلوبين (غيرك)",
    note="وصف قصير للجلسة أو المتطلبات"
)
async def lfg_command(
    interaction: discord.Interaction,
    mode: str,
    slots: app_commands.Range[int, 1, 3],
    note: str = ""
):
    await interaction.response.defer(ephemeral=True)
    
    channel = interaction.channel
    host = interaction.user
    
    title_mode = mode.strip() or "ARC Raiders"
    embed = discord.Embed(
        title=f"🎮 LFG - {title_mode}",
        color=COLORS["primary"],
        timestamp=datetime.now()
    )
    embed.add_field(name="المضيف", value=host.mention, inline=True)
    embed.add_field(name="اللاعبون المطلوبون", value=str(slots), inline=True)
    if note:
        embed.add_field(name="الوصف", value=note[:200], inline=False)
    embed.add_field(name="المنضمّون", value=f"- {host.mention}", inline=False)
    embed.set_footer(text="اضغط ✅ للانضمام • ❌ لإلغاء الإعلان (للمضيف)")
    
    msg = await channel.send(embed=embed)
    bot.lfg_sessions[msg.id] = {
        "owner_id": host.id,
        "max_slots": slots + 1,
        "members": [host.id],
        "mode": title_mode,
        "note": note[:200]
    }
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    
    await interaction.followup.send("تم إنشاء إعلان LFG في هذه القناة.", ephemeral=True)

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


@bot.tree.command(name="build", description="اقتراح بِلْد / لودآوت حسب أسلوب لعبك")
@app_commands.describe(
    weapon="اسم السلاح (اختياري)",
    role="أسلوب اللعب (مثال: solo, team, support, aggressive, cautious)"
)
async def build_command(
    interaction: discord.Interaction,
    weapon: str = "",
    role: str = ""
):
    """أمر اقتراح بِلْد"""
    await interaction.response.defer()

    # نجرب نربط مع بيانات اللعبة لو أعطى سلاح
    context_parts = []
    if weapon and bot.search_engine:
        results = bot.search_engine.search(weapon, limit=1)
        if results:
            item = results[0]["item"]
            name = bot.search_engine.extract_name(item)
            context_parts.append(f"السلاح: {name}")

    if role:
        context_parts.append(f"أسلوب اللعب المطلوب: {role}")

    context = " | ".join(context_parts) if context_parts else ""

    question = f"اقترح لي بِلْد مناسب في ARC Raiders {f'مع سلاح {weapon}' if weapon else ''} {f'لأسلوب {role}' if role else ''}."

    ai_result = await bot.ai_manager.ask_ai(question, context=context, mode="build")

    if ai_result["success"]:
        embed = EmbedBuilder.success(
            "اقتراح بِلْد",
            ai_result["answer"]
        )
        embed.set_footer(text=f"via {ai_result['provider']} • 🤖 {BOT_NAME}")
    else:
        embed = EmbedBuilder.error(
            "عذراً",
            "ما قدرت أجهز بِلْد حالياً.\n\n💡 جرب تغيّر طريقة السؤال أو جرّب لاحقاً."
        )

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="explain", description="خل دليل يشرح لك شيء عن اللعبة")
@app_commands.describe(topic="اكتب الشيء اللي تبي شرحه (ميكانيك، مهمة، نظام، سلاح، الخ)")
async def explain_command(interaction: discord.Interaction, topic: str):
    """أمر شرح ميكانيك / نظام"""
    await interaction.response.defer()

    context = ""
    # نحاول نربط بالبيانات لو يتعلق بسلاح / مهمة / عدو
    if bot.search_engine:
        results = bot.search_engine.search(topic, limit=1)
        if results:
            item = results[0]["item"]
            name = bot.search_engine.extract_name(item)
            context = f"الموضوع يتعلق بالعنصر: {name}"

    question = f"اشرح للاعب عربي جديد في ARC Raiders: {topic}"

    ai_result = await bot.ai_manager.ask_ai(question, context=context, mode="explain")

    if ai_result["success"]:
        embed = EmbedBuilder.success(
            "شرح من دليل",
            ai_result["answer"]
        )
        embed.set_footer(text=f"via {ai_result['provider']} • 🤖 {BOT_NAME}")
    else:
        embed = EmbedBuilder.error(
            "عذراً",
            "ما قدرت أشرح هذا الشيء حالياً.\n\n💡 جرّب تسأل بطريقة أبسط."
        )

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
    
    # التأكد من أن search_engine جاهز
    if not bot.search_engine:
        embed = EmbedBuilder.error(
            "خطأ في النظام",
            "البحث غير متاح حالياً. جرب بعد قليل."
        )
        await message.reply(embed=embed)
        return
    
    resource_keywords = [
        'mechanical_components',
        'heavy_gun_parts',
        'simple_gun_parts',
        'advanced_mechanical_components',
        'advanced_simple_gun_parts'
    ]
    if any(keyword in content_lower for keyword in resource_keywords):
        await ask_ai_and_reply(message, question)
        return
    
    # البحث في قاعدة البيانات
    results = bot.search_engine.search(question, limit=1)
    
    if results and results[0]['score'] > 0.6:
        # وجدنا نتيجة جيدة!
        result = results[0]
        item = result['item']
        
        # تحقق إضافي: لو السؤال فيه اسم محدد، نتأكد النتيجة تطابقه
        item_name = bot.search_engine.extract_name(item).lower()
        item_id = str(item.get('id', '')).lower()
        
        # استخراج الكلمات الإنجليزية من السؤال (أسماء العناصر)
        english_words = re.findall(r'[a-zA-Z]+', content)
        
        # لو في اسم إنجليزي بالسؤال، نتأكد موجود بالنتيجة
        skip_result = False
        if english_words:
            main_word = max(english_words, key=len).lower()  # أطول كلمة إنجليزية
            # التحقق من الاسم أو الـ id
            if len(main_word) > 3:
                name_match = main_word in item_name or item_name in main_word
                id_match = main_word in item_id or item_id in main_word
                
                # لو السؤال فيه رقم (مستوى)، نتحقق من الـ id
                has_level = bool(re.search(r'\b[1-5]\b|\b[ivx]+\b', content.lower()))
                if has_level:
                    # لو السؤال عن مستوى معين، نتأكد الـ id يحتوي المستوى
                    level_match = any(level in item_id for level in ['i', 'ii', 'iii', 'iv', 'v'])
                    if not (name_match or id_match or level_match):
                        skip_result = True
                elif not (name_match or id_match):
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
            
            embed = EmbedBuilder.item_embed(item, translated_desc, bot.database)
            
            location_keywords = ['وين', 'اين', 'أين', 'مكان', 'موقع', 'القى', 'الاقي', 'where', 'location', 'find']
            obtain_keywords = ['احصل', 'أحصل', 'الحصول', 'اطلع', 'أطلع', 'drop', 'get', 'farm', 'اول مره', 'أول مره', 'اول مرة', 'أول مرة']
            upgrade_keywords = ['تطوير', 'ترقية', 'طور', 'اطور', 'أطور', 'قطع تطوير', 'upgrade']
            strength_keywords = ['قوته', 'قوي', 'قوية', 'قوتها', 'يستاهل', 'يسوى', 'افضل', 'أقوى', 'strong', 'meta']
            dismantle_keywords = ['فك', 'فكك', 'تفكيك', 'لو فككته', 'كسرت', 'كسر', 'recycle', 'salvage', 'dismantle']
            is_location_question = any(keyword in content_lower for keyword in location_keywords)
            is_obtain_question = any(keyword in content_lower for keyword in obtain_keywords)
            is_upgrade_question = any(keyword in content_lower for keyword in upgrade_keywords)
            is_strength_question = any(keyword in content_lower for keyword in strength_keywords)
            is_dismantle_question = any(keyword in content_lower for keyword in dismantle_keywords)
            
            reply = await message.reply(embed=embed)
            
            resource_ids = set()
            recipe = item.get('recipe')
            upgrade_cost = item.get('upgradeCost')
            recycles_into = item.get('recyclesInto')
            salvages_into = item.get('salvagesInto')
            if isinstance(recipe, dict):
                resource_ids.update(recipe.keys())
            if isinstance(upgrade_cost, dict):
                resource_ids.update(upgrade_cost.keys())
            if isinstance(recycles_into, dict):
                resource_ids.update(recycles_into.keys())
            if isinstance(salvages_into, dict):
                resource_ids.update(salvages_into.keys())
            
            if resource_ids and bot.database and bot.database.items:
                sent = 0
                for res_id in resource_ids:
                    res_item = None
                    for base_item in bot.database.items:
                        if isinstance(base_item, dict) and base_item.get('id') == res_id:
                            res_item = base_item
                            break
                    if not res_item:
                        continue
                    res_embed = EmbedBuilder.resource_preview_embed(res_item)
                    await message.channel.send(embed=res_embed)
                    sent += 1
                    if sent >= 4:
                        break
            
            if is_location_question:
                location = item.get('location') or item.get('spawn_location') or item.get('map')
                if location:
                    if isinstance(location, dict):
                        location = location.get('en') or list(location.values())[0]
                    
                    map_embed = EmbedBuilder.map_embed(str(location), item)
                    await message.channel.send(embed=map_embed)
            
            if is_dismantle_question:
                followup_question = (
                    f"اللاعب يسأل ماذا يحصل لو فكك أو أعاد تدوير العنصر {bot.search_engine.extract_name(item)} في ARC Raiders. "
                    f"السؤال الأصلي: \"{content}\". بالاعتماد على بيانات اللعبة في السياق، اشرح بالعربية ما هي الموارد التي يحصل عليها عند التفكيك "
                    f"(recyclesInto / salvagesInto) وهل من المنطقي تفكيكه أم الاحتفاظ به."
                )
                await ask_ai_and_reply(message, followup_question)
            elif is_upgrade_question:
                followup_question = (
                    f"اللاعب يسأل عن متطلبات أو قطع تطوير العنصر {bot.search_engine.extract_name(item)} في ARC Raiders. "
                    f"السؤال الأصلي: \"{content}\". بالاعتماد على بيانات اللعبة في السياق، اشرح بالعربية وبشكل واضح ما هي موارد التطوير المطلوبة "
                    f"وأي ملاحظات مهمة عن الانتقال بين المستويات إن وجدت، بدون اختراع أرقام غير موجودة."
                )
                await ask_ai_and_reply(message, followup_question)
            elif is_obtain_question:
                followup_question = (
                    f"كيف يمكن الحصول على العنصر {bot.search_engine.extract_name(item)} لأول مرة في ARC Raiders؟ "
                    f"السؤال الأصلي: \"{content}\". وضح أفضل الطرق الثابتة مثل المهام، الدروب من الأعداء، التصنيع، أو وحدات الـ Hideout إن كانت موجودة في البيانات."
                )
                await ask_ai_and_reply(message, followup_question)
            elif is_strength_question:
                followup_question = (
                    f"اللاعب يسأل عن قوة العنصر {bot.search_engine.extract_name(item)} في ARC Raiders. "
                    f"السؤال الأصلي: \"{content}\". قيم قوة هذا العنصر بشكل عام بالاعتماد على وصفه ونوعه وندرته في السياق، "
                    f"واشرح متى يكون مفيداً ومتى قد لا يكون خياراً جيداً، بدون اختراع أرقام تفصيلية غير موجودة."
                )
                await ask_ai_and_reply(message, followup_question)
            
            # حفظ السياق
            name = bot.search_engine.extract_name(item)
            bot.context_manager.set_context(message.author.id, name, item)
            
            # إضافة reactions بسيطة
            await reply.add_reaction('✅')  # إجابة صحيحة
            await reply.add_reaction('❌')  # إجابة خاطئة
            
            bot.questions_answered += 1
            return
    
    # لو skip_result أو النتيجة ضعيفة
    if results and results[0]['score'] > 0.3:
        # نتيجة متوسطة - نعرض اقتراحات
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
        else:
            # نستخدم AI
            await ask_ai_and_reply(message, question)
    
    else:
        # لا نتائج - نستخدم AI
        await ask_ai_and_reply(message, question)


async def ask_ai_and_reply(message: discord.Message, question: str):
    """سؤال الـ AI والرد"""
    thinking_msg = await message.reply("🔍 أبحث لك...")
    
    context_parts = []
    user_context = bot.context_manager.get_context(message.author.id)
    if user_context:
        context_parts.append(f"المستخدم كان يسأل سابقاً عن: {user_context['item']}")
    
    knowledge_context = ""
    if bot.search_engine and bot.database and bot.database.loaded:
        try:
            search_results = bot.search_engine.search(question, limit=3)
            snippets = []
            for result in search_results:
                item = result.get('item')
                if not isinstance(item, dict):
                    continue
                name = bot.search_engine.extract_name(item)
                if not name or name == "غير معروف":
                    continue
                desc_val = item.get('description')
                if isinstance(desc_val, dict):
                    desc = desc_val.get('en') or desc_val.get('ar') or list(desc_val.values())[0]
                elif desc_val:
                    desc = str(desc_val)
                else:
                    desc = ""
                if desc:
                    desc = desc.replace('\n', ' ')[:120]
                item_id = str(item.get("id", ""))
                extra_parts = []
                upgrade_cost = item.get("upgradeCost")
                if isinstance(upgrade_cost, dict) and upgrade_cost:
                    cost_parts = []
                    for res_id, amount in upgrade_cost.items():
                        res_name = EmbedBuilder._find_resource_name(res_id, bot.database)
                        label = res_name or str(res_id).replace("_", " ")
                        cost_parts.append(f"{amount}x {label}")
                    if cost_parts:
                        extra_parts.append("متطلبات تطوير: " + ", ".join(cost_parts))
                recycles_into = item.get("recyclesInto") or item.get("salvagesInto")
                if isinstance(recycles_into, dict) and recycles_into:
                    recycle_parts = []
                    for res_id, amount in recycles_into.items():
                        res_name = EmbedBuilder._find_resource_name(res_id, bot.database)
                        label = res_name or str(res_id).replace("_", " ")
                        recycle_parts.append(f"{amount}x {label}")
                    if recycle_parts:
                        extra_parts.append("يعاد تدويره إلى: " + ", ".join(recycle_parts))
                quests = bot.search_engine.find_quests_rewarding_item(item_id)
                if quests:
                    extra_parts.append(f"يُكافِئ عليه في {len(quests)} مهمة على الأقل.")
                hideout_sources = bot.search_engine.find_hideout_sources_for_item(item_id)
                if hideout_sources:
                    extra_parts.append("مرتبط بوحدات الـ Hideout أو التصنيع/التفكيك.")
                extra = (" " + " | ".join(extra_parts)) if extra_parts else ""
                snippets.append(f"- {name} ({item_id}): {desc}{extra}")
            if snippets:
                knowledge_context = "مقتطفات قصيرة من بيانات ARC Raiders (عناصر + مهام + Hideout):\n" + "\n".join(snippets)
        except Exception as e:
            logger.warning(f"خطأ في بناء سياق بيانات اللعبة للـ AI: {e}")
    
    if knowledge_context:
        context_parts.append(knowledge_context)
    
    context = "\n".join(context_parts) if context_parts else ""
    
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
    
    emoji = str(reaction.emoji)
    
    if reaction.message.id in bot.lfg_sessions:
        session = bot.lfg_sessions[reaction.message.id]
        if emoji == '✅':
            if user.id not in session['members'] and len(session['members']) < session['max_slots']:
                session['members'].append(user.id)
                members_text = "\n".join([f"- <@{uid}>" for uid in session['members']])
                embed = reaction.message.embeds[0] if reaction.message.embeds else discord.Embed(color=COLORS["primary"])
                for field in embed.fields:
                    if field.name == "المنضمّون":
                        embed.remove_field(embed.fields.index(field))
                        break
                embed.add_field(name="المنضمّون", value=members_text, inline=False)
                await reaction.message.edit(embed=embed)
        elif emoji == '❌' and user.id == session['owner_id']:
            del bot.lfg_sessions[reaction.message.id]
            await reaction.message.delete()
        return
    
    if reaction.message.author != bot.user:
        return
    
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
