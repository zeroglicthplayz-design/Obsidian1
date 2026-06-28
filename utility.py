import discord
from discord.ext import commands
import config

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vouches = {}

    @commands.command(name="ping")
    async def ping_cmd(self, ctx):
        """Check bot latency"""
        latency = round(self.bot.latency * 1000)
        status = "🟢 Good" if latency < 200 else "🟡 Okay" if latency < 500 else "🔴 Slow"
        color = config.COLOR_SUCCESS if latency < 200 else config.COLOR_WARNING if latency < 500 else config.COLOR_ERROR
        await ctx.send(embed=discord.Embed(title="Pong", description=f"**Latency:** `{latency}ms`
**Status:** {status}", color=color))

    @commands.command(name="userinfo")
    async def userinfo_cmd(self, ctx, member: discord.Member = None):
        """Get detailed user information"""
        target = member or ctx.author
        roles = [r.mention for r in target.roles if r != ctx.guild.default_role]
        embed = discord.Embed(title=f"{target}", color=config.COLOR_PRIMARY)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="Nickname", value=target.nick or "None", inline=True)
        embed.add_field(name="Bot", value="Yes" if target.bot else "No", inline=True)
        embed.add_field(name="Joined Server", value=discord.utils.format_dt(target.joined_at, 'R') if target.joined_at else "Unknown", inline=True)
        embed.add_field(name="Account Created", value=discord.utils.format_dt(target.created_at, 'R'), inline=True)
        embed.add_field(name="Top Role", value=target.top_role.mention, inline=True)
        embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join(roles[:10]) or "None", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo")
    async def serverinfo_cmd(self, ctx):
        """Get server statistics"""
        guild = ctx.guild
        embed = discord.Embed(title=f"{guild.name}", description=f"**ID:** `{guild.id}`
**Owner:** {guild.owner.mention if guild.owner else 'Unknown'}", color=config.COLOR_PRIMARY)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Members", value=f"`{guild.member_count}`", inline=True)
        embed.add_field(name="Channels", value=f"`{len(guild.channels)}`", inline=True)
        embed.add_field(name="Roles", value=f"`{len(guild.roles)}`", inline=True)
        embed.add_field(name="Boosts", value=f"`{guild.premium_subscription_count}` (Level {guild.premium_tier})", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, 'R'), inline=True)
        embed.add_field(name="Verification", value=str(guild.verification_level).title(), inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.command(name="vouch")
    async def vouch_cmd(self, ctx, member: discord.Member, *, message: str):
        """Leave a review/vouch for a user"""
        if member == ctx.author:
            await ctx.send(embed=discord.Embed(title="Error", description="Can't vouch for yourself.", color=config.COLOR_ERROR))
            return
        if member.id not in self.vouches:
            self.vouches[member.id] = []
        self.vouches[member.id].append({"from": ctx.author.id, "message": message, "time": discord.utils.utcnow()})
        vouch_ch = ctx.guild.get_channel(config.VOUCH_CHANNEL)
        if vouch_ch:
            await vouch_ch.send(embed=discord.Embed(title="New Vouch", description=f"**For:** {member.mention}
**From:** {ctx.author.mention}
**Message:** {message}", color=config.COLOR_SUCCESS))
        await ctx.send(embed=discord.Embed(title="Vouch Submitted", description=f"Your vouch for {member.mention} recorded.", color=config.COLOR_SUCCESS))

    @commands.command(name="vouches")
    async def vouches_cmd(self, ctx, member: discord.Member = None):
        """View reviews for a user"""
        target = member or ctx.author
        if target.id not in self.vouches or not self.vouches[target.id]:
            await ctx.send(embed=discord.Embed(title="Vouches", description=f"{target.mention} has no vouches.", color=config.COLOR_PRIMARY))
            return
        embed = discord.Embed(title=f"Vouches for {target}", description=f"Total: {len(self.vouches[target.id])}", color=config.COLOR_PRIMARY)
        for i, vouch in enumerate(self.vouches[target.id][-5:], 1):
            user = ctx.guild.get_member(vouch["from"])
            name = user.mention if user else "Unknown"
            embed.add_field(name=f"Vouch #{i}", value=f"**From:** {name}
**Message:** {vouch['message']}
**Time:** {discord.utils.format_dt(vouch['time'], 'R')}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="avatar")
    async def avatar_cmd(self, ctx, member: discord.Member = None):
        """Get a user's avatar image"""
        target = member or ctx.author
        embed = discord.Embed(title=f"{target}'s Avatar", color=config.COLOR_PRIMARY)
        embed.set_image(url=target.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.command(name="poll")
    async def poll_cmd(self, ctx, question: str, *options):
        """Create a poll with up to 5 options"""
        if len(options) < 2:
            await ctx.send(embed=discord.Embed(title="Invalid Poll", description="Provide at least 2 options.
Usage: `!poll "Question" opt1 opt2 ...`", color=config.COLOR_WARNING))
            return
        options = options[:5]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        embed = discord.Embed(title="Poll", description=f"**{question}**", color=config.COLOR_PRIMARY)
        for i, opt in enumerate(options):
            embed.add_field(name=f"{emojis[i]} {opt}", value="Vote below!", inline=False)
        embed.set_footer(text=f"Poll by {ctx.author}")
        msg = await ctx.send(embed=embed)
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

    @commands.command(name="announce")
    @commands.has_permissions(administrator=True)
    async def announce_cmd(self, ctx, channel: discord.TextChannel, *, message: str):
        """Send a staff announcement embed"""
        embed = discord.Embed(title="Announcement", description=message, color=config.COLOR_PRIMARY)
        embed.set_footer(text=f"Posted by {ctx.author}")
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)
        await ctx.send(f"Announcement sent to {channel.mention}", delete_after=5)

    @commands.command(name="embed")
    @commands.has_permissions(administrator=True)
    async def embed_cmd(self, ctx, channel: discord.TextChannel, title: str, *, description: str):
        """Send a custom embed"""
        embed = discord.Embed(title=title, description=description, color=config.COLOR_PRIMARY)
        embed.set_footer(text=f"Posted by {ctx.author}")
        await channel.send(embed=embed)
        await ctx.send(f"Embed sent to {channel.mention}", delete_after=5)

    @commands.command(name="say")
    @commands.has_permissions(administrator=True)
    async def say_cmd(self, ctx, channel: discord.TextChannel, *, message: str):
        """Make the bot send a message"""
        await channel.send(message)
        await ctx.message.delete()

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_cmd(self, ctx):
        """Sync slash commands (Owner only)"""
        guild = discord.Object(id=config.GUILD_ID)
        self.bot.tree.copy_global_to(guild=guild)
        synced = await self.bot.tree.sync(guild=guild)
        await ctx.send(embed=discord.Embed(title="Commands Synced", description=f"Synced `{len(synced)}` slash commands.", color=config.COLOR_SUCCESS))

async def setup(bot):
    await bot.add_cog(Utility(bot))
