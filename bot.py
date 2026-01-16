# بوت "دليل" - Daleel Bot (single-file, مُعدّل)
# ---------------------------------------------------------
# ملاحظة: انسخ هذا الملف كاملًا واستبدل به bot.py في مشروعك.
# هذا الملف يجمع:
# - تحميل البيانات من مجلد arcraiders-data/
# - محرك بحث ذكي يدعم العربي/إنجليزي وتحسين المطابقة
# - رد مختصر أولاً + زر "عرض التفاصيل" لعرض Embed مفصّل
# - تكاملات AI كخيار احتياطي (إذا مفعلت مفاتيح API)
# - تحكم بالسياق، منع سبام، أزرار تقييم، وإحصائيات
# ---------------------------------------------------------

import os
import re
import json
import logging
import asyncio
from pathlib import Path
from functools import lru_cache
from difflib import SequenceMatcher
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from dotenv import load_dotenv

# Optional: rapidfuzz gives better fuzzy matching if installed
try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except Exception:
    HAS_RAPIDFUZZ = False

# -------------------------
# Load environment
# -------------------------
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_GUILD_ID = int(os.getenv('ALLOWED_GUILD_ID', '621014916173791288'))
ALLOWED_CHANNEL_ID = int(os.getenv('ALLOWED_CHANNEL_ID', '1459709364301594848'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '1459724977346445429'))
OWNER_ID = int(os.getenv('OWNER_ID', '595228721946820614'))

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

BOT_NAME = "دليل"
BOT_VERSION = "2.0.1"

# -------------------------
# Logging
# -------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Daleel')

# -------------------------
# Constants / Mappings
# -------------------------
IMAGES_BASE_URL = "https://raw.githubusercontent.com/RaidTheory/arcraiders-data/main/images"

COLORS = {
    "success": 0x2ecc71,
    "error": 0xe74c3c,
    "warning": 0xf39c12,
    "info": 0x3498db,
    "primary": 0x9b59b6,
}

ARABIC_TO_ENGLISH = {
    # common tokens (extendable)
    'سلاح': 'weapon', 'اسلحة': 'weapons', 'بندقية': 'rifle', 'مسدس': 'pistol',
    'رشاش': 'smg', 'قناص': 'sniper', 'شوتقن': 'shotgun',
    'مخطط': 'blueprint', 'مخطوطة': 'blueprint', 'تصنيع': 'craft',
    'طاولة': 'workbench', 'ادوات': 'materials', 'أدوات': 'materials',
    'مكونات': 'components', 'موقع': '', 'وين': '', 'اين': '', 'أين': '',
    'كيف': '', 'وش': '', 'ابغى': '', 'ابي': '', 'اعطني': '', 'عطني': '',
    'فلير': 'flare', 'كوين': 'queen', 'ذهبي': 'legendary', 'بنفسجي': 'epic',
    'ازرق': 'rare', 'اخضر': 'uncommon', 'ابيض': 'common'
}

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "arcraiders-data"

# -------------------------
# Utilities: normalize and similarity
# -------------------------
def normalize_text(s: Optional[str]) -> str:
    if not s:
        return ""
    s = str(s).lower()
    s = re.sub(r"[^\w\s\u0600-\u06FF\-]", " ", s)  # keep arabic letters, alnum, hyphen
    s = re.sub(r"\s+", " ", s).strip()
    return s

def translate_arabic_tokens(text: str) -> str:
    return " ".join(ARABIC_TO_ENGLISH.get(t, t) for t in text.split())

def similarity_score(a: str, b: str) -> float:
    a = normalize_text(a)
    b = normalize_text(b)
    if HAS_RAPIDFUZZ:
        try:
            return fuzz.token_sort_ratio(a, b) / 100.0
        except Exception:
            pass
    return SequenceMatcher(None, a, b).ratio()

