import discord
from discord.ext import commands
import asyncio
import config

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_cmd(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a user from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author.id != config.OWNER_ID:
            await ctx.send(embed=discord.Embed(title="Error", description="Cannot ban higher/equal role.", color=config.COLOR_ERROR))
            return
        await member.ban(reason=reason)
        embed = discord.Embed(title="User Banned", description=f"**User:** {member.mention}
**By:** {ctx.author.mention}
**Reason:** {reason}", color=config.COLOR_ERROR)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
        log_ch = ctx.guild.get_channel(config.MOD_LOG_CHANNEL)
        if log_ch: await log_ch.send(embed=embed)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_cmd(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a user from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author.id != config.OWNER_ID:
            await ctx.send(embed=discord.Embed(title="Error", description="Cannot kick higher/equal role.", color=config.COLOR_ERROR))
            return
        await member.kick(reason=reason)
        embed = discord.Embed(title="User Kicked", description=f"**User:** {member.mention}
**By:** {ctx.author.mention}
**Reason:** {reason}", color=config.COLOR_WARNING)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
        log_ch = ctx.guild.get_channel(config.MOD_LOG_CHANNEL)
        if log_ch: await log_ch.send(embed=embed)

    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute_cmd(self, ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        """Timeout/mute a user (e.g., 10m, 1h, 1d)"""
        if member.top_role >= ctx.author.top_role and ctx.author.id != config.OWNER_ID:
            await ctx.send(embed=discord.Embed(title="Error", description="Cannot mute higher/equal role.", color=config.COLOR_ERROR))
            return
        time_units = {"m": 60, "h": 3600, "d": 86400}
        unit = duration[-1].lower()
        if unit not in time_units:
            await ctx.send(embed=discord.Embed(title="Invalid Duration", description="Use: 10m, 1h, 1d", color=config.COLOR_WARNING))
            return
        try: amount = int(duration[:-1])
        except:
            await ctx.send(embed=discord.Embed(title="Invalid Duration", description="Use: 10m, 1h, 1d", color=config.COLOR_WARNING))
            return
        seconds = min(amount * time_units[unit], 2419200)
        await member.timeout(discord.utils.utcnow() + discord.timedelta(seconds=seconds), reason=reason)
        embed = discord.Embed(title="User Muted", description=f"**User:** {member.mention}
**Duration:** {duration}
**Reason:** {reason}
**By:** {ctx.author.mention}", color=config.COLOR_WARNING)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
        log_ch = ctx.guild.get_channel(config.MOD_LOG_CHANNEL)
        if log_ch: await log_ch.send(embed=embed)

    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute_cmd(self, ctx, member: discord.Member):
        """Remove timeout from a user"""
        await member.timeout(None, reason=f"Unmuted by {ctx.author}")
        await ctx.send(embed=discord.Embed(title="User Unmuted", description=f"**User:** {member.mention}
**By:** {ctx.author.mention}", color=config.COLOR_SUCCESS))

    @commands.command(name="warn")
    @commands.has_permissions(kick_members=True)
    async def warn_cmd(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a user (3 warnings = auto-kick)"""
        if member.id not in self.warnings: self.warnings[member.id] = []
        self.warnings[member.id].append({"reason": reason, "moderator": ctx.author.id, "time": discord.utils.utcnow()})
        warn_count = len(self.warnings[member.id])
        embed = discord.Embed(title="User Warned", description=f"**User:** {member.mention}
**Warning #{warn_count}**
**Reason:** {reason}
**By:** {ctx.author.mention}", color=config.COLOR_WARNING)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
        if warn_count >= 3:
            try:
                await member.kick(reason="Auto-kick: 3 warnings")
                await ctx.send(embed=discord.Embed(title="Auto-Kick", description=f"{member.mention} kicked for 3 warnings.", color=config.COLOR_ERROR))
                del self.warnings[member.id]
            except: pass

    @commands.command(name="warnings")
    @commands.has_permissions(kick_members=True)
    async def warnings_cmd(self, ctx, member: discord.Member):
        """View a user's warning history"""
        if member.id not in self.warnings or not self.warnings[member.id]:
            await ctx.send(embed=discord.Embed(title="Clean Record", description=f"{member.mention} has no warnings.", color=config.COLOR_SUCCESS))
            return
        embed = discord.Embed(title=f"Warnings for {member}", description=f"Total: {len(self.warnings[member.id])}", color=config.COLOR_WARNING)
        for i, warn in enumerate(self.warnings[member.id], 1):
            mod = ctx.guild.get_member(warn["moderator"])
            mod_name = mod.mention if mod else "Unknown"
            embed.add_field(name=f"Warning #{i}", value=f"**Reason:** {warn['reason']}
**By:** {mod_name}
**Time:** {discord.utils.format_dt(warn['time'], 'R')}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="clearwarns")
    @commands.has_permissions(administrator=True)
    async def clearwarns_cmd(self, ctx, member: discord.Member):
        """Clear all warnings from a user"""
        if member.id in self.warnings: del self.warnings[member.id]
        await ctx.send(embed=discord.Embed(title="Warnings Cleared", description=f"All warnings for {member.mention} cleared.", color=config.COLOR_SUCCESS))

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge_cmd(self, ctx, amount: int, member: discord.Member = None):
        """Delete messages in bulk (1-100)"""
        if amount < 1 or amount > 100:
            await ctx.send(embed=discord.Embed(title="Invalid Amount", description="Use 1-100.", color=config.COLOR_WARNING))
            return
        if member:
            deleted = await ctx.channel.purge(limit=amount, check=lambda m: m.author == member)
        else:
            deleted = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(embed=discord.Embed(title="Messages Purged", description=f"Deleted {len(deleted)} message(s).", color=config.COLOR_SUCCESS))
        await asyncio.sleep(5)
        await msg.delete()

async def setup(bot):
    await bot.add_cog(Moderation(bot))
