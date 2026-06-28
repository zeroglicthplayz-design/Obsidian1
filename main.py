import discord
from discord.ext import commands
import config
import os

intents = discord.Intents.all()

class ObsidianBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        self.synced = False

    async def setup_hook(self):
        cogs = [
            'cogs.help_system',
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
                print(f"Loaded {cog}")
            except Exception as e:
                print(f"Failed to load {cog}: {e}")

    async def on_ready(self):
        if not self.synced:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            try:
                synced = await self.tree.sync(guild=guild)
                print(f"Synced {len(synced)} slash commands to guild {config.GUILD_ID}")
            except Exception as e:
                print(f"Slash sync failed: {e}")
            self.synced = True

        print(f"{self.user.name} is online!")
        print(f"In {len(self.guilds)} guild(s)")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Obsidian Marketplace | !help"
            ),
            status=discord.Status.dnd
        )

bot = ObsidianBot()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Access Denied",
            description="You don't have permission to use this command.",
            color=config.COLOR_ERROR
        )
        await ctx.send(embed=embed, delete_after=10)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Missing Argument",
            description=f"Usage: `!{ctx.command.name} {ctx.command.signature}`",
            color=config.COLOR_WARNING
        )
        await ctx.send(embed=embed, delete_after=10)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title="Invalid Argument",
            description=str(error),
            color=config.COLOR_WARNING
        )
        await ctx.send(embed=embed, delete_after=10)
    else:
        print(f"Command error in {ctx.command}: {error}")

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("DISCORD_TOKEN not found! Set it in environment variables.")
else:
    bot.run(TOKEN)
