import discord
from discord.ext import commands
import re
import config

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_cache = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content_lower = message.content.lower()

        # Scam detection
        for keyword in config.SCAM_KEYWORDS:
            if keyword in content_lower:
                try:
                    await message.delete()
                    embed = discord.Embed(title="Scam Detected", description=f"{message.author.mention}, scam content deleted.", color=config.COLOR_ERROR)
                    await message.channel.send(embed=embed, delete_after=10)
                    if any(k in content_lower for k in ["stealer", "grabber", "token logger"]):
                        await message.author.ban(reason="AutoMod: Malware content")
                        log_ch = message.guild.get_channel(config.MOD_LOG_CHANNEL)
                        if log_ch:
                            await log_ch.send(embed=discord.Embed(title="Auto-Ban", description=f"User: {message.author.mention} | Reason: Malware", color=config.COLOR_ERROR))
                    return
                except:
                    pass

        # Invite blocking
        if re.search(config.INVITE_PATTERN, message.content):
            if not message.author.guild_permissions.manage_channels:
                try:
                    await message.delete()
                    embed = discord.Embed(title="Invite Blocked", description=f"{message.author.mention}, external invites are not allowed.", color=config.COLOR_WARNING)
                    await message.channel.send(embed=embed, delete_after=10)
                    return
                except:
                    pass

        # Spam detection
        author_id = message.author.id
        if author_id not in self.spam_cache:
            self.spam_cache[author_id] = []
        self.spam_cache[author_id].append(message.created_at)
        self.spam_cache[author_id] = [t for t in self.spam_cache[author_id] if (message.created_at - t).total_seconds() < config.SPAM_INTERVAL]

        if len(self.spam_cache[author_id]) >= config.SPAM_THRESHOLD:
            try:
                await message.author.timeout(discord.utils.utcnow() + discord.timedelta(minutes=10), reason="AutoMod: Spam")
                embed = discord.Embed(title="Auto-Mute", description=f"{message.author.mention} muted 10m for spam.", color=config.COLOR_WARNING)
                await message.channel.send(embed=embed, delete_after=10)
                log_ch = message.guild.get_channel(config.MOD_LOG_CHANNEL)
                if log_ch:
                    await log_ch.send(embed=embed)
            except:
                pass

        # Mass mention
        if len(message.mentions) >= config.MASS_MENTION_LIMIT:
            try:
                await message.delete()
                embed = discord.Embed(title="Mass Mention Blocked", description=f"{message.author.mention}, don't mass mention.", color=config.COLOR_WARNING)
                await message.channel.send(embed=embed, delete_after=10)
            except:
                pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        account_age = (discord.utils.utcnow() - member.created_at).days
        if account_age < config.MIN_ACCOUNT_AGE_DAYS:
            try:
                await member.kick(reason=f"AutoMod: Account too new ({account_age} days)")
                log_ch = member.guild.get_channel(config.MOD_LOG_CHANNEL)
                if log_ch:
                    await log_ch.send(embed=discord.Embed(title="Alt Account Kicked", description=f"User: {member.mention} | Age: {account_age} days", color=config.COLOR_ERROR))
            except:
                pass

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
