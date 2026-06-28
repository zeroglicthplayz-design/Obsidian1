import discord
from discord.ext import commands
import sqlite3
import config
from datetime import datetime, timedelta

DB_PATH = "economy.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, daily_claimed TEXT)")
    conn.commit()
    conn.close()

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()

    def get_balance(self, user_id):
        conn = get_db()
        cur = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            conn.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            conn.commit()
            conn.close()
            return 0
        conn.close()
        return row["balance"]

    def set_balance(self, user_id, amount):
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO users (user_id, balance) VALUES (?, ?)", (user_id, amount))
        conn.commit()
        conn.close()

    @commands.command(name="balance")
    async def balance_cmd(self, ctx, member: discord.Member = None):
        """Check your G-Coins balance"""
        target = member or ctx.author
        bal = self.get_balance(target.id)
        embed = discord.Embed(title="Balance", description=f"**{target.mention}**
**Balance:** `{bal:,}` G-Coins", color=config.COLOR_PRIMARY)
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily_cmd(self, ctx):
        """Claim your daily 100 G-Coins reward"""
        conn = get_db()
        cur = conn.execute("SELECT daily_claimed FROM users WHERE user_id = ?", (ctx.author.id,))
        row = cur.fetchone()
        now = datetime.utcnow()
        if row and row["daily_claimed"]:
            last = datetime.fromisoformat(row["daily_claimed"])
            if now - last < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last)
                h, rem = divmod(int(remaining.total_seconds()), 3600)
                m, _ = divmod(rem, 60)
                await ctx.send(embed=discord.Embed(title="Daily Reward", description=f"Already claimed. Next: {h}h {m}m", color=config.COLOR_WARNING))
                conn.close()
                return
        bal = self.get_balance(ctx.author.id)
        self.set_balance(ctx.author.id, bal + config.DAILY_REWARD)
        conn.execute("UPDATE users SET daily_claimed = ? WHERE user_id = ?", (now.isoformat(), ctx.author.id))
        conn.commit()
        conn.close()
        embed = discord.Embed(title="Daily Reward Claimed", description=f"**+{config.DAILY_REWARD} G-Coins**
**New Balance:** `{bal + config.DAILY_REWARD:,}`", color=config.COLOR_SUCCESS)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="pay")
    async def pay_cmd(self, ctx, member: discord.Member, amount: int):
        """Send G-Coins to another user"""
        if member == ctx.author:
            await ctx.send(embed=discord.Embed(title="Error", description="Can't pay yourself.", color=config.COLOR_ERROR))
            return
        if amount <= 0:
            await ctx.send(embed=discord.Embed(title="Error", description="Amount must be positive.", color=config.COLOR_ERROR))
            return
        sender_bal = self.get_balance(ctx.author.id)
        if sender_bal < amount:
            await ctx.send(embed=discord.Embed(title="Insufficient Funds", description=f"You have `{sender_bal:,}` G-Coins.", color=config.COLOR_ERROR))
            return
        self.set_balance(ctx.author.id, sender_bal - amount)
        self.set_balance(member.id, self.get_balance(member.id) + amount)
        await ctx.send(embed=discord.Embed(title="Payment Sent", description=f"**From:** {ctx.author.mention}
**To:** {member.mention}
**Amount:** `{amount:,}` G-Coins", color=config.COLOR_SUCCESS))

    @commands.command(name="leaderboard")
    async def leaderboard_cmd(self, ctx):
        """View top 10 richest users"""
        conn = get_db()
        cur = conn.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        embed = discord.Embed(title="Leaderboard", description="Top 10 richest users", color=config.COLOR_PRIMARY)
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, row in enumerate(rows):
            user = ctx.guild.get_member(row["user_id"])
            name = user.mention if user else f"User {row['user_id']}"
            embed.add_field(name=f"{medals[i]} {name}", value=f"`{row['balance']:,}` G-Coins", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="addcoins")
    @commands.has_permissions(administrator=True)
    async def addcoins_cmd(self, ctx, member: discord.Member, amount: int):
        """Add coins to a user (Admin only)"""
        bal = self.get_balance(member.id)
        self.set_balance(member.id, bal + amount)
        await ctx.send(embed=discord.Embed(title="Coins Added", description=f"**User:** {member.mention}
**Added:** `{amount:,}`
**New:** `{bal + amount:,}`", color=config.COLOR_SUCCESS))

    @commands.command(name="removecoins")
    @commands.has_permissions(administrator=True)
    async def removecoins_cmd(self, ctx, member: discord.Member, amount: int):
        """Remove coins from a user (Admin only)"""
        bal = self.get_balance(member.id)
        new_bal = max(0, bal - amount)
        self.set_balance(member.id, new_bal)
        await ctx.send(embed=discord.Embed(title="Coins Removed", description=f"**User:** {member.mention}
**Removed:** `{amount:,}`
**New:** `{new_bal:,}`", color=config.COLOR_WARNING))

async def setup(bot):
    await bot.add_cog(Economy(bot))
