import discord
from discord.ext import commands
from datetime import datetime
import config

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        log_channel = message.guild.get_channel(config.MESSAGE_LOG_CHANNEL)
        if not log_channel:
            return
        embed = discord.Embed(title="Message Deleted", description=f"{message.author.mention}", color=config.ERROR_COLOR, timestamp=datetime.now())
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        if message.content:
            embed.add_field(name="Content", value=message.content[:1024], inline=False)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        log_channel = before.guild.get_channel(config.MESSAGE_LOG_CHANNEL)
        if not log_channel:
            return
        embed = discord.Embed(title="Message Edited", description=f"{before.author.mention}", color=config.WARNING_COLOR, timestamp=datetime.now())
        embed.add_field(name="Before", value=before.content[:1024] or "Empty", inline=False)
        embed.add_field(name="After", value=after.content[:1024] or "Empty", inline=False)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        log_channel = member.guild.get_channel(config.MOD_LOG_CHANNEL)
        if not log_channel:
            return
        embed = discord.Embed(title="Member Joined", description=f"{member.mention}", color=config.SUCCESS_COLOR, timestamp=datetime.now())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Account Age", value=f"{(datetime.now() - member.created_at).days} days", inline=True)
        embed.add_field(name="Members", value=f"{member.guild.member_count}", inline=True)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        log_channel = member.guild.get_channel(config.MOD_LOG_CHANNEL)
        if not log_channel:
            return
        embed = discord.Embed(title="Member Left", description=f"{member.mention}", color=config.ERROR_COLOR, timestamp=datetime.now())
        await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
