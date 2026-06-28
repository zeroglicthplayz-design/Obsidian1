import discord
from discord.ext import commands
import asyncio
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from flask import Flask
    from threading import Thread
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("WARNING: Flask not installed.")

if FLASK_AVAILABLE:
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "Obsidian Marketplace Bot is running!", 200

    @app.route('/health')
    def health():
        return {"status": "ok", "bot": bot.user.name if bot.user else "offline"}, 200

    def run_flask():
        app.run(host='0.0.0.0', port=10000)

class ObsidianBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None,
            case_insensitive=True
        )

    async def setup_hook(self):
        print("Starting cog loading...")
        cogs = [
            'cogs.tickets',
            'cogs.automod', 
            'cogs.moderation',
            'cogs.welcome',
            'cogs.economy',
            'cogs.shop',
            'cogs.logs',
            'cogs.utility'
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

        print("Syncing slash commands...")
        import config
        guild = discord.Object(id=config.GUILD_ID)
        try:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"✅ Synced {len(synced)} slash commands to guild {config.GUILD_ID}")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")

    async def on_ready(self):
        print(f"🤖 {self.user} is online!")
        print(f"📊 In {len(self.guilds)} guilds")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Obsidian Marketplace"
            )
        )

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing: `{error.param.name}`", delete_after=5)
        elif isinstance(error, commands.CommandNotFound):
            return
        else:
            print(f"Error: {error}")

bot = ObsidianBot()

@bot.command(name="sync")
@commands.is_owner()
async def sync_command(ctx):
    """Manual sync slash commands"""
    import config
    guild = discord.Object(id=config.GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)
    await ctx.send(f"✅ Synced {len(synced)} slash commands! Type `/` to see them.")

if FLASK_AVAILABLE:
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask server started on port 10000")

bot.run(os.getenv('DISCORD_TOKEN'))