# -------------------------
# Database Manager
# -------------------------
class DatabaseManager:
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

    def load_all(self) -> bool:
        base_path = DATA_DIR
        if not base_path.exists():
            logger.warning("مجلد arcraiders-data غير موجود!")
            return False
        try:
            # load directories
            for folder in ['items', 'quests', 'hideout', 'map-events']:
                path = base_path / folder
                if path.exists():
                    for f in path.glob("*.json"):
                        try:
                            with open(f, 'r', encoding='utf-8') as fh:
                                data = json.load(fh)
                                if isinstance(data, list):
                                    self.all_data.extend(data)
                                elif isinstance(data, dict):
                                    self.all_data.append(data)
                        except Exception as e:
                            logger.error(f"خطأ في تحميل {f}: {e}")

            # load main files
            for fname, dest in [
                ('bots.json', 'bots'),
                ('maps.json', 'maps'),
                ('trades.json', 'trades'),
                ('skillNodes.json', 'skills'),
                ('projects.json', 'projects')
            ]:
                fpath = base_path / fname
                if fpath.exists():
                    try:
                        with open(fpath, 'r', encoding='utf-8') as fh:
                            data = json.load(fh)
                            if isinstance(data, list):
                                getattr(self, dest).extend(data)
                                self.all_data.extend(data)
                            elif isinstance(data, dict):
                                getattr(self, dest).append(data)
                                self.all_data.append(data)
                    except Exception as e:
                        logger.error(f"خطأ في تحميل {fname}: {e}")

            # load items folder explicitly to items list for some logic
            items_path = base_path / 'items'
            if items_path.exists():
                for f in items_path.glob('*.json'):
                    try:
                        with open(f, 'r', encoding='utf-8') as fh:
                            data = json.load(fh)
                            if isinstance(data, list):
                                self.items.extend(data)
                            elif isinstance(data, dict):
                                self.items.append(data)
                    except Exception as e:
                        logger.error(f"خطأ في تحميل item file {f}: {e}")

            self.loaded = True
            logger.info(f"✅ تم تحميل قاعدة البيانات: {len(self.all_data)} عناصر إجمالاً")
            return True
        except Exception as e:
            logger.error(f"خطأ في تحميل قاعدة البيانات: {e}")
            return False

    def get_stats(self):
        return {
            'items': len(self.items),
            'total': len(self.all_data),
            'bots': len(self.bots),
            'maps': len(self.maps),
            'trades': len(self.trades),
            'skills': len(self.skills),
            'projects': len(self.projects)
        }

# -------------------------
# Search Engine
# -------------------------
class SearchEngine:
    def __init__(self, db: DatabaseManager):
        self.db = db

    @staticmethod
    def normalize(text: str) -> str:
        return normalize_text(text)

    def translate_query(self, q: str) -> str:
        return translate_arabic_tokens(q)

    def calculate_match_score(self, query: str, text: str) -> float:
        if not query or not text:
            return 0.0
        q = normalize_text(query)
        t = normalize_text(text)
        if q == t:
            return 1.0
        if q in t:
            return 0.85 + min(0.15, len(q)/max(1,len(t))*0.1)
        q_words = q.split()
        matches = sum(1 for w in q_words if w in t)
        if matches == len(q_words) and matches>0:
            return 0.8 + 0.15 * (matches/len(q_words))
        if matches>0:
            return 0.5 + 0.3 * (matches/len(q_words))
        # fallback fuzzy
        return similarity_score(q, t) * 0.7

    def search(self, query: str, limit: int = 5) -> List[dict]:
        if not self.db.loaded:
            return []
        q_norm = normalize_text(query)
        q_trans = normalize_text(self.translate_query(query))
        results = []
        for item in self.db.all_data:
            if not isinstance(item, dict):
                continue
            score = 0.0
            matched_field = None
            fields = ['id', 'name', 'title', 'displayName', 'description', 'category', 'type', 'location', 'nameKey', 'rarity']
            for field in fields:
                if field not in item:
                    continue
                val = item[field]
                if isinstance(val, dict):
                    for v in val.values():
                        if not v or not isinstance(v, str):
                            continue
                        s1 = self.calculate_match_score(q_norm, v)
                        s2 = self.calculate_match_score(q_trans, v)
                        cur = max(s1, s2)
                        if cur > score:
                            score = cur
                            matched_field = field
                    if score >= 0.95:
                        break
                elif isinstance(val, str):
                    s1 = self.calculate_match_score(q_norm, val)
                    s2 = self.calculate_match_score(q_trans, val)
                    cur = max(s1, s2)
                    if cur > score:
                        score = cur
                        matched_field = field
            if score > 0.3:
                results.append({'item': item, 'score': score, 'matched_field': matched_field})
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

    def extract_name(self, item: dict) -> str:
        for k in ['name', 'title', 'displayName', 'nameKey']:
            if k in item:
                v = item[k]
                if isinstance(v, dict):
                    return v.get('ar') or v.get('en') or next(iter(v.values()))
                elif isinstance(v, str):
                    return v
        return item.get('id') or 'غير معروف'

    def find_similar(self, query: str, limit: int = 3) -> List[str]:
        res = self.search(query, limit=limit)
        names = []
        for r in res:
            n = self.extract_name(r['item'])
            if n and n not in names:
                names.append(n)
        return names

