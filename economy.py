import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import sqlite3
import config

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0,
            daily_claimed TEXT, total_spent INTEGER DEFAULT 0, total_earned INTEGER DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount INTEGER,
            type TEXT, description TEXT, timestamp TEXT)""")
        conn.commit()
        conn.close()

    def get_balance(self, user_id):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0

    def add_balance(self, user_id, amount, description=""):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
        c.execute("UPDATE users SET balance = balance + ?, total_earned = total_earned + ? WHERE user_id = ?", (amount, amount, user_id))
        c.execute("INSERT INTO transactions (user_id, amount, type, description, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (user_id, amount, 'credit', description, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def remove_balance(self, user_id, amount, description=""):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
        c.execute("UPDATE users SET balance = balance - ?, total_spent = total_spent + ? WHERE user_id = ?", (amount, amount, user_id))
        c.execute("INSERT INTO transactions (user_id, amount, type, description, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (user_id, amount, 'debit', description, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    @app_commands.command(name="balance", description="Check G-Coin balance")
    async def balance(self, interaction: discord.Interaction):
        bal = self.get_balance(interaction.user.id)
        embed = discord.Embed(title="💰 Your Balance", description=f"**{bal:,}** G-Coins", color=config.SHOP_COLOR)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="daily", description="Claim daily reward")
    async def daily(self, interaction: discord.Interaction):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT daily_claimed FROM users WHERE user_id = ?", (interaction.user.id,))
        result = c.fetchone()
        conn.close()

        now = datetime.now()
        if result and result[0]:
            last = datetime.fromisoformat(result[0])
            if (now - last).days < 1:
                next_claim = last + timedelta(days=1)
                time_left = next_claim - now
                await interaction.response.send_message(f"⏰ Come back in {int(time_left.total_seconds()//3600)}h {int((time_left.total_seconds()%3600)//60)}m", ephemeral=True)
                return

        reward = config.DAILY_REWARD
        if interaction.user.premium_since:
            reward += config.BOOSTER_BONUS

        self.add_balance(interaction.user.id, reward, "Daily reward")
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("UPDATE users SET daily_claimed = ? WHERE user_id = ?", (now.isoformat(), interaction.user.id))
        conn.commit()
        conn.close()

        embed = discord.Embed(title="🎁 Daily Reward!", description=f"You got **{reward:,}** G-Coins!", color=config.SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="pay", description="Send G-Coins")
    async def pay(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ Positive only.", ephemeral=True)
            return
        sender_bal = self.get_balance(interaction.user.id)
        if sender_bal < amount:
            await interaction.response.send_message(f"❌ You have {sender_bal:,} G-Coins.", ephemeral=True)
            return
        self.remove_balance(interaction.user.id, amount, f"Sent to {user}")
        self.add_balance(user.id, amount, f"From {interaction.user}")
        embed = discord.Embed(title="💸 Transfer Complete", description=f"Sent **{amount:,}** to {user.mention}!", color=config.SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leaderboard", description="Top balances")
    async def leaderboard(self, interaction: discord.Interaction):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
        results = c.fetchall()
        conn.close()
        if not results:
            await interaction.response.send_message("No data yet!", ephemeral=True)
            return
        embed = discord.Embed(title="🏆 Leaderboard", color=config.SHOP_COLOR)
        for i, (uid, bal) in enumerate(results):
            user = self.bot.get_user(uid)
            name = user.name if user else f"User {uid}"
            embed.add_field(name=f"{i+1}. {name}", value=f"{bal:,} G-Coins", inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
