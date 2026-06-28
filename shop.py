import discord
from discord.ext import commands
import sqlite3
import config

SHOP_DB = "shop.db"

def get_shop_db():
    conn = sqlite3.connect(SHOP_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_shop_db():
    conn = get_shop_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            tier TEXT NOT NULL,
            category TEXT NOT NULL,
            seller_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_shop_db()

    @commands.command(name="shop")
    async def shop_cmd(self, ctx, tier: str = None, category: str = None):
        """Browse items by tier and category"""
        conn = get_shop_db()
        if tier and category:
            cur = conn.execute("SELECT * FROM items WHERE tier = ? AND category = ?", (tier.lower(), category.lower()))
        elif tier:
            cur = conn.execute("SELECT * FROM items WHERE tier = ?", (tier.lower(),))
        else:
            cur = conn.execute("SELECT * FROM items")
        items = cur.fetchall()
        conn.close()

        if not items:
            embed = discord.Embed(title="Shop", description="No items found. Use `!additem` to add products.

**Tiers:** `1k-4k`, `5k-10k`, `11k-15k`
**Categories:** `vegetation`, `chinese`, `cars`, `rockets`", color=config.COLOR_PRIMARY)
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title="Obsidian Marketplace", description=f"{'Tier: ' + tier.upper() if tier else 'All Items'} {'| Category: ' + category.title() if category else ''}", color=config.COLOR_PRIMARY)
        for item in items:
            seller = ctx.guild.get_member(item["seller_id"])
            seller_name = seller.mention if seller else "Unknown"
            embed.add_field(name=f"#{item['id']} {item['name']} - `{item['price']:,}` Robux", value=f"{item['description'] or 'No description'}
**Tier:** {item['tier'].upper()} | **Category:** {item['category'].title()}
**Seller:** {seller_name}", inline=False)
        embed.set_footer(text="Use !buy <item_id> to purchase")
        await ctx.send(embed=embed)

    @commands.command(name="buy")
    async def buy_cmd(self, ctx, item_id: int):
        """Purchase an item from the shop"""
        conn = get_shop_db()
        cur = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        item = cur.fetchone()
        conn.close()
        if not item:
            await ctx.send(embed=discord.Embed(title="Item Not Found", description="That item doesn't exist.", color=config.COLOR_ERROR))
            return
        embed = discord.Embed(title="Purchase Request", description=f"**Item:** {item['name']}
**Price:** `{item['price']:,}` Robux

Open a ticket to complete purchase.", color=config.COLOR_PRIMARY)
        embed.set_footer(text="Use !ticket to open support")
        await ctx.send(embed=embed)

    @commands.command(name="inventory")
    async def inventory_cmd(self, ctx):
        """View your purchased items"""
        embed = discord.Embed(title="Inventory", description="Your purchased items appear here.

*Purchases handled via tickets.*", color=config.COLOR_PRIMARY)
        await ctx.send(embed=embed)

    @commands.command(name="additem")
    @commands.has_permissions(administrator=True)
    async def additem_cmd(self, ctx, name: str, price: int, tier: str, category: str, *, description: str = "No description"):
        """Add an item to the shop (Admin only)"""
        conn = get_shop_db()
        conn.execute("INSERT INTO items (name, description, price, tier, category, seller_id) VALUES (?, ?, ?, ?, ?, ?)", (name, description, price, tier.lower(), category.lower(), ctx.author.id))
        conn.commit()
        item_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        await ctx.send(embed=discord.Embed(title="Item Added", description=f"**#{item_id}** {name}
**Price:** `{price:,}` Robux
**Tier:** {tier.upper()}
**Category:** {category.title()}", color=config.COLOR_SUCCESS))

    @commands.command(name="removeitem")
    @commands.has_permissions(administrator=True)
    async def removeitem_cmd(self, ctx, item_id: int):
        """Remove an item from the shop (Admin only)"""
        conn = get_shop_db()
        cur = conn.execute("SELECT name FROM items WHERE id = ?", (item_id,))
        item = cur.fetchone()
        if not item:
            await ctx.send(embed=discord.Embed(title="Item Not Found", description="That item doesn't exist.", color=config.COLOR_ERROR))
            conn.close()
            return
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        await ctx.send(embed=discord.Embed(title="Item Removed", description=f"**#{item_id}** {item['name']} removed.", color=config.COLOR_SUCCESS))

async def setup(bot):
    await bot.add_cog(Shop(bot))
