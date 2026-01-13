import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from pathlib import Path
from typing import Optional, List
import re

# ================== إعدادات البوت ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# إعدادات الأمان (من متغيرات البيئة في الاستضافة)
ALLOWED_GUILD_ID = int(os.getenv('ALLOWED_GUILD_ID', '621014916173791288'))
ALLOWED_CHANNEL_ID = int(os.getenv('ALLOWED_CHANNEL_ID', '1459709364301594848'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '1460565420644892881'))
OWNER_ID = int(os.getenv('OWNER_ID', '595228721946820614'))

# ================== تحميل البيانات ==================
DATA_PATH = Path("arcraiders-data")

def load_json(filename: str) -> list:
    """تحميل ملف JSON"""
    filepath = DATA_PATH / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_items() -> dict:
    """تحميل جميع الـ items من مجلد items"""
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

# تحميل كل البيانات عند التشغيل
ITEMS = load_items()
BOTS = load_json("bots.json")
MAPS = load_json("maps.json")

print(f"✅ تم تحميل {len(ITEMS)} item")
print(f"✅ تم تحميل {len(BOTS)} ARC")
print(f"✅ تم تحميل {len(MAPS)} خريطة")

# ================== دوال البحث ==================
def normalize_text(text: str) -> str:
    """تطبيع النص للبحث"""
    arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670]')
    text = arabic_diacritics.sub('', text)
    return text.lower().strip()

def search_items(query: str, limit: int = 5) -> List[dict]:
    """البحث عن items"""
    query = normalize_text(query)
    results = []
    
    for item_id, item in ITEMS.items():
        if query in item['name']['en'].lower():
            results.append(item)
            continue
        if query in item_id.lower():
            results.append(item)
            continue
        if 'description' in item and query in item['description']['en'].lower():
            results.append(item)
    
    return results[:limit]

def search_arcs(query: str) -> List[dict]:
    """البحث عن ARCs"""
    query = normalize_text(query)
    results = []
    
    for arc in BOTS:
        if query in arc['name'].lower() or query in arc['id'].lower():
            results.append(arc)
    
    return results

def search_maps(query: str) -> List[dict]:
    """البحث عن الخرائط"""
    query = normalize_text(query)
    results = []
    
    for map_data in MAPS:
        if query in map_data['name']['en'].lower() or query in map_data['id'].lower():
            results.append(map_data)
    
    return results

# ================== دالة التحقق من الصلاحيات ==================
def check_permissions(interaction: discord.Interaction) -> bool:
    """التحقق من أن المستخدم في السيرفر والقناة الصحيحة"""
    if interaction.guild_id != ALLOWED_GUILD_ID:
        return False
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return False
    return True

async def log_command(interaction: discord.Interaction, command: str, details: str = ""):
    """إرسال لوق للأوامر"""
    try:
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title=f"📝 أمر: {command}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="المستخدم", value=interaction.user.mention, inline=True)
            embed.add_field(name="القناة", value=interaction.channel.mention, inline=True)
            if details:
                embed.add_field(name="التفاصيل", value=details, inline=False)
            await log_channel.send(embed=embed)
    except:
        pass

# ================== Embeds ==================
def create_item_embed(item: dict) -> discord.Embed:
    """إنشاء Embed للـ item"""
    embed = discord.Embed(
        title=f"📦 {item['name']['en']}",
        color=discord.Color.blue()
    )
    
    if 'description' in item:
        desc = item['description']['en'][:300]
        embed.description = desc
    
    if 'type' in item:
        embed.add_field(name="النوع", value=item['type'], inline=True)
    
    if 'rarity' in item:
        rarity_emoji = {
            'Common': '⚪',
            'Uncommon': '🟢',
            'Rare': '🔵',
            'Epic': '🟣',
            'Legendary': '🟠'
        }
        emoji = rarity_emoji.get(item['rarity'], '⚪')
        embed.add_field(name="الندرة", value=f"{emoji} {item['rarity']}", inline=True)
    
    if 'value' in item:
        embed.add_field(name="💰 القيمة", value=f"{item['value']} coins", inline=True)
    
    if 'weightKg' in item:
        embed.add_field(name="⚖️ الوزن", value=f"{item['weightKg']} kg", inline=True)
    
    if 'recipe' in item and item['recipe']:
        recipe_text = "\n".join([f"• {r['itemId']}: {r['quantity']}" for r in item['recipe'][:5]])
        if len(item['recipe']) > 5:
            recipe_text += f"\n... +{len(item['recipe']) - 5} أخرى"
        embed.add_field(name="🔧 وصفة الصناعة", value=recipe_text, inline=False)
    
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
    
    color = threat_colors.get(arc.get('threat', 'Moderate'), discord.Color.blue())
    
    embed = discord.Embed(
        title=f"🤖 {arc['name']}",
        description=arc['description'][:400],
        color=color
    )
    
    embed.add_field(name="النوع", value=arc['type'], inline=True)
    embed.add_field(name="⚠️ التهديد", value=arc['threat'], inline=True)
    
    if 'weakness' in arc:
        embed.add_field(name="🎯 نقطة الضعف", value=arc['weakness'], inline=False)
    
    embed.add_field(name="💰 XP (تدمير)", value=str(arc.get('destroyXp', 0)), inline=True)
    embed.add_field(name="💰 XP (نهب)", value=str(arc.get('lootXp', 0)), inline=True)
    
    if 'maps' in arc and arc['maps']:
        maps_text = ", ".join(arc['maps'][:3])
        if len(arc['maps']) > 3:
            maps_text += f" +{len(arc['maps']) - 3}"
        embed.add_field(name="🗺️ الخرائط", value=maps_text, inline=False)
    
    if 'drops' in arc and arc['drops']:
        drops_text = ", ".join(arc['drops'][:6])
        if len(arc['drops']) > 6:
            drops_text += f" +{len(arc['drops']) - 6}"
        embed.add_field(name="🎁 المسروقات", value=drops_text, inline=False)
    
    embed.set_footer(text=f"ID: {arc['id']}")
    return embed