# -------------------------
# AI Manager
# -------------------------
class AIManager:
    def __init__(self):
        self.daily_usage = 0
        self.daily_limit = 50
        self.last_reset = datetime.now().date()
        self.usage_stats = {'deepseek':0,'groq':0,'openai':0,'anthropic':0,'google':0}
        self.translation_cache = {}

    def check_daily(self) -> bool:
        today = datetime.now().date()
        if today > self.last_reset:
            self.daily_usage = 0
            self.last_reset = today
        return self.daily_usage < self.daily_limit

    async def translate_to_arabic(self, text: str) -> str:
        if not text or len(text)<3:
            return text
        key = text[:120]
        if key in self.translation_cache:
            return self.translation_cache[key]
        if any('\u0600' <= c <= '\u06FF' for c in text):
            return text
        # use Groq/OpenAI/Google per availability (best-effort)
        try:
            if GROQ_API_KEY:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        'https://api.groq.com/openai/v1/chat/completions',
                        headers={'Authorization': f'Bearer {GROQ_API_KEY}','Content-Type':'application/json'},
                        json={'model':'llama-3.3-70b-versatile','messages':[{'role':'system','content':'ترجم النص التالي للعربية دون شرح.'},{'role':'user','content':text}], 'max_tokens':300,'temperature':0.2},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        if resp.status==200:
                            data = await resp.json()
                            out = data['choices'][0]['message']['content'].strip()
                            self.translation_cache[key] = out
                            return out
        except Exception:
            pass
        return text

    async def ask_ai(self, question: str, context: str = "") -> dict:
        if not any([DEEPSEEK_API_KEY,GROQ_API_KEY,OPENAI_API_KEY,ANTHROPIC_API_KEY,GOOGLE_API_KEY]):
            return {'success':False,'answer':'الذكاء الاصطناعي غير مفعل.','provider':None}
        if not self.check_daily():
            return {'success':False,'answer':'تم الوصول للحد اليومي للـ AI.','provider':None}
        # system prompt: concise Arabic
        system_prompt = f"""أنت "دليل" - بوت مختصر باللغة العربية لمجتمع ARC Raiders. أجب بجملة أو جملتين واضحين، ثم اختِمُّ بـ "لمزيد: اضغط عرض التفاصيل". لا تكتب فلسفة أو شروحات طويلة. {('سياق: '+context) if context else ''}"""
        # try providers in order
        providers = [
            ('deepseek', self._ask_deepseek),
            ('groq', self._ask_groq),
            ('openai', self._ask_openai),
            ('anthropic', self._ask_anthropic),
            ('google', self._ask_google),
        ]
        for name, func in providers:
            try:
                res = await func(question, system_prompt)
                if res:
                    self.daily_usage += 1
                    self.usage_stats[name] = self.usage_stats.get(name,0)+1
                    return {'success':True,'answer':res,'provider':name}
            except Exception as e:
                logger.warning(f"AI provider {name} failed: {e}")
                continue
        return {'success':False,'answer':'فشل الاتصال بمزودي AI','provider':None}

    async def _ask_deepseek(self, question, system_prompt):
        if not DEEPSEEK_API_KEY: return None
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.deepseek.com/v1/chat/completions',
                                    headers={'Authorization':f'Bearer {DEEPSEEK_API_KEY}','Content-Type':'application/json'},
                                    json={'model':'deepseek-chat','messages':[{'role':'system','content':system_prompt},{'role':'user','content':question}], 'max_tokens':400,'temperature':0.5},
                                    timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status==200:
                    data = await resp.json()
                    return data['choices'][0]['message']['content'].strip()
        return None

    async def _ask_groq(self, question, system_prompt):
        if not GROQ_API_KEY: return None
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.groq.com/openai/v1/chat/completions',
                                    headers={'Authorization':f'Bearer {GROQ_API_KEY}','Content-Type':'application/json'},
                                    json={'model':'llama-3.3-70b-versatile','messages':[{'role':'system','content':system_prompt},{'role':'user','content':question}], 'max_tokens':400,'temperature':0.5},
                                    timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status==200:
                    data = await resp.json()
                    return data['choices'][0]['message']['content'].strip()
        return None

    async def _ask_openai(self, question, system_prompt):
        if not OPENAI_API_KEY: return None
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.openai.com/v1/chat/completions',
                                    headers={'Authorization':f'Bearer {OPENAI_API_KEY}','Content-Type':'application/json'},
                                    json={'model':'gpt-4o-mini','messages':[{'role':'system','content':system_prompt},{'role':'user','content':question}], 'max_tokens':400,'temperature':0.5},
                                    timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status==200:
                    data = await resp.json()
                    return data['choices'][0]['message']['content'].strip()
        return None

    async def _ask_anthropic(self, question, system_prompt):
        if not ANTHROPIC_API_KEY: return None
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.anthropic.com/v1/messages',
                                    headers={'x-api-key':ANTHROPIC_API_KEY,'Content-Type':'application/json'},
                                    json={'model':'claude-3-haiku-20240307','system':system_prompt,'messages':[{'role':'user','content':question}], 'max_tokens':400},
                                    timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status==200:
                    data = await resp.json()
                    # adapt to Claude response format
                    if isinstance(data, dict):
                        return data.get('content', [{'type':'output_text','text':''}])[0].get('text','').strip()
        return None

    async def _ask_google(self, question, system_prompt):
        if not GOOGLE_API_KEY: return None
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}',
                                    headers={'Content-Type':'application/json'},
                                    json={'contents':[{'parts':[{'text':f"{system_prompt}\n\nسؤال: {question}"}]}],'generationConfig':{'maxOutputTokens':400,'temperature':0.5}},
                                    timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status==200:
                    data = await resp.json()
                    return data['candidates'][0]['content']['parts'][0]['text'].strip()
        return None

