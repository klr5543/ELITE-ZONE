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

# إعدادات الأمان
ALLOWED_GUILD_ID = 621014916173791288  # سيرفر SPECTRE
ALLOWED_CHANNEL_ID = 1459709364301594848  # قناة دليل
LOG_CHANNEL_ID = 1460565420644892881  # قناة اللوق
OWNER_ID = 595228721946820614  # نواف

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
    """تطبيع النص للبحث (إزالة التشكيل والمسافات الزائدة)"""
    # إزالة التشكيل العربي
    arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670]')
    text = arabic_diacritics.sub('', text)
    return text.lower().strip()

def search_items(query: str, limit: int = 5) -> List[dict]:
    """البحث عن items بالعربي أو الإنجليزي"""
    query = normalize_text(query)
    results = []
    
    for item_id, item in ITEMS.items():
        # البحث في الاسم الإنجليزي
        if query in item['name']['en'].lower():
            results.append(item)
            continue
        
        # البحث في الـ ID
        if query in item_id.lower():
            results.append(item)
            continue
        
        # البحث في الوصف الإنجليزي
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

# ================== Embeds ==================
def create_item_embed(item: dict) -> discord.Embed:
    """إنشاء Embed لعرض معلومات الـ item"""
    embed = discord.Embed(
        title=f"📦 {item['name']['en']}",
        color=discord.Color.blue()
    )
    
    # الوصف
    if 'description' in item:
        desc = item['description']['en'][:200]
        embed.description = desc
    
    # النوع والندرة
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
    
    # القيمة والوزن
    if 'value' in item:
        embed.add_field(name="القيمة", value=f"{item['value']} coins", inline=True)
    
    if 'weightKg' in item:
        embed.add_field(name="الوزن", value=f"{item['weightKg']} kg", inline=True)
    
    # وصفة الصناعة
    if 'recipe' in item and item['recipe']:
        recipe_text = "\n".join([f"• {r['itemId']}: {r['quantity']}" for r in item['recipe'][:3]])
        embed.add_field(name="🔧 الصناعة", value=recipe_text, inline=False)
    
    # الصورة
    if 'imageFilename' in item:
        image_url = f"https://cdn.arctracker.io/items/{item['imageFilename']}"
        embed.set_thumbnail(url=image_url)
    
    embed.set_footer(text=f"ID: {item['id']}")
    return embed

def create_arc_embed(arc: dict) -> discord.Embed:
    """إنشاء Embed لعرض معلومات الـ ARC"""
    # ألوان حسب مستوى التهديد
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
        description=arc['description'],
        color=color
    )
    
    # النوع ومستوى التهديد
    embed.add_field(name="النوع", value=arc['type'], inline=True)
    embed.add_field(name="مستوى التهديد", value=arc['threat'], inline=True)
    
    # نقاط الضعف
    if 'weakness' in arc:
        embed.add_field(name="⚠️ نقطة الضعف", value=arc['weakness'], inline=False)
    
    # الخرائط
    if 'maps' in arc and arc['maps']:
        maps_text = ", ".join(arc['maps'][:3])
        if len(arc['maps']) > 3:
            maps_text += f" +{len(arc['maps']) - 3}"
        embed.add_field(name="🗺️ الخرائط", value=maps_text, inline=False)
    
    # المكافآت
    embed.add_field(name="💰 XP (تدمير)", value=str(arc.get('destroyXp', 0)), inline=True)
    embed.add_field(name="💰 XP (نهب)", value=str(arc.get('lootXp', 0)), inline=True)
    
    # الـ Drops
    if 'drops' in arc and arc['drops']:
        drops_text = ", ".join(arc['drops'][:5])
        if len(arc['drops']) > 5:
            drops_text += f" +{len(arc['drops']) - 5}"
        embed.add_field(name="🎁 المسروقات", value=drops_text, inline=False)
    
    # الصورة
    if 'image' in arc:
        embed.set_image(url=arc['image'])
    
    embed.set_footer(text=f"ID: {arc['id']}")
    return embed

def create_map_embed(map_data: dict) -> discord.Embed:
    """إنشاء Embed لعرض معلومات الخريطة"""
    embed = discord.Embed(
        title=f"🗺️ {map_data['name']['en']}",
        color=discord.Color.green()
    )
    
    # الصورة
    if 'image' in map_data:
        embed.set_image(url=map_data['image'])
    
    embed.set_footer(text=f"ID: {map_data['id']}")
    return embed

