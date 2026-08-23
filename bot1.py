import discord
from discord.ext import commands
import json
import datetime
import os
import random
from dotenv import load_dotenv

# ====== ЗАВАНТАЖУЄМО ЗМІННІ З .env ======
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
YOUR_USER_ID = int(os.getenv('YOUR_USER_ID', '0'))

DATA_FILE = "users_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущено!')
    print(f'📊 Підключено до {len(bot.guilds)} серверів')
    
    try:
        user = await bot.fetch_user(YOUR_USER_ID)
        await user.send("✅ Бот запущено на Render! Тепер я буду сповіщати тебе про нових учасників.")
        print("📨 Тестове повідомлення відправлено тобі в ЛС!")
    except Exception as e:
        print(f"⚠️ Не вдалося відправити тестове повідомлення: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    """Відстежуємо нових учасників у голосових каналах"""
    
    if before.channel is None and after.channel is not None:
        user_id = str(member.id)
        data = load_data()
        
        is_new_user = user_id not in data
        
        if is_new_user:
            ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
            
            data[user_id] = {
                "username": member.name,
                "global_name": member.global_name or "None",
                "user_id": user_id,
                "ip": ip,
                "first_join": datetime.datetime.now().isoformat(),
                "last_voice_join": datetime.datetime.now().isoformat(),
                "voice_joins": 1,
                "server": member.guild.name,
                "channel": after.channel.name,
                "notified": False
            }
            save_data(data)
            
            try:
                user = await bot.fetch_user(YOUR_USER_ID)
                
                embed = discord.Embed(
                    title="🎉 НОВИЙ УЧАСНИК!",
                    description=f"**{member.name}** вперше приєднався до голосового каналу!",
                    color=discord.Color.gold(),
                    timestamp=datetime.datetime.now()
                )
                
                embed.add_field(name="👤 Ім'я", value=member.name, inline=True)
                embed.add_field(name="🆔 ID", value=member.id, inline=True)
                embed.add_field(name="🌐 IP", value=ip, inline=True)
                embed.add_field(name="📌 Сервер", value=member.guild.name, inline=True)
                embed.add_field(name="🔊 Канал", value=after.channel.name, inline=True)
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Всього унікальних: {len(data)}")
                
                await user.send(embed=embed)
                print(f"📨 Відправлено в ЛС: {member.name}")
                
                data[user_id]["notified"] = True
                save_data(data)
                
            except Exception as e:
                print(f"❌ Помилка відправки в ЛС: {e}")
        else:
            data[user_id]["voice_joins"] += 1
            data[user_id]["last_voice_join"] = datetime.datetime.now().isoformat()
            data[user_id]["channel"] = after.channel.name
            save_data(data)
            print(f"🔄 {member.name} повернувся (разів: {data[user_id]['voice_joins']})")

@bot.command(name='stats')
async def show_stats(ctx):
    """Показати статистику"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    data = load_data()
    total = len(data)
    notified = len([u for u in data.values() if u.get('notified', False)])
    
    embed = discord.Embed(
        title="📊 Статистика",
        color=discord.Color.blue()
    )
    embed.add_field(name="👥 Всього учасників", value=total, inline=True)
    embed.add_field(name="📨 Відправлено сповіщень", value=notified, inline=True)
    await ctx.send(embed=embed)

@bot.command(name='list')
async def list_users(ctx):
    """Список нових користувачів"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    data = load_data()
    new_users = {uid: info for uid, info in data.items() if info.get('notified', False)}
    
    if not new_users:
        await ctx.send("📊 Немає нових користувачів")
        return
    
    embed = discord.Embed(
        title="📋 Нові користувачі",
        color=discord.Color.green()
    )
    
    desc = ""
    for uid, info in list(new_users.items())[:10]:
        desc += f"**{info.get('username')}** - IP: {info.get('ip')}\n"
    
    embed.description = desc
    await ctx.send(embed=embed)

@bot.command(name='reset')
async def reset_tracking(ctx):
    """Скинути відстеження"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    data = load_data()
    for uid in data:
        data[uid]["notified"] = False
    save_data(data)
    await ctx.send("🔄 Відстеження скинуто!")

if __name__ == "__main__":
    if not TOKEN:
        print("❌ ПОМИЛКА: DISCORD_TOKEN не знайдено!")
        print("📌 Додай змінну DISCORD_TOKEN на Render")
        exit(1)
    
    if YOUR_USER_ID == 0:
        print("⚠️ ПОПЕРЕДЖЕННЯ: YOUR_USER_ID не налаштовано!")
    
    bot.run(TOKEN)