# -------------------------
# Context Manager
# -------------------------
class ContextManager:
    def __init__(self, timeout_minutes:int=5):
        self.contexts = {}
        self.timeout = timedelta(minutes=timeout_minutes)
    def set_context(self, user_id:int, item_name:str, item_data:dict=None):
        self.contexts[user_id] = {'item':item_name,'data':item_data,'timestamp':datetime.now()}
    def get_context(self, user_id:int):
        c = self.contexts.get(user_id)
        if not c: return None
        if datetime.now() - c['timestamp'] > self.timeout:
            del self.contexts[user_id]
            return None
        return c
    def clear_context(self, user_id:int):
        if user_id in self.contexts: del self.contexts[user_id]
    def inject_context(self, user_id:int, question:str) -> str:
        ctx = self.get_context(user_id)
        if not ctx: return question
        follow_up_keywords = ['وين','where','نسبة','spawn','location','كم','how','طريقة','كيف','استراتيجية']
        ql = question.lower()
        is_follow = any(k in ql for k in follow_up_keywords)
        if is_follow and len(question.split())<=5:
            return f"{ctx['item']} {question}"
        return question

# -------------------------
# Anti-Spam
# -------------------------
class AntiSpam:
    def __init__(self, max_messages:int=3, window_seconds:int=60):
        self.user_messages = {}
        self.max_messages = max_messages
        self.window = timedelta(seconds=window_seconds)
    def check(self, user_id:int):
        now = datetime.now()
        lst = self.user_messages.get(user_id, [])
        lst = [ts for ts in lst if now - ts < self.window]
        if len(lst) >= self.max_messages:
            oldest = min(lst)
            wait_time = int((oldest + self.window - now).total_seconds())
            return False, wait_time
        lst.append(now)
        self.user_messages[user_id] = lst
        return True, 0

