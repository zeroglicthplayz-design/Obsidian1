import discord
from discord.ext import commands
import config

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        log_ch = message.guild.get_channel(config.MESSAGE_LOG_CHANNEL)
        if not log_ch:
            return
        embed = discord.Embed(title="Message Deleted", description=f"**Author:** {message.author.mention}
**Channel:** {message.channel.mention}", color=config.COLOR_ERROR, timestamp=message.created_at)
        if message.content:
            embed.add_field(name="Content", value=message.content[:1024], inline=False)
        if message.attachments:
            embed.add_field(name="Attachments", value="
".join([a.url for a in message.attachments[:5]]), inline=False)
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        log_ch = before.guild.get_channel(config.MESSAGE_LOG_CHANNEL)
        if not log_ch:
            return
        embed = discord.Embed(title="Message Edited", description=f"**Author:** {before.author.mention}
**Channel:** {before.channel.mention}
[Jump]({after.jump_url})", color=config.COLOR_WARNING)
        embed.add_field(name="Before", value=before.content[:1024] or "*Empty*", inline=False)
        embed.add_field(name="After", value=after.content[:1024] or "*Empty*", inline=False)
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        log_ch = member.guild.get_channel(config.MOD_LOG_CHANNEL)
        if not log_ch:
            return
        age = (discord.utils.utcnow() - member.created_at).days
        embed = discord.Embed(title="Member Joined", description=f"**User:** {member.mention}
**ID:** `{member.id}`
**Account Age:** {age} days", color=config.COLOR_SUCCESS)
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        log_ch = member.guild.get_channel(config.MOD_LOG_CHANNEL)
        if not log_ch:
            return
        embed = discord.Embed(title="Member Left", description=f"**User:** {member.mention}
**ID:** `{member.id}`", color=config.COLOR_ERROR)
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles == after.roles:
            return
        log_ch = before.guild.get_channel(config.MOD_LOG_CHANNEL)
        if not log_ch:
            return
        added = [r for r in after.roles if r not in before.roles]
        removed = [r for r in before.roles if r not in after.roles]
        if added or removed:
            embed = discord.Embed(title="Role Update", description=f"**User:** {before.mention}", color=config.COLOR_INFO)
            if added:
                embed.add_field(name="Added", value="
".join([r.mention for r in added]), inline=False)
            if removed:
                embed.add_field(name="Removed", value="
".join([r.mention for r in removed]), inline=False)
            await log_ch.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
