import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import sqlite3
import config

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS vouches (
            id INTEGER PRIMARY KEY AUTOINCREMENT, receiver_id INTEGER,
            giver_id INTEGER, message TEXT, timestamp TEXT)""")
        conn.commit()
        conn.close()

    @app_commands.command(name="ping", description="Check latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        color = config.SUCCESS_COLOR if latency < 200 else config.WARNING_COLOR if latency < 500 else config.ERROR_COLOR
        embed = discord.Embed(title="Pong!", description=f"Latency: **{latency}ms**", color=color)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="User info")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        embed = discord.Embed(title=f"User Info - {user}", color=config.INFO_COLOR, timestamp=datetime.now())
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="ID", value=f"`{user.id}`", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(user.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Joined", value=f"<t:{int(user.joined_at.timestamp())}:R>" if user.joined_at else "N/A", inline=True)
        roles = [r.mention for r in user.roles if r.name != "@everyone"]
        embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join(roles[:10]) or "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Server info")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"{guild.name} Info", color=config.INFO_COLOR)
        embed.add_field(name="Members", value=f"{guild.member_count}", inline=True)
        embed.add_field(name="Channels", value=f"{len(guild.channels)}", inline=True)
        embed.add_field(name="Roles", value=f"{len(guild.roles)}", inline=True)
        embed.add_field(name="Boosts", value=f"Level {guild.premium_tier} | {guild.premium_subscription_count}", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="vouch", description="Leave a review")
    async def vouch(self, interaction: discord.Interaction, user: discord.Member, message: str):
        if user.id == interaction.user.id:
            await interaction.response.send_message("❌ Can't vouch for yourself!", ephemeral=True)
            return
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO vouches (receiver_id, giver_id, message, timestamp) VALUES (?, ?, ?, ?)",
                  (user.id, interaction.user.id, message, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        vouch_channel = interaction.guild.get_channel(config.VOUCH_CHANNEL)
        if vouch_channel:
            embed = discord.Embed(title="New Vouch!", description=f"{interaction.user.mention} vouched for {user.mention}", color=config.SUCCESS_COLOR)
            embed.add_field(name="Review", value=message, inline=False)
            await vouch_channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Vouched for {user.mention}!")

    @app_commands.command(name="vouches", description="View reviews")
    async def vouches(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT giver_id, message, timestamp FROM vouches WHERE receiver_id = ? ORDER BY timestamp DESC", (user.id,))
        results = c.fetchall()
        conn.close()
        if not results:
            await interaction.response.send_message(f"{user.mention} has no vouches.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Vouches for {user}", description=f"Total: {len(results)}", color=config.SUCCESS_COLOR)
        for giver_id, msg, ts in results[:5]:
            giver = self.bot.get_user(giver_id)
            name = giver.name if giver else f"User {giver_id}"
            embed.add_field(name=f"From {name}", value=msg[:1024], inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="announce", description="Send announcement (Admin)")
    @app_commands.checks.has_permissions(administrator=True)
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, title: str, message: str, ping: bool = False):
        embed = discord.Embed(title=title, description=message, color=config.EMBED_COLOR, timestamp=datetime.now())
        embed.set_footer(text=f"By {interaction.user}", icon_url=interaction.user.display_avatar.url)
        content = "@everyone" if ping else None
        await channel.send(content=content, embed=embed)
        await interaction.response.send_message(f"✅ Sent to {channel.mention}!")

    @app_commands.command(name="poll", description="Create a poll")
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
        options = [o for o in [option1, option2, option3, option4] if o]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        embed = discord.Embed(title="Poll", description=f"**{question}**", color=config.INFO_COLOR)
        for i, opt in enumerate(options):
            embed.add_field(name=f"{emojis[i]} {opt}", value="Vote!", inline=False)
        embed.set_footer(text=f"By {interaction.user}")
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        for i in range(len(options)):
            await message.add_reaction(emojis[i])

async def setup(bot):
    await bot.add_cog(Utility(bot))