# -------------------------
# Embed Builder & Utilities
# -------------------------
class EmbedBuilder:
    @staticmethod
    def clean_description(text:str) -> str:
        if not text: return text
        return text.replace('запасная','احتياطية')

    @staticmethod
    def extract_field(item:dict, field:str) -> Optional[str]:
        v = item.get(field)
        if not v: return None
        if isinstance(v, dict):
            return v.get('en') or v.get('ar') or next(iter(v.values()), None)
        return str(v)

    @staticmethod
    def get_image_url(item:dict) -> Optional[str]:
        img = item.get('image') or item.get('icon') or item.get('imageUrl')
        if img and isinstance(img, str) and img.startswith('http'):
            return img
        filename = item.get('imageFilename')
        if filename and isinstance(filename, str):
            if filename.startswith('http'):
                return filename
            if filename.startswith('/'):
                filename = filename.lstrip('/')
            return f"{IMAGES_BASE_URL}/{filename}"
        item_id = item.get('id') or item.get('slug') or item.get('itemId')
        if item_id:
            itype = item.get('type') or item.get('category') or ''
            if isinstance(itype, dict):
                itype = itype.get('en','')
            itype = str(itype).lower()
            if 'bot' in itype or 'enemy' in itype:
                folder='bots'
            elif 'map' in itype:
                folder='maps'
            elif 'trader' in itype:
                folder='traders'
            else:
                folder='items'
            return f"{IMAGES_BASE_URL}/{folder}/{item_id}.png"
        return None

    @staticmethod
    def item_embed(item:dict, translated_desc:Optional[str]=None) -> discord.Embed:
        name = EmbedBuilder.extract_field(item, 'name') or item.get('id') or 'غير معروف'
        if translated_desc:
            desc = translated_desc
        else:
            d = item.get('description')
            if isinstance(d, dict):
                desc = d.get('ar') or d.get('en') or next(iter(d.values()), '')
            else:
                desc = d or 'لا يوجد وصف'
        desc = EmbedBuilder.clean_description(desc)[:800]
        embed = discord.Embed(title=f"📦 {name}", description=desc, color=COLORS['primary'], timestamp=datetime.now())
        # fields
        category = EmbedBuilder.extract_field(item, 'category')
        if category: embed.add_field(name="📁 الفئة", value=category, inline=True)
        itype = EmbedBuilder.extract_field(item, 'type')
        if itype: embed.add_field(name="🏷️ النوع", value=itype, inline=True)
        rarity = EmbedBuilder.extract_field(item, 'rarity')
        if rarity:
            rar_map={'common':'عادي ⚪','uncommon':'غير شائع 🟢','rare':'نادر 🔵','epic':'ملحمي 🟣','legendary':'أسطوري 🟡'}
            embed.add_field(name="💎 الندرة", value=rar_map.get(rarity.lower(), rarity), inline=True)
        found_in = EmbedBuilder.extract_field(item, 'location') or item.get('foundIn')
        if found_in: embed.add_field(name="📍 الموقع", value=str(found_in), inline=False)
        price = item.get('price') or item.get('value')
        if price: embed.add_field(name="💰 السعر", value=str(price), inline=True)
        spawn = item.get('spawnRate') or item.get('spawn_rate')
        if spawn: embed.add_field(name="📊 نسبة الظهور", value=str(spawn), inline=True)
        # obtain field
        obtain_lines=[]
        if item.get('foundIn'): obtain_lines.append(f"- يوجد في: {item.get('foundIn')}")
        if item.get('craftBench'): obtain_lines.append(f"- يتصنع في: {item.get('craftBench')}")
        recipe = item.get('recipe')
        if isinstance(recipe, dict) and recipe: obtain_lines.append("- له وصفة تصنيع، شوف التفاصيل")
        drops = item.get('drops')
        if isinstance(drops, list) and drops: obtain_lines.append(f"- يسقط من: {len(drops)} مصدر/مصادر")
        traders = item.get('traders') or item.get('soldBy')
        if traders: obtain_lines.append("- متوفر لدى التجار")
        if obtain_lines:
            embed.add_field(name="طرق الحصول", value="\n".join(obtain_lines), inline=False)
        url = EmbedBuilder.get_image_url(item)
        if url: embed.set_thumbnail(url=url)
        embed.set_footer(text=f"🤖 {BOT_NAME} | ARC Raiders")
        return embed

    @staticmethod
    def map_embed(map_name:str, map_data:dict=None) -> discord.Embed:
        embed = discord.Embed(title=f"🗺️ خريطة: {map_name}", color=COLORS['info'], timestamp=datetime.now())
        map_id = map_data.get('id') if map_data else map_name.lower().replace(' ','_')
        map_url = f"{IMAGES_BASE_URL}/maps/{map_id}.png"
        embed.set_image(url=map_url)
        if map_data and map_data.get('description'):
            desc = map_data['description']
            if isinstance(desc, dict):
                desc = desc.get('en','')
            embed.description = desc[:500]
        embed.set_footer(text=f"🤖 {BOT_NAME} | ARC Raiders")
        return embed

    @staticmethod
    def stats_embed(db_stats:dict, ai_stats:dict, uptime:str) -> discord.Embed:
        embed = discord.Embed(title="📊 إحصائيات دليل", color=COLORS['info'], timestamp=datetime.now())
        db_text = (f"📦 العناصر: **{db_stats.get('items',0):,}**\n📚 المجموع: **{db_stats.get('total',0):,}**")
        embed.add_field(name="🗄️ قاعدة البيانات", value=db_text, inline=True)
        ai_text = "\n".join([f"{k}: {v}" for k,v in ai_stats.items()])
        embed.add_field(name="🤖 استخدام AI", value=ai_text, inline=True)
        embed.add_field(name="⏱️ وقت التشغيل", value=uptime, inline=False)
        embed.set_footer(text=f"🤖 {BOT_NAME} v{BOT_VERSION}")
        return embed

# -------------------------
# Feedback view (buttons)
# -------------------------
class FeedbackView(discord.ui.View):
    def __init__(self, author_id:int, source_question:str, embed_title:str):
        super().__init__(timeout=600)
        self.author_id = author_id
        self.source_question = source_question
        self.embed_title = embed_title or ""

    async def _send_log(self, interaction: discord.Interaction, status: str):
        try:
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(f"📝 تقييم: {status}\n👤 المرسل: <@{interaction.user.id}>\n📦 العنوان: {self.embed_title}\n🗨️ السؤال: {self.source_question}")
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

# -------------------------
# Bot class
# -------------------------
class DaleelBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents, help_command=None)
        self.database = DatabaseManager()
        self.search_engine: Optional[SearchEngine] = None
        self.ai_manager = AIManager()
        self.context_manager = ContextManager()
        self.anti_spam = AntiSpam()
        self.start_time: Optional[datetime] = None
        self.questions_answered = 0

    async def setup_hook(self):
        loaded = self.database.load_all()
        self.search_engine = SearchEngine(self.database)
        # sync only for the allowed guild to speed up
        try:
            await self.tree.sync(guild=discord.Object(id=ALLOWED_GUILD_ID))
            logger.info("✅ Tree synced")
        except Exception as e:
            logger.warning(f"Sync warning: {e}")

    async def on_ready(self):
        self.start_time = datetime.now()
        logger.info(f"✅ Bot ready: {self.user} ({self.user.id}) — data: {len(self.database.all_data)} items")
        await self.send_startup_message()
        try:
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="أسئلتكم عن ARC Raiders"))
        except Exception:
            pass

    async def send_startup_message(self):
        try:
            ch = self.get_channel(LOG_CHANNEL_ID)
            if ch:
                embed = discord.Embed(title="🚀 البوت شغال!", description=f"✅ **{BOT_NAME}** جاهز\n📊 العناصر: {len(self.database.all_data):,}", color=COLORS['success'], timestamp=datetime.now())
                await ch.send(embed=embed)
        except Exception as e:
            logger.warning(f"Startup message failed: {e}")

    def get_uptime(self) -> str:
        if not self.start_time:
            return "غير معروف"
        delta = datetime.now() - self.start_time
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        return f"{h} ساعة, {m} دقيقة, {s} ثانية"

