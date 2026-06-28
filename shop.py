import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import sqlite3
import config

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS shop_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT,
            price INTEGER, category TEXT, tier TEXT, image_url TEXT,
            stock INTEGER DEFAULT -1, created_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, item_id INTEGER,
            price_paid INTEGER, timestamp TEXT)""")
        conn.commit()
        conn.close()

    def get_items(self, tier=None, category=None):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        if tier and category:
            c.execute("SELECT * FROM shop_items WHERE tier = ? AND category = ? ORDER BY price", (tier, category))
        elif tier:
            c.execute("SELECT * FROM shop_items WHERE tier = ? ORDER BY price", (tier,))
        elif category:
            c.execute("SELECT * FROM shop_items WHERE category = ? ORDER BY price", (category,))
        else:
            c.execute("SELECT * FROM shop_items ORDER BY tier, price")
        items = c.fetchall()
        conn.close()
        return items

    @app_commands.command(name="shop", description="Browse the shop")
    @app_commands.choices(tier=[
        app_commands.Choice(name="1K-4K Robux", value="1k-4k"),
        app_commands.Choice(name="5K-10K Robux", value="5k-10k"),
        app_commands.Choice(name="11K-15K Robux", value="11k-15k")
    ])
    @app_commands.choices(category=[
        app_commands.Choice(name="Vegetation", value="vegetation-models"),
        app_commands.Choice(name="Chinese Theme", value="chinese-theme-models"),
        app_commands.Choice(name="Cars", value="car-models"),
        app_commands.Choice(name="Rockets", value="rocket-models")
    ])
    async def shop_cmd(self, interaction: discord.Interaction, tier: app_commands.Choice[str] = None, category: app_commands.Choice[str] = None):
        items = self.get_items(tier.value if tier else None, category.value if category else None)
        if not items:
            await interaction.response.send_message("No items found.", ephemeral=True)
            return
        embed = discord.Embed(title="Obsidian Marketplace", description="Browse premium Roblox models.", color=config.SHOP_COLOR)
        for item in items[:10]:
            item_id, name, desc, price, cat, t, img, stock, created = item
            stock_text = f" | Stock: {stock}" if stock >= 0 else ""
            embed.add_field(name=f"#{item_id} {name} - {price:,} G-Coins", value=f"{desc}{stock_text}", inline=False)
        embed.set_footer(text="Use /buy [item-id] to purchase")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Purchase an item")
    async def buy(self, interaction: discord.Interaction, item_id: int):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM shop_items WHERE id = ?", (item_id,))
        item = c.fetchone()
        if not item:
            await interaction.response.send_message("Item not found.", ephemeral=True)
            conn.close()
            return
        item_id, name, desc, price, category, tier, image_url, stock, created = item
        if stock == 0:
            await interaction.response.send_message("Out of stock!", ephemeral=True)
            conn.close()
            return
        c.execute("SELECT balance FROM users WHERE user_id = ?", (interaction.user.id,))
        result = c.fetchone()
        balance = result[0] if result else 0
        if balance < price:
            await interaction.response.send_message(f"❌ You have {balance:,}. Price: {price:,}", ephemeral=True)
            conn.close()
            return
        c.execute("UPDATE users SET balance = balance - ?, total_spent = total_spent + ? WHERE user_id = ?", (price, price, interaction.user.id))
        c.execute("INSERT INTO purchases (user_id, item_id, price_paid, timestamp) VALUES (?, ?, ?, ?)", (interaction.user.id, item_id, price, datetime.now().isoformat()))
        if stock > 0:
            c.execute("UPDATE shop_items SET stock = stock - 1 WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        embed = discord.Embed(title="Purchase Complete!", description=f"You bought **{name}** for **{price:,}** G-Coins!", color=config.SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="inventory", description="View your items")
    async def inventory(self, interaction: discord.Interaction):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""SELECT p.item_id, s.name, s.category, s.tier, p.price_paid, p.timestamp 
                     FROM purchases p JOIN shop_items s ON p.item_id = s.id WHERE p.user_id = ? ORDER BY p.timestamp DESC""", (interaction.user.id,))
        purchases = c.fetchall()
        conn.close()
        if not purchases:
            await interaction.response.send_message("No purchases yet!", ephemeral=True)
            return
        embed = discord.Embed(title="Your Inventory", description=f"{len(purchases)} items", color=config.SHOP_COLOR)
        for item_id, name, cat, tier, price, ts in purchases[:10]:
            date = datetime.fromisoformat(ts).strftime('%Y-%m-%d')
            embed.add_field(name=f"#{item_id} {name}", value=f"{tier} | {price:,} G-Coins | {date}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="additem", description="Add item to shop (Admin)")
    @app_commands.checks.has_permissions(administrator=True)
    async def additem(self, interaction: discord.Interaction, name: str, description: str, price: int, 
                      tier: app_commands.Choice[str], category: app_commands.Choice[str], stock: int = -1):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO shop_items (name, description, price, category, tier, stock, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (name, description, price, category.value, tier.value, stock, datetime.now().isoformat()))
        item_id = c.lastrowid
        conn.commit()
        conn.close()
        embed = discord.Embed(title="Item Added", description=f"**{name}** added!", color=config.SUCCESS_COLOR)
        embed.add_field(name="ID", value=str(item_id))
        embed.add_field(name="Price", value=f"{price:,} G-Coins")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Shop(bot))