# ================== الأوامر ==================
@bot.event
async def on_ready():
    """عند تشغيل البوت"""
    print(f'✅ البوت شغال: {bot.user.name}')
    print(f'✅ ID: {bot.user.id}')
    print(f'✅ السيرفر المسموح: {ALLOWED_GUILD_ID}')
    print(f'✅ القناة المسموحة: {ALLOWED_CHANNEL_ID}')
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")

@bot.tree.command(name="item", description="البحث عن item في اللعبة")
@app_commands.describe(اسم="اسم الـ item")
async def item_command(interaction: discord.Interaction, اسم: str):
    """أمر البحث عن item"""
    if not check_permissions(interaction):
        await interaction.response.send_message(
            f"❌ استخدم البوت في <#{ALLOWED_CHANNEL_ID}> في سيرفر SPECTRE",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    await log_command(interaction, "/item", اسم)
    
    results = search_items(اسم)
    
    if not results:
        embed = discord.Embed(
            title="❌ لم يتم العثور على نتائج",
            description=f"لم أجد أي item باسم: **{اسم}**",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return
    
    item = results[0]
    embed = create_item_embed(item)
    
    if len(results) > 1:
        other_items = "\n".join([f"• {i['name']['en']}" for i in results[1:4]])
        embed.add_field(
            name=f"📋 نتائج أخرى ({len(results)-1})",
            value=other_items,
            inline=False
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="arc", description="البحث عن ARC (عدو)")
@app_commands.describe(اسم="اسم الـ ARC")
async def arc_command(interaction: discord.Interaction, اسم: str):
    """أمر البحث عن ARC"""
    if not check_permissions(interaction):
        await interaction.response.send_message(
            f"❌ استخدم البوت في <#{ALLOWED_CHANNEL_ID}> في سيرفر SPECTRE",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    await log_command(interaction, "/arc", اسم)
    
    results = search_arcs(اسم)
    
    if not results:
        embed = discord.Embed(
            title="❌ لم يتم العثور على نتائج",
            description=f"لم أجد أي ARC باسم: **{اسم}**",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return
    
    arc = results[0]
    embed = create_arc_embed(arc)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="help", description="عرض قائمة الأوامر")
async def help_command(interaction: discord.Interaction):
    """أمر المساعدة"""
    if not check_permissions(interaction):
        await interaction.response.send_message(
            f"❌ استخدم البوت في <#{ALLOWED_CHANNEL_ID}> في سيرفر SPECTRE",
            ephemeral=True
        )
        return
    
    await log_command(interaction, "/help")
    
    embed = discord.Embed(
        title="📋 دليل - بوت ARC Raiders",
        description="بوت عربي لمعلومات لعبة ARC Raiders",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🔍 أوامر البحث",
        value=(
            "`/item [اسم]` - ابحث عن item\n"
            "`/arc [اسم]` - معلومات عن ARC\n"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📊 معلومات",
        value=(
            "`/stats` - إحصائيات البوت\n"
            "`/help` - هذه القائمة"
        ),
        inline=False
    )
    
    embed.set_footer(text="مصنوع بـ ❤️ لسيرفر SPECTRE")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stats", description="إحصائيات البوت")
async def stats_command(interaction: discord.Interaction):
    """أمر الإحصائيات"""
    if not check_permissions(interaction):
        await interaction.response.send_message(
            f"❌ استخدم البوت في <#{ALLOWED_CHANNEL_ID}> في سيرفر SPECTRE",
            ephemeral=True
        )
        return
    
    await log_command(interaction, "/stats")
    
    embed = discord.Embed(
        title="📊 إحصائيات البوت",
        color=discord.Color.purple()
    )
    
    embed.add_field(name="📦 Items", value=f"{len(ITEMS):,}", inline=True)
    embed.add_field(name="🤖 ARCs", value=str(len(BOTS)), inline=True)
    embed.add_field(name="🗺️ خرائط", value=str(len(MAPS)), inline=True)
    
    embed.set_footer(text="بيانات من arcraiders-data")
    
    await interaction.response.send_message(embed=embed)

# ================== تشغيل البوت ==================
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        print("❌ خطأ: DISCORD_TOKEN غير موجود في متغيرات البيئة!")
        print("يرجى إضافة DISCORD_TOKEN في إعدادات الاستضافة")
    else:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"❌ خطأ في تشغيل البوت: {e}")