# instantiate bot
bot = DaleelBot()

# -------------------------
# Views for details/disambiguation
# -------------------------
class DetailsView(discord.ui.View):
    def __init__(self, embed: discord.Embed, timeout:int=120):
        super().__init__(timeout=timeout)
        self.embed = embed
    @discord.ui.button(label="عرض التفاصيل", style=discord.ButtonStyle.primary)
    async def show(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=self.embed)

class DisambButton(discord.ui.Button):
    def __init__(self, label:str, payload):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.payload = payload
    async def callback(self, interaction: discord.Interaction):
        source, item, score = self.payload
        short = build_short_answer(source, item)
        embed = EmbedBuilder.item_embed(item, None)
        view = DetailsView(embed)
        await interaction.response.send_message(content=short, embed=None, view=view)

class DisambiguationView(discord.ui.View):
    def __init__(self, options:List[Tuple[str, dict, float]], timeout:int=60):
        super().__init__(timeout=timeout)
        for source, item, score in options[:5]:
            label = bot.search_engine.extract_name(item)
            self.add_item(DisambButton(label=label, payload=(source,item,score)))

# -------------------------
# Short answer builder (used in many places)
# -------------------------
def build_short_answer(source:str, item:dict) -> str:
    name = bot.search_engine.extract_name(item) if bot.search_engine else (item.get('id') or 'معلومة')
    found = item.get('foundIn') or item.get('maps') or item.get('location')
    price = item.get('value') or item.get('price') or item.get('cost')
    parts = [f"**{name}**"]
    if found:
        if isinstance(found, (list,tuple)): parts.append(f"تحصل عليه في: {', '.join(str(x) for x in found[:3])}")
        else: parts.append(f"تحصل عليه في: {found}")
    if price:
        parts.append(f"السعر: {price}")
    # keep concise
    return " · ".join(parts)

# -------------------------
# Interaction / Message helpers
# -------------------------
async def _respond(ctx_or_inter, **kwargs):
    if isinstance(ctx_or_inter, commands.Context):
        return await ctx_or_inter.send(**kwargs)
    elif isinstance(ctx_or_inter, discord.Interaction):
        try:
            if ctx_or_inter.response.is_done():
                return await ctx_or_inter.followup.send(**kwargs)
            else:
                return await ctx_or_inter.response.send_message(**kwargs)
        except Exception:
            return await ctx_or_inter.followup.send(**kwargs)
    else:
        raise TypeError("Unsupported context")

# -------------------------
# Commands: help / stats / search
# -------------------------
@bot.tree.command(name="help", description="عرض المساعدة")
async def help_command(interaction: discord.Interaction):
    if interaction.channel and interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("استخدم قناة الأسئلة المخصصة فقط.", ephemeral=True)
        return
    embed = discord.Embed(title="📖 مساعدة دليل", description="أنا **دليل** — اسألني عن ARC Raiders", color=COLORS['info'])
    embed.add_field(name="أمثلة", value="• `وين أحصل Rusted Gear؟`\n• `كيف أهزم Queen؟`", inline=False)
    embed.set_footer(text=f"🤖 {BOT_NAME} v{BOT_VERSION}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stats", description="عرض إحصائيات البوت")
async def stats_command(interaction: discord.Interaction):
    if interaction.channel and interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("استخدم قناة الأسئلة المخصصة فقط.", ephemeral=True)
        return
    embed = EmbedBuilder.stats_embed(bot.database.get_stats(), bot.ai_manager.usage_stats, bot.get_uptime())
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
        embed = discord.Embed(title="لا نتائج", description=f"ما لقيت نتائج لـ **{query}**", color=COLORS['warning'])
        await interaction.followup.send(embed=embed)
        return
    embed = discord.Embed(title=f"🔍 نتائج البحث: {query}", color=COLORS['info'])
    for i,r in enumerate(results,1):
        item = r['item']
        name = bot.search_engine.extract_name(item)
        score = int(r['score']*100)
        cat = EmbedBuilder.extract_field(item,'category') or EmbedBuilder.extract_field(item,'type') or 'غير محدد'
        embed.add_field(name=f"{i}. {name}", value=f"📁 {cat} | 🎯 تطابق: {score}%", inline=False)
    await interaction.followup.send(embed=embed)

