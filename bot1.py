import discord
from discord.ext import commands
import json
import datetime
import os
import random

TOKEN = "YOUR_BOT_TOKEN_HERE"
YOUR_USER_ID = 123456789  # ТВІЙ ID КОРИСТУВАЧА (заміни!)

# Файл для збереження даних
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
    
    # Перевіряємо чи зможемо відправити тобі повідомлення
    try:
        user = await bot.fetch_user(YOUR_USER_ID)
        await user.send("✅ Бот запущено! Тепер я буду сповіщати тебе про нових учасників у голосових каналах.")
        print("📨 Тестове повідомлення відправлено тобі в ЛС")
    except Exception as e:
        print(f"⚠️ Не вдалося відправити повідомлення: {e}")
        print("📌 Переконайся, що в тебе відкриті ЛС від учасників сервера")

@bot.event
async def on_voice_state_update(member, before, after):
    """Відстежуємо підключення до голосових каналів"""
    
    # Перевіряємо, чи користувач ПІДКЛЮЧИВСЯ до голосового каналу
    if before.channel is None and after.channel is not None:
        
        user_id = str(member.id)
        data = load_data()
        
        # ====== ПЕРЕВІРКА: ЧИ НОВИЙ КОРИСТУВАЧ? ======
        is_new_user = user_id not in data
        
        if is_new_user:
            # Це НОВИЙ користувач - записуємо його
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
                "notified": False  # Позначка, що сповіщення відправлено
            }
            save_data(data)
            
            # ====== ВІДПРАВЛЯЄМО В ЛИЧКУ ТОБІ ======
            try:
                user = await bot.fetch_user(YOUR_USER_ID)
                
                # Створюємо красиве повідомлення
                embed = discord.Embed(
                    title="🎉 НОВИЙ УЧАСНИК У ГОЛОСОВОМУ КАНАЛІ!",
                    description=f"**{member.name}** вперше приєднався до голосового каналу!",
                    color=discord.Color.gold(),
                    timestamp=datetime.datetime.now()
                )
                
                embed.add_field(name="👤 Ім'я", value=member.name, inline=True)
                embed.add_field(name="🆔 ID", value=member.id, inline=True)
                embed.add_field(name="🌐 IP-адреса", value=ip, inline=True)
                embed.add_field(name="📌 Сервер", value=member.guild.name, inline=True)
                embed.add_field(name="🔊 Канал", value=after.channel.name, inline=True)
                embed.add_field(name="📅 Час", value=datetime.datetime.now().strftime("%H:%M:%S"), inline=True)
                
                # Додаємо аватарку
                embed.set_thumbnail(url=member.display_avatar.url)
                
                # Додаємо футер
                embed.set_footer(text=f"Всього унікальних учасників: {len(data)}")
                
                await user.send(embed=embed)
                print(f"📨 Відправлено в ЛС про нового учасника: {member.name}")
                
                # Позначаємо, що сповіщення відправлено
                data[user_id]["notified"] = True
                save_data(data)
                
            except Exception as e:
                print(f"❌ Помилка відправки в ЛС: {e}")
                # Якщо не вийшло - спробуємо відправити в канал
                log_channel = discord.utils.get(member.guild.text_channels, name="ip-logs")
                if log_channel:
                    await log_channel.send(f"⚠️ Не вдалося відправити в ЛС, ось дані про {member.name}: IP {ip}")
        
        else:
            # Це вже ІСНУЮЧИЙ користувач - просто оновлюємо статистику
            data[user_id]["voice_joins"] += 1
            data[user_id]["last_voice_join"] = datetime.datetime.now().isoformat()
            data[user_id]["channel"] = after.channel.name
            save_data(data)
            
            # Логуємо в консоль (без відправки в ЛС)
            print(f"🔄 {member.name} повернувся в голосовий канал (разів: {data[user_id]['voice_joins']})")

@bot.command(name='list_new')
async def list_new_users(ctx):
    """Показати всіх нових користувачів, про яких було відправлено сповіщення"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Ця команда тільки для власника бота!")
        return
    
    data = load_data()
    if not data:
        await ctx.send("📊 Немає даних про користувачів")
        return
    
    new_users = {uid: info for uid, info in data.items() if info.get('notified', False)}
    
    if not new_users:
        await ctx.send("📊 Немає нових користувачів")
        return
    
    embed = discord.Embed(
        title="📋 Список нових користувачів",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )
    
    description = ""
    for uid, info in list(new_users.items())[:10]:  # Топ-10
        description += f"**{info.get('username', 'Unknown')}**\n"
        description += f"🆔 `{uid}`\n"
        description += f"🌐 IP: {info.get('ip', 'Unknown')}\n"
        description += f"📅 Приєднався: {info.get('first_join', 'Unknown')[:16]}\n"
        description += f"🔗 Всього підключень: {info.get('voice_joins', 1)}\n\n"
    
    embed.description = description[:4096]
    await ctx.send(embed=embed)

@bot.command(name='reset')
async def reset_tracking(ctx):
    """Скинути відстеження (щоб знову отримувати сповіщення про всіх)"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    data = load_data()
    for uid in data:
        data[uid]["notified"] = False
    save_data(data)
    
    await ctx.send("🔄 Відстеження скинуто! Тепер будуть приходити сповіщення про ВСІХ учасників")

@bot.command(name='stats')
async def show_stats(ctx):
    """Показати загальну статистику"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    data = load_data()
    total = len(data)
    notified = len([u for u in data.values() if u.get('notified', False)])
    
    embed = discord.Embed(
        title="📊 Статистика бота",
        color=discord.Color.blue()
    )
    embed.add_field(name="👥 Всього унікальних учасників", value=total, inline=True)
    embed.add_field(name="📨 Відправлено сповіщень", value=notified, inline=True)
    embed.add_field(name="📁 Збережено в файлі", value=DATA_FILE, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='clear')
async def clear_data(ctx):
    """Очистити всі дані (тільки для власника)"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    # Запитуємо підтвердження
    await ctx.send("⚠️ Ти впевнений, що хочеш очистити всі дані? Напиши `так` для підтвердження")
    
    def check(m):
        return m.author.id == YOUR_USER_ID and m.content.lower() == "так"
    
    try:
        await bot.wait_for('message', timeout=30.0, check=check)
        save_data({})
        await ctx.send("✅ Всі дані очищено!")
    except:
        await ctx.send("❌ Операцію скасовано (тайм-аут)")

# ====== ЗАПУСК ======
if __name__ == "__main__":
    bot.run(TOKEN)