# ================== الأوامر ==================
@bot.event
async def on_ready():
    """عند تشغيل البوت"""
    print(f'✅ البوت شغال: {bot.user.name}')
    print(f'✅ ID: {bot.user.id}')
    
    # مزامنة الأوامر
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر")
    except Exception as e:
        print(f"❌ خطأ في المزامنة: {e}")

@bot.tree.command(name="item", description="البحث عن item في اللعبة")
@app_commands.describe(اسم="اسم الـ item بالعربي أو الإنجليزي")
async def item_command(interaction: discord.Interaction, اسم: str):
    """أمر البحث عن item"""
    # التحقق من السيرفر والقناة
    if interaction.guild_id != ALLOWED_GUILD_ID:
        await interaction.response.send_message("❌ هذا البوت يعمل فقط في سيرفر SPECTRE", ephemeral=True)
        return
    
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message(f"❌ يرجى استخدام البوت في <#{ALLOWED_CHANNEL_ID}>", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    results = search_items(اسم)
    
    if not results:
        embed = discord.Embed(
            title="❌ لم يتم العثور على نتائج",
            description=f"لم أجد أي item باسم: **{اسم}**",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return
    
    # عرض أول نتيجة
    item = results[0]
    embed = create_item_embed(item)
    
    # إذا كان هناك نتائج إضافية
    if len(results) > 1:
        other_items = "\n".join([f"• {i['name']['en']}" for i in results[1:4]])
        embed.add_field(
            name="📋 نتائج أخرى",
            value=other_items,
            inline=False
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="arc", description="البحث عن ARC (عدو) في اللعبة")
@app_commands.describe(اسم="اسم الـ ARC")
async def arc_command(interaction: discord.Interaction, اسم: str):
    """أمر البحث عن ARC"""
    await interaction.response.defer()
    
    results = search_arcs(اسم)
    
    if not results:
        embed = discord.Embed(
            title="❌ لم يتم العثور على نتائج",
            description=f"لم أجد أي ARC باسم: **{اسم}**",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return
    
    # عرض أول نتيجة
    arc = results[0]
    embed = create_arc_embed(arc)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="arcs", description="عرض قائمة بكل الـ ARCs")
async def arcs_command(interaction: discord.Interaction):
    """أمر عرض كل الـ ARCs"""
    await interaction.response.defer()
    
    embed = discord.Embed(
        title="🤖 قائمة ARCs",
        description="جميع الأعداء في اللعبة",
        color=discord.Color.blue()
    )
    
    # تقسيم حسب مستوى التهديد
    threats = {}
    for arc in BOTS:
        threat = arc.get('threat', 'Unknown')
        if threat not in threats:
            threats[threat] = []
        threats[threat].append(arc['name'])
    
    # عرض كل مستوى تهديد
    threat_order = ['Extreme', 'Critical', 'High', 'Moderate', 'Low']
    for threat in threat_order:
        if threat in threats:
            arcs_list = "\n".join([f"• {name}" for name in threats[threat]])
            embed.add_field(name=f"⚠️ {threat}", value=arcs_list, inline=False)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="map", description="البحث عن خريطة في اللعبة")
@app_commands.describe(اسم="اسم الخريطة")
async def map_command(interaction: discord.Interaction, اسم: str):
    """أمر البحث عن خريطة"""
    await interaction.response.defer()
    
    results = search_maps(اسم)
    
    if not results:
        embed = discord.Embed(
            title="❌ لم يتم العثور على نتائج",
            description=f"لم أجد أي خريطة باسم: **{اسم}**",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return
    
    # عرض أول نتيجة
    map_data = results[0]
    embed = create_map_embed(map_data)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="maps", description="عرض قائمة بكل الخرائط")
async def maps_command(interaction: discord.Interaction):
    """أمر عرض كل الخرائط"""
    await interaction.response.defer()
    
    embed = discord.Embed(
        title="🗺️ قائمة الخرائط",
        description="جميع الخرائط المتوفرة في اللعبة",
        color=discord.Color.green()
    )
    
    maps_list = "\n".join([f"• **{m['name']['en']}**\n   `{m['id']}`" for m in MAPS])
    embed.add_field(name="الخرائط", value=maps_list, inline=False)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="craft", description="عرض وصفة صناعة item")
