"""
╔══════════════════════════════════════════════════════════════════╗
║                    🎮 بوت دليل - ARC Raiders                      ║
║                 بوت ذكي للإجابة على أسئلة اللعبة                   ║
║                     صنع بـ ❤️ لسيرفر ELITE-ZONE                   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

# ══════════════════════════════════════════════════════════════════
#                         إعدادات البوت
# ══════════════════════════════════════════════════════════════════

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# إعدادات الأمان
ALLOWED_GUILD_ID = int(os.getenv('ALLOWED_GUILD_ID', '0'))
ALLOWED_CHANNEL_ID = int(os.getenv('ALLOWED_CHANNEL_ID', '0'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '0'))
OWNER_ID = int(os.getenv('OWNER_ID', '0'))

# API Keys
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

# أسماء البوت للتعرف عليها
BOT_NAMES = [
    'دليل', 'دلييل', 'دليييل', 'daleel', 'guide',
    'يا دليل', 'يادليل', 'هاي دليل', 'مرحبا دليل',
    'دليل؟', 'دليل!', 'دليل،', 'دليل.',
]

# Rate Limiting
user_cooldowns: Dict[int, List[datetime]] = defaultdict(list)
RATE_LIMIT = 5  # أسئلة
RATE_WINDOW = 60  # ثانية

# ══════════════════════════════════════════════════════════════════
#                         تحميل البيانات
# ══════════════════════════════════════════════════════════════════

DATA_PATH = Path("arcraiders-data")

def load_json(filename: str) -> list:
    """تحميل ملف JSON"""
    filepath = DATA_PATH / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_items() -> dict:
    """تحميل جميع الـ items"""
    items = {}
    items_path = DATA_PATH / "items"
    if items_path.exists():
        for file in items_path.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    item_data = json.load(f)
                    if 'id' in item_data:
                        items[item_data['id']] = item_data
            except Exception as e:
                print(f"⚠️ خطأ في قراءة {file.name}: {e}")
    return items

def load_quests() -> list:
    """تحميل المهام"""
    quests = []
    quests_path = DATA_PATH / "quests"
    if quests_path.exists():
        for file in quests_path.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    quest_data = json.load(f)
                    quests.append(quest_data)
            except Exception as e:
                print(f"⚠️ خطأ في قراءة {file.name}: {e}")
    return quests

# تحميل البيانات
print("📦 جاري تحميل البيانات...")
ITEMS = load_items()
BOTS = load_json("bots.json")
MAPS = load_json("maps.json")
QUESTS = load_quests()

print(f"✅ تم تحميل {len(ITEMS)} قطعة")
print(f"✅ تم تحميل {len(BOTS)} ARC")
print(f"✅ تم تحميل {len(MAPS)} خريطة")
print(f"✅ تم تحميل {len(QUESTS)} مهمة")

# ══════════════════════════════════════════════════════════════════
#                         دوال مساعدة
# ══════════════════════════════════════════════════════════════════

def normalize_text(text: str) -> str:
    """تطبيع النص العربي والإنجليزي"""
    # إزالة التشكيل العربي
    arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670]')
    text = arabic_diacritics.sub('', text)
    # تحويل للصغير وإزالة المسافات الزائدة
    text = text.lower().strip()
    # إزالة علامات الترقيم
    text = re.sub(r'[؟?!.,،؛:]+', '', text)
    return text

def check_rate_limit(user_id: int) -> Tuple[bool, int]:
    """التحقق من Rate Limit"""
    now = datetime.now()
    # تنظيف القديم
    user_cooldowns[user_id] = [
        t for t in user_cooldowns[user_id] 
        if now - t < timedelta(seconds=RATE_WINDOW)
    ]
    
    if len(user_cooldowns[user_id]) >= RATE_LIMIT:
        oldest = min(user_cooldowns[user_id])
        wait_time = RATE_WINDOW - (now - oldest).seconds
        return False, wait_time
    
    user_cooldowns[user_id].append(now)
    return True, 0

def is_bot_mentioned(message: discord.Message) -> bool:
    """التحقق إذا البوت مذكور"""
    content = normalize_text(message.content)
    
    # تحقق من المنشن المباشر
    if bot.user in message.mentions:
        return True
    
    # تحقق من الاسم
    for name in BOT_NAMES:
        if name in content:
            return True
    
    return False

def extract_question(content: str) -> str:
    """استخراج السؤال من الرسالة"""
    # إزالة المنشن
    content = re.sub(r'<@!?\d+>', '', content)
    # إزالة اسم البوت
    for name in BOT_NAMES:
        content = re.sub(rf'\b{name}\b', '', content, flags=re.IGNORECASE)
    return content.strip()

# ══════════════════════════════════════════════════════════════════
#                    نظام البحث (3 مستويات)
# ══════════════════════════════════════════════════════════════════

def search_items(query: str, limit: int = 5) -> List[dict]:
    """البحث في القطع"""
    query = normalize_text(query)
    results = []
    
    for item_id, item in ITEMS.items():
        score = 0
        name_en = item.get('name', {}).get('en', '').lower()
        
        # تطابق تام
        if query == name_en or query == item_id.lower():
            score = 100
        # يبدأ بالكلمة
        elif name_en.startswith(query) or item_id.lower().startswith(query):
            score = 80
        # يحتوي على الكلمة
        elif query in name_en or query in item_id.lower():
            score = 60
        # في الوصف
        elif 'description' in item:
            desc = item['description'].get('en', '').lower()
            if query in desc:
                score = 40
        
        if score > 0:
            results.append((score, item))
    
    # ترتيب حسب النتيجة
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:limit]]

def search_arcs(query: str) -> List[dict]:
    """البحث في ARCs"""
    query = normalize_text(query)
    results = []
    
    for arc in BOTS:
        name = arc.get('name', '').lower()
        arc_id = arc.get('id', '').lower()
        
        if query in name or query in arc_id:
            results.append(arc)
    
    return results

def search_maps(query: str) -> List[dict]:
    """البحث في الخرائط"""
    query = normalize_text(query)
    results = []
    
    for map_data in MAPS:
        name = map_data.get('name', {}).get('en', '').lower()
        map_id = map_data.get('id', '').lower()
        
        if query in name or query in map_id:
            results.append(map_data)
    
    return results

def search_all(query: str) -> Dict[str, list]:
    """بحث شامل في كل البيانات"""
    return {
        'items': search_items(query, limit=3),
        'arcs': search_arcs(query),
        'maps': search_maps(query)
    }

# ══════════════════════════════════════════════════════════════════
#                         AI Integration
# ══════════════════════════════════════════════════════════════════

async def ask_ai(question: str, context: str = "") -> str:
    """سؤال الذكاء الاصطناعي"""
    
    system_prompt = """أنت "دليل" - بوت مساعد عربي للعبة ARC Raiders.
    