# prefix text command for backwards compatibility
@commands.command(name="سأل")
async def ask_prefix(ctx: commands.Context, *, query: str):
    await handle_message_query(ctx, query)

bot.add_command(ask_prefix)

# -------------------------
# Core message handling (refactored)
# -------------------------
async def handle_message_query(ctx_or_inter, raw_query: str, message_obj: discord.Message = None):
    """
    Common handler for queries (from message or interaction).
    Returns after sending short answer + view (details button).
    """
    # for usage detection
    is_interaction = isinstance(ctx_or_inter, discord.Interaction)
    # sanitize
    query = raw_query.strip()
    if not query:
        await _respond(ctx_or_inter, content="اكتب السؤال أو اسم العنصر.")
        return

    # anti-spam for messages (Context only)
    if isinstance(ctx_or_inter, commands.Context):
        allowed, wait = bot.anti_spam.check(ctx_or_inter.author.id)
        if not allowed:
            await ctx_or_inter.send(embed=discord.Embed(title="⚠️ انتظر قل��لاً", description=f"⏰ انتظر {wait} ثانية", color=COLORS['warning']), delete_after=10)
            return

    # inject context if present (only for messages)
    if isinstance(ctx_or_inter, commands.Context):
        query = bot.context_manager.inject_context(ctx_or_inter.author.id, query)

    # detect question type for threshold tuning
    ql = query.lower()
    is_crafting = any(k in ql for k in ['تصنيع','مكونات','recipe','craft'])
    is_location = any(k in ql for k in ['وين','اين','أين','مكان','where','location','احصل'])
    is_obtain = any(k in ql for k in ['كيف احصل','كيف اجيب','drop','drops','يطيح','يسقط','get'])

    match_threshold = 0.70
    if is_crafting or is_location or is_obtain:
        match_threshold = 0.35

    # attempt local search first
    results = bot.search_engine.search(query, limit=5 if (is_crafting or is_obtain or is_location) else 1)

    # if best result passes threshold, send short + details-button embed
    if results and results[0]['score'] >= match_threshold:
        result = results[0]
        item = result['item']
        short = build_short_answer(result.get('item_source','local') if 'item_source' in result else 'local', item)
        embed = EmbedBuilder.item_embed(item, None)
        # include extra custom details for obtain questions
        if is_obtain or is_location:
            obtain_info = []
            found_in = item.get('foundIn')
            if found_in: obtain_info.append(f"📍 المنطقة: {found_in}")
            loc = item.get('location') or item.get('map')
            if loc:
                if isinstance(loc, dict): loc = loc.get('en') or loc.get('ar') or next(iter(loc.values()))
                obtain_info.append(f"🗺️ الموقع: {loc}")
            spawn_rate = item.get('spawnRate') or item.get('spawn_rate')
            if spawn_rate: obtain_info.append(f"📊 نسبة الظهور: {spawn_rate}%")
            price = item.get('price') or item.get('value')
            if price: obtain_info.append(f"💰 السعر: {price}")
            if obtain_info:
                embed.add_field(name="ملاحظات الحصول", value="\n".join(obtain_info), inline=False)

        # reply: short answer + button to show embed (or send embed directly in ephemeral for interactions)
        view = DetailsView(embed)
        # use feedback view with reply (for messages)
        if isinstance(ctx_or_inter, commands.Context):
            reply = await reply_with_feedback(ctx_or_inter.message, embed)
            # also send short answer as follow-up message for clarity
            await ctx_or_inter.send(content=short, view=view)
        else:
            # interaction
            await ctx_or_inter.response.send_message(content=short, embed=None, view=view)
        # set context for follow-ups
        name = bot.search_engine.extract_name(item)
        if isinstance(ctx_or_inter, commands.Context):
            user_id = ctx_or_inter.author.id
        else:
            user_id = ctx_or_inter.user.id
        bot.context_manager.set_context(user_id, name, item)
        bot.questions_answered += 1
        return

    # if no strong match, but moderate matches exist, offer disambiguation buttons
    top = bot.search_engine.search(query, limit=5)
    top_filtered = [ (r['item'].get('id') if 'id' in r['item'] else 'local', r['item'], r['score']) for r in top if r['score']>=0.40 ]
    if top_filtered:
        view = DisambiguationView(top_filtered)
        msg = "ما لقيت تطابق قوي، بس هذي اقتراحات ممكن تقصد واحد منها — اضغط على الخيار:"
        await _respond(ctx_or_inter, content=msg, view=view)
        return

    # fallback to AI if configured and allowed
    ai_enabled = any([DEEPSEEK_API_KEY,GROQ_API_KEY,OPENAI_API_KEY,ANTHROPIC_API_KEY,GOOGLE_API_KEY])
    # decide if AI should answer based on intent keywords (simple)
    use_ai = any(tok in ql for tok in ['أفضل','أقوى','استراتيجية','لماذا','ليش','كيف','explain','vs','مقارنة','بديل','alternative'])
    if use_ai and ai_enabled:
        # craft safe context
        user_ctx = None
        if isinstance(ctx_or_inter, commands.Context):
            user_ctx = bot.context_manager.get_context(ctx_or_inter.author.id)
        else:
            user_ctx = bot.context_manager.get_context(ctx_or_inter.user.id)
        context = f"المستخدم كان يسأل عن: {user_ctx['item']}" if user_ctx else ""
        thinking = None
        if isinstance(ctx_or_inter, commands.Context):
            thinking = await ctx_or_inter.send("🔍 أبحث لك...")
        else:
            await ctx_or_inter.response.defer()
        ai_res = await bot.ai_manager.ask_ai(query, context)
        if thinking:
            try: await thinking.delete()
            except: pass
        if ai_res['success']:
            embed = discord.Embed(title="🤖 إجابة مختصرة", description=ai_res['answer'][:700], color=COLORS['info'], timestamp=datetime.now())
            embed.set_footer(text=f"via {ai_res['provider']} • {BOT_NAME}")
            if isinstance(ctx_or_inter, commands.Context):
                await reply_with_feedback(ctx_or_inter.message, embed)
            else:
                await ctx_or_inter.followup.send(embed=embed)
            return
        # else fallthrough to not found
    # final: not found in data or AI
    await _respond(ctx_or_inter, content="ما لقيت شيء واضح في الداتا. جرّب تكتب اسم العنصر بالكامل أو تغير صياغة السؤال.")