@app_commands.describe(اسم="اسم الـ item")
async def craft_command(interaction: discord.Interaction, اسم: str):
    """أمر عرض وصفة الصناعة"""
    await interaction.response.defer()
    
    results = search_items(اسم, limit=1)
    
    if not results:
        embed = discord.Embed(
            title="❌ لم يتم العثور على نتائج",
            description=f"لم أجد أي item باسم: **{اسم}**",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return
    
    item = results[0]
    
    embed = discord.Embed(
        title=f"🔧 وصفة صناعة: {item['name']['en']}",
        color=discord.Color.gold()
    )
    
    # التحقق من وجود وصفة
    if 'recipe' not in item or not item['recipe']:
        embed.description = "❌ هذا الـ item لا يمكن صناعته"
        await interaction.followup.send(embed=embed)
        return
    
    # عرض المتطلبات
    recipe_text = ""
    for ingredient in item['recipe']:
        ing_id = ingredient['itemId']
        quantity = ingredient['quantity']
        
        # محاولة الحصول على الاسم الإنجليزي
        ing_name = ing_id
        if ing_id in ITEMS:
            ing_name = ITEMS[ing_id]['name']['en']
        
        recipe_text += f"• **{quantity}x** {ing_name}\n"
    
    embed.add_field(name="المتطلبات", value=recipe_text, inline=False)
    
    # معلومات الصناعة
    if 'craftBench' in item:
        embed.add_field(name="المنشأة", value=item['craftBench'], inline=True)
    
    if 'stationLevelRequired' in item:
        embed.add_field(name="المستوى المطلوب", value=str(item['stationLevelRequired']), inline=True)
    
    if 'craftQuantity' in item:
        embed.add_field(name="الكمية المنتجة", value=str(item['craftQuantity']), inline=True)
    
    # الصورة
    if 'imageFilename' in item:
        image_url = f"https://cdn.arctracker.io/items/{item['imageFilename']}"
        embed.set_thumbnail(url=image_url)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="help", description="عرض قائمة الأوامر المتاحة")
async def help_command(interaction: discord.Interaction):
    """أمر المساعدة"""
    embed = discord.Embed(
        title="📋 قائمة الأوامر",
        description="جميع الأوامر المتاحة في البوت",
        color=discord.Color.blue()
    )
    
    commands_list = """
    **🔍 أوامر البحث:**
    • `/item [اسم]` - البحث عن item
    • `/arc [اسم]` - البحث عن ARC (عدو)
    • `/map [اسم]` - البحث عن خريطة
    • `/craft [اسم]` - عرض وصفة الصناعة
    
    **📊 أوامر القوائم:**
    • `/arcs` - عرض جميع الـ ARCs
    • `/maps` - عرض جميع الخرائط
    
    **ℹ️ أوامر المساعدة:**
    • `/help` - عرض هذه القائمة
    • `/stats` - إحصائيات البوت
    """
    
    embed.description = commands_list
    embed.set_footer(text="البوت مبني خصيصاً لـ ARC Raiders 🎮")
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="stats", description="عرض إحصائيات البوت")
async def stats_command(interaction: discord.Interaction):
    """أمر عرض الإحصائيات"""
    embed = discord.Embed(
        title="📊 إحصائيات البوت",
        color=discord.Color.purple()
    )
    
    embed.add_field(name="📦 Items", value=str(len(ITEMS)), inline=True)
    embed.add_field(name="🤖 ARCs", value=str(len(BOTS)), inline=True)
    embed.add_field(name="🗺️ Maps", value=str(len(MAPS)), inline=True)
    embed.add_field(name="🎯 Projects", value=str(len(PROJECTS)), inline=True)
    embed.add_field(name="💪 Skill Nodes", value=str(len(SKILL_NODES)), inline=True)
    embed.add_field(name="🏪 Trades", value=str(len(TRADES)), inline=True)
    
    embed.set_footer(text=f"البوت في {len(bot.guilds)} سيرفر")
    
    await interaction.followup.send(embed=embed)

# ================== تشغيل البوت ==================
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        print("❌ خطأ: لم يتم العثور على DISCORD_TOKEN في البيئة!")
        print("يرجى إضافة التوكن في ملف .env")
    else:
        bot.run(TOKEN)
