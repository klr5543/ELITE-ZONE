# Test file - إذا شفت هذا في الـ logs، يعني الملف الجديد شغال!
import discord
from discord.ext import commands
import os

print("="*60)
print("🔥 TESTING - UPDATED FILE IS RUNNING!")
print("="*60)

TOKEN = os.getenv('TOKEN') or os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("="*60)
    print("✅ ✅ ✅ NEW FILE IS WORKING! ✅ ✅ ✅")
    print("="*60)

@bot.event  
async def on_message(message):
    if message.author == bot.user:
        return
    
    if 'فوكسي' in message.content.lower() or 'foxy' in message.content.lower():
        await message.reply("✅ الملف الجديد شغال! رد واحد فقط!", mention_author=False)
        print(f"✅ Replied ONCE to: {message.content}")
    
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)