# Helper wrapper for message event
@bot.event
async def on_message(message: discord.Message):
    try:
        if message.author.bot:
            return
        # guild filter
        if message.guild and message.guild.id != ALLOWED_GUILD_ID:
            return
        # channel filter: if not allowed channel, still process commands
        if message.channel.id != ALLOWED_CHANNEL_ID:
            await bot.process_commands(message)
            return
        content = message.content.strip()
        if not content or len(content) < 3:
            return
        # ignore greetings
        if content.lower() in ['hi','hello','مرحبا','السلام','هاي','هلا']:
            return
        # quick replies
        quick = {'شكراً':'العفو! 💚','thanks':"You're welcome!"}
        if content in quick:
            await message.reply(quick[content])
            return
        # process user message
        # remove prefix "دليل" if present
        if content.lower().startswith('دليل'):
            content = content[5:].strip()
            if not content: return
        # pass to handler
        await handle_message_query(message, content, message_obj=message)
    except Exception as e:
        logger.exception("خطأ في on_message: %s", e)
        try:
            await message.reply(embed=EmbedBuilder.error("خطأ غير متوقع","حصل خطأ داخل البوت."))
        except Exception:
            pass

# Slash command handler calls same logic
@bot.tree.command(name="سأل", description="اسأل عن عنصر أو عن طريقة الحصول عليه")
@app_commands.describe(query="اكتب اسم العنصر أو السؤال")
async def ask_slash(interaction: discord.Interaction, query: str):
    await handle_message_query(interaction, query)

# Admin commands
@commands.is_owner()
@commands.command(name="reload_data")
async def reload_data(ctx: commands.Context):
    bot.database = DatabaseManager()
    loaded = bot.database.load_all()
    bot.search_engine = SearchEngine(bot.database)
    await ctx.send("✅ تم إعادة تحميل البيانات.")

@commands.check(lambda ctx: ctx.author.id == OWNER_ID)
@commands.command(name="اعد_تحميل_البيانات")
async def reload_data_ar(ctx: commands.Context):
    bot.database = DatabaseManager()
    bot.database.load_all()
    bot.search_engine = SearchEngine(bot.database)
    await ctx.send("✅ تم إعادة تحميل البيانات بنجاح")

# Reaction handling for manual feedback logs
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot: return
    if reaction.message.author != bot.user: return
    emoji = str(reaction.emoji)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if emoji in ['❌','✅'] and log_channel:
        try:
            embed = discord.Embed(title=f"تقييم: {'خاطئ' if emoji=='❌' else 'صحيح'}", color=COLORS['error'] if emoji=='❌' else COLORS['success'], timestamp=datetime.now())
            original = reaction.message.embeds[0] if reaction.message.embeds else None
            if original:
                embed.add_field(name="الرد", value=(original.title or '') + "\n" + (original.description[:300] if original.description else ''), inline=False)
            await log_channel.send(embed=embed)
        except Exception:
            pass

# -------------------------
# Run
# -------------------------
def main():
    if not DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN غير موجود. ضع التوكن في ملف .env أو متغير بيئة.")
        return
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.exception("فشل تشغيل البوت: %s", e)

if __name__ == "__main__":
    main()