مهمتك:
- الإجابة على أسئلة اللاعبين عن اللعبة
- تقديم معلومات دقيقة ومفيدة
- الرد بشكل مختصر وواضح (3-5 جمل)
- استخدام العربية الفصحى المبسطة

قواعد مهمة:
- لا تخترع معلومات غير موجودة
- إذا ما تعرف، قول "ما عندي معلومة عن هذا"
- كن ودود ومساعد
- لا تستخدم إيموجي كثير"""

    user_prompt = f"""السؤال: {question}

{f'معلومات متاحة: {context}' if context else ''}

أجب بشكل مختصر ومفيد:"""

    # محاولة DeepSeek أولاً (أرخص)
    if DEEPSEEK_API_KEY:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"⚠️ DeepSeek Error: {e}")
    
    # محاولة Groq (سريع)
    if GROQ_API_KEY:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-70b-versatile",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"⚠️ Groq Error: {e}")
    
    # محاولة Claude (الأقوى)
    if ANTHROPIC_API_KEY:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 500,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": user_prompt}
                        ]
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data['content'][0]['text']
        except Exception as e:
            print(f"⚠️ Claude Error: {e}")
    
    return None

# ══════════════════════════════════════════════════════════════════
#                    معالجة الأسئلة الذكية
# ══════════════════════════════════════════════════════════════════

async def process_question(question: str) -> Tuple[str, discord.Embed]:
    """معالجة السؤال وإرجاع الجواب"""
    
    query = normalize_text(question)
    
    # ══════════════════════════════════════
    # المستوى 1: البحث في Database
    # ══════════════════════════════════════
    
    results = search_all(query)
    
    # إذا وجدنا items
    if results['items']:
        item = results['items'][0]
        embed = create_item_embed(item)
        return "📦 لقيت لك المعلومات:", embed
    
    # إذا وجدنا ARCs
    if results['arcs']:
        arc = results['arcs'][0]
        embed = create_arc_embed(arc)
        return "🤖 هذا الـ ARC اللي تسأل عنه:", embed
    
    # إذا وجدنا خرائط
    if results['maps']:
        map_data = results['maps'][0]
        embed = create_map_embed(map_data)
        return "🗺️ معلومات الخريطة:", embed
    
    # ══════════════════════════════════════
    # المستوى 2: سؤال AI
    # ══════════════════════════════════════
    
    # تجهيز سياق من البيانات المتاحة
    context_parts = []
    if ITEMS:
        sample_items = list(ITEMS.keys())[:20]
        context_parts.append(f"Items متاحة: {', '.join(sample_items)}")
    if BOTS:
        arc_names = [b['name'] for b in BOTS[:10]]
        context_parts.append(f"ARCs: {', '.join(arc_names)}")
    
    context = "\n".join(context_parts)
    
    ai_response = await ask_ai(question, context)
    
    if ai_response:
        embed = discord.Embed(
            title="💬 رد دليل",
            description=ai_response,
            color=discord.Color.blue()
        )
        embed.set_footer(text="🤖 تم الرد بواسطة الذكاء الاصطناعي")
        return "", embed
    
    # ══════════════════════════════════════
    # المستوى 3: ما لقينا شي
    # ══════════════════════════════════════
    
    embed = discord.Embed(
        title="🤔 ما فهمت السؤال",
        description=(
            f"ما لقيت معلومات عن: **{question}**\n\n"
            "جرب تسألني عن:\n"
            "• اسم قطعة معينة (مثل: Rusted Gear)\n"
            "• اسم ARC (مثل: Hunter)\n"
            "• اسم خريطة (مثل: Dam)"
        ),
        color=discord.Color.orange()
    )
    return "", embed

# ══════════════════════════════════════════════════════════════════
#                         Embeds
# ══════════════════════════════════════════════════════════════════

def create_item_embed(item: dict) -> discord.Embed:
    """إنشاء Embed للقطعة"""
    
    rarity_colors = {
        'Common': discord.Color.light_grey(),
        'Uncommon': discord.Color.green(),
        'Rare': discord.Color.blue(),
        'Epic': discord.Color.purple(),
        'Legendary': discord.Color.gold()
    }
    
    rarity = item.get('rarity', 'Common')
    color = rarity_colors.get(rarity, discord.Color.blue())
    
    embed = discord.Embed(
        title=f"📦 {item['name']['en']}",
        color=color
    )
    
    if 'description' in item:
        desc = item['description'].get('en', '')[:300]
        embed.description = desc
    
    # معلومات أساسية
    info_parts = []
    if 'type' in item:
        info_parts.append(f"**النوع:** {item['type']}")
    if 'rarity' in item:
        rarity_emoji = {'Common': '⚪', 'Uncommon': '🟢', 'Rare': '🔵', 'Epic': '🟣', 'Legendary': '🟠'}
        emoji = rarity_emoji.get(rarity, '⚪')
        info_parts.append(f"**الندرة:** {emoji} {rarity}")
    
    if info_parts:
        embed.add_field(name="📋 المعلومات", value="\n".join(info_parts), inline=False)
    
    # إحصائيات
    stats_parts = []
    if 'value' in item:
        stats_parts.append(f"💰 القيمة: {item['value']}")
    if 'weightKg' in item:
        stats_parts.append(f"⚖️ الوزن: {item['weightKg']} kg")
    
    if stats_parts:
        embed.add_field(name="📊 الإحصائيات", value=" | ".join(stats_parts), inline=False)
    
    # وصفة الصناعة
    if 'recipe' in item and item['recipe']:
        recipe_text = "\n".join([f"• {r['itemId']}: x{r['quantity']}" for r in item['recipe'][:5]])
        if len(item['recipe']) > 5:
            recipe_text += f"\n... و{len(item['recipe']) - 5} مواد أخرى"
        embed.add_field(name="🔧 الصناعة", value=recipe_text, inline=False)
    
    embed.set_footer(text=f"ID: {item['id']}")
    return embed

def create_arc_embed(arc: dict) -> discord.Embed:
    """إنشاء Embed للـ ARC"""
    
    threat_colors = {
        'Low': discord.Color.green(),
        'Moderate': discord.Color.gold(),
        'High': discord.Color.orange(),
        'Critical': discord.Color.red(),
        'Extreme': discord.Color.dark_red()
    }
    
    threat = arc.get('threat', 'Moderate')
    color = threat_colors.get(threat, discord.Color.blue())
    
    embed = discord.Embed(
        title=f"🤖 {arc['name']}",
        description=arc.get('description', '')[:400],
        color=color
    )
    
    # معلومات أساسية
    embed.add_field(name="📋 النوع", value=arc.get('type', 'غير محدد'), inline=True)
    embed.add_field(name="⚠️ التهديد", value=threat, inline=True)
    
    # نقطة الضعف
    if 'weakness' in arc:
        embed.add_field(name="🎯 نقطة الضعف", value=arc['weakness'], inline=False)
    
    # XP
    xp_text = f"تدمير: {arc.get('destroyXp', 0)} | نهب: {arc.get('lootXp', 0)}"
    embed.add_field(name="💰 XP", value=xp_text, inline=False)
    
    # الخرائط
    if 'maps' in arc and arc['maps']:
        maps_text = ", ".join(arc['maps'][:5])
        embed.add_field(name="🗺️ يظهر في", value=maps_text, inline=False)
    
    # المسروقات
    if 'drops' in arc and arc['drops']:
        drops_text = ", ".join(arc['drops'][:8])
        if len(arc['drops']) > 8:
            drops_text += f" +{len(arc['drops']) - 8}"
        embed.add_field(name="🎁 الغنائم", value=drops_text, inline=False)
    
    embed.set_footer(text=f"ID: {arc['id']}")
    return embed

def create_map_embed(map_data: dict) -> discord.Embed:
    """إنشاء Embed للخريطة"""
    
    embed = discord.Embed(
        title=f"🗺️ {map_data['name']['en']}",
        color=discord.Color.green()
    )
    
    if 'description' in map_data:
        embed.description = map_data['description'].get('en', '')[:300]
    
    embed.set_footer(text=f"ID: {map_data['id']}")
    return embed

# ══════════════════════════════════════════════════════════════════
#                    أحداث البوت (Events)
# ══════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    """عند تشغيل البوت"""
    print("═" * 50)
    print(f"✅ البوت شغال: {bot.user.name}")
    print(f"✅ ID: {bot.user.id}")
    print(f"✅ السيرفر: {ALLOWED_GUILD_ID}")
    print(f"✅ القناة: {ALLOWED_CHANNEL_ID}")
    print("═" * 50)
    
    # تغيير الحالة
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="أسئلتكم | اكتب دليل"
        )
    )
    
    # مزامنة الأوامر
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")

@bot.event
async def on_message(message: discord.Message):
    """معالجة الرسائل"""
    
    # تجاهل رسائل البوت نفسه
    if message.author.bot:
        return
    
    # تحقق من السيرفر والقناة
    if message.guild and message.guild.id != ALLOWED_GUILD_ID:
        return
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return
    
    # تحقق إذا البوت مذكور
    if not is_bot_mentioned(message):
        return
    
    # Rate Limiting
    allowed, wait_time = check_rate_limit(message.author.id)
    if not allowed:
        await message.reply(
            f"⏳ انتظر {wait_time} ثانية قبل السؤال التالي",
            delete_after=5
        )
        return
    
    # استخراج السؤال
    question = extract_question(message.content)
    
    if not question or len(question) < 2:
        await message.reply(
            "👋 أهلاً! أنا **دليل** - اسألني عن أي شي في ARC Raiders!\n"
            "مثال: `دليل وين ألقى Rusted Gear؟`"
        )
        return
    
    # إظهار أن البوت يكتب
    async with message.channel.typing():
        try:
            # معالجة السؤال
            text, embed = await process_question(question)
            
            if text:
                await message.reply(text, embed=embed)
            else:
                await message.reply(embed=embed)
                
        except Exception as e:
            print(f"❌ خطأ: {e}")
            await message.reply(
                "😅 صار خطأ، جرب مرة ثانية!",
                delete_after=10
            )
    
    # معالجة الأوامر العادية
    await bot.process_commands(message)

# ══════════════════════════════════════════════════════════════════
#                    Slash Commands
# ══════════════════════════════════════════════════════════════════

@bot.tree.command(name="item", description="🔍 البحث عن قطعة")
@app_commands.describe(name="اسم القطعة")
async def item_command(interaction: discord.Interaction, name: str):
    """أمر البحث عن قطعة"""
    
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ استخدم البوت في <#{ALLOWED_CHANNEL_ID}>",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    results = search_items(name)
    
    if not results:
        embed = discord.Embed(
            title="❌ ما لقيت",
            description=f"ما لقيت قطعة باسم: **{name}**",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return
    
    embed = create_item_embed(results[0])
    
    if len(results) > 1:
        others = "\n".join([f"• {i['name']['en']}" for i in results[1:4]])
        embed.add_field(name="📋 نتائج أخرى", value=others, inline=False)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="arc", description="🤖 البحث عن ARC")
@app_commands.describe(name="اسم الـ ARC")
async def arc_command(interaction: discord.Interaction, name: str):
    """أمر البحث عن ARC"""
    
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ استخدم البوت في <#{ALLOWED_CHANNEL_ID}>",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    results = search_arcs(name)
    
    if not results:
        embed = discord.Embed(
            title="❌ ما لقيت",
            description=f"ما لقيت ARC باسم: **{name}**",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return
    
    embed = create_arc_embed(results[0])
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="help", description="📋 قائمة الأوامر")
async def help_command(interaction: discord.Interaction):
    """أمر المساعدة"""
    
    embed = discord.Embed(
        title="📋 دليل - مساعدك في ARC Raiders",
        description="أنا بوت ذكي أساعدك في كل شي عن اللعبة!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="💬 الطريقة السهلة",
        value=(
            "اكتب **دليل** + سؤالك\n"
            "مثال: `دليل وين ألقى Rusted Gear؟`\n"
            "مثال: `دليل كيف أقتل Hunter؟`"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🔍 أوامر البحث",
        value=(
            "`/item [اسم]` - البحث عن قطعة\n"
            "`/arc [اسم]` - معلومات عن ARC\n"
            "`/stats` - إحصائيات البوت"
        ),
        inline=False
    )
    
    embed.set_footer(text="صنع بـ ❤️ لسيرفر ELITE-ZONE")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stats", description="📊 إحصائيات البوت")
async def stats_command(interaction: discord.Interaction):
    """أمر الإحصائيات"""
    
    embed = discord.Embed(
        title="📊 إحصائيات دليل",
        color=discord.Color.purple()
    )
    
    embed.add_field(name="📦 القطع", value=f"{len(ITEMS):,}", inline=True)
    embed.add_field(name="🤖 ARCs", value=str(len(BOTS)), inline=True)
    embed.add_field(name="🗺️ الخرائط", value=str(len(MAPS)), inline=True)
    embed.add_field(name="📜 المهام", value=str(len(QUESTS)), inline=True)
    
    # حالة AI
    ai_status = []
    if DEEPSEEK_API_KEY:
        ai_status.append("✅ DeepSeek")
    if GROQ_API_KEY:
        ai_status.append("✅ Groq")
    if ANTHROPIC_API_KEY:
        ai_status.append("✅ Claude")
    
    if ai_status:
        embed.add_field(name="🧠 الذكاء الاصطناعي", value="\n".join(ai_status), inline=False)
    
    embed.set_footer(text="بيانات من arcraiders-data")
    
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════════════════════════
#                         تشغيل البوت
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        print("═" * 50)
        print("❌ خطأ: DISCORD_TOKEN غير موجود!")
        print("أضف DISCORD_TOKEN في متغيرات البيئة")
        print("═" * 50)
    else:
        print("═" * 50)
        print("🚀 جاري تشغيل بوت دليل...")
        print("═" * 50)
        
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"❌ خطأ في التشغيل: {e}")
