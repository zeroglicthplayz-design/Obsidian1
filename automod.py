import discord
from discord.ext import commands
from datetime import datetime, timedelta
import re
import config

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_cache = {}
        self.mention_cache = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content_lower = message.content.lower()
        user_id = message.author.id
        now = datetime.now()

        # Account age check
        account_age = (now - message.author.created_at).days
        if account_age < config.MIN_ACCOUNT_AGE:
            await message.delete()
            try:
                await message.author.send(f"Your account must be {config.MIN_ACCOUNT_AGE}+ days old.")
            except:
                pass
            await message.author.kick(reason=f"Account too new ({account_age} days)")
            return

        # Scam keywords = instant ban
        for keyword in config.SCAM_KEYWORDS:
            if keyword in content_lower:
                await message.delete()
                try:
                    await message.author.ban(reason=f"Scam: {keyword}")
                except:
                    pass
                log_channel = message.guild.get_channel(config.MOD_LOG_CHANNEL)
                if log_channel:
                    embed = discord.Embed(title="🔨 Auto Ban", description=f"{message.author.mention} banned for scam.", color=config.ERROR_COLOR)
                    await log_channel.send(embed=embed)
                return

        # Suspicious keywords = warn + delete
        for keyword in config.SUSPICIOUS_KEYWORDS:
            if keyword in content_lower:
                await message.delete()
                log_channel = message.guild.get_channel(config.MOD_LOG_CHANNEL)
                if log_channel:
                    embed = discord.Embed(title="⚠️ Suspicious Content", description=f"{message.author.mention}", color=config.WARNING_COLOR)
                    await log_channel.send(embed=embed)
                return

        # Invite links
        invite_pattern = r'discord\.gg/[a-zA-Z0-9]+|discord\.com/invite/[a-zA-Z0-9]+'
        if re.search(invite_pattern, content_lower):
            if not message.author.guild_permissions.manage_channels:
                await message.delete()
                return

        # @everyone/@here
        if '@everyone' in message.content or '@here' in message.content:
            if not message.author.guild_permissions.mention_everyone:
                await message.delete()
                return

        # Mass mentions
        mention_count = len(message.mentions) + len(message.role_mentions)
        if mention_count >= config.MENTION_LIMIT:
            if not message.author.guild_permissions.mention_everyone:
                await message.delete()
                return

        # Anti-spam
        if user_id not in self.message_cache:
            self.message_cache[user_id] = []
        self.message_cache[user_id].append((now, message.channel.id))
        self.message_cache[user_id] = [(t, c) for t, c in self.message_cache[user_id] if (now - t).seconds < config.SPAM_INTERVAL]

        if len(self.message_cache[user_id]) >= config.SPAM_THRESHOLD:
            async for msg in message.channel.history(limit=50):
                if msg.author.id == user_id and (now - msg.created_at).seconds < 10:
                    await msg.delete()
            muted_role = message.guild.get_role(config.MUTED_ROLE)
            if muted_role:
                await message.author.add_roles(muted_role)
                await asyncio.sleep(600)
                await message.author.remove_roles(muted_role)
            self.message_cache[user_id] = []

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        await self.on_message(after)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
