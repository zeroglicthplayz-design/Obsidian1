import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import config

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}

    @app_commands.command(name="ban", description="Ban a user")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason", delete_days: int = 0):
        if user.top_role >= interaction.user.top_role and interaction.user.id != config.OWNER_ID:
            await interaction.response.send_message("❌ Can't ban higher role.", ephemeral=True)
            return
        try:
            embed = discord.Embed(title=f"🔨 Banned from {interaction.guild.name}", description=f"Reason: {reason}", color=config.ERROR_COLOR)
            await user.send(embed=embed)
        except:
            pass
        await user.ban(reason=reason, delete_message_days=delete_days)
        await interaction.response.send_message(f"✅ {user.mention} banned.")

    @app_commands.command(name="kick", description="Kick a user")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
        if user.top_role >= interaction.user.top_role and interaction.user.id != config.OWNER_ID:
            await interaction.response.send_message("❌ Can't kick higher role.", ephemeral=True)
            return
        try:
            embed = discord.Embed(title=f"👢 Kicked from {interaction.guild.name}", description=f"Reason: {reason}", color=config.WARNING_COLOR)
            await user.send(embed=embed)
        except:
            pass
        await user.kick(reason=reason)
        await interaction.response.send_message(f"✅ {user.mention} kicked.")

    @app_commands.command(name="mute", description="Mute a user")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str = "No reason"):
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        unit = duration[-1].lower()
        if unit not in time_units:
            await interaction.response.send_message("❌ Use: 10m, 1h, 1d", ephemeral=True)
            return
        try:
            amount = int(duration[:-1])
        except:
            await interaction.response.send_message("❌ Invalid duration.", ephemeral=True)
            return
        seconds = amount * time_units[unit]
        if seconds > 2419200:
            seconds = 2419200
        timeout_until = datetime.now() + timedelta(seconds=seconds)
        await user.timeout(timeout_until, reason=reason)
        await interaction.response.send_message(f"🔇 {user.mention} muted for {duration}.")

    @app_commands.command(name="unmute", description="Unmute a user")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, user: discord.Member):
        await user.timeout(None)
        await interaction.response.send_message(f"🔊 {user.mention} unmuted.")

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.checks.has_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        guild_id = interaction.guild.id
        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
        if user.id not in self.warnings[guild_id]:
            self.warnings[guild_id][user.id] = []

        self.warnings[guild_id][user.id].append({'moderator': interaction.user.id, 'reason': reason, 'timestamp': datetime.now()})
        warn_count = len(self.warnings[guild_id][user.id])

        if warn_count >= 3:
            await user.kick(reason=f"Auto-kick: {warn_count} warnings")
            action = f"Auto-kicked ({warn_count} warnings)"
        elif warn_count == 2:
            await user.timeout(datetime.now() + timedelta(hours=1), reason=f"Auto-mute: {warn_count} warnings")
            action = f"Auto-muted 1h (warning {warn_count}/3)"
        else:
            action = f"Warning {warn_count}/3"

        await interaction.response.send_message(f"⚠️ {user.mention} warned. {action}")

    @app_commands.command(name="warnings", description="View warnings")
    @app_commands.checks.has_permissions(kick_members=True)
    async def warnings_cmd(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        guild_id = interaction.guild.id
        user_warnings = self.warnings.get(guild_id, {}).get(user.id, [])
        if not user_warnings:
            await interaction.response.send_message(f"✅ {user.mention} has no warnings.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Warnings for {user}", description=f"Total: {len(user_warnings)}", color=config.WARNING_COLOR)
        for i, warn in enumerate(user_warnings[-5:], 1):
            mod = self.bot.get_user(warn['moderator'])
            embed.add_field(name=f"Warning #{i}", value=f"Reason: {warn['reason']}\nBy: {mod.name if mod else 'Unknown'}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="purge", description="Delete messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int, user: discord.Member = None):
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be 1-100.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        if user:
            deleted = await interaction.channel.purge(limit=amount, check=lambda m: m.author.id == user.id)
        else:
            deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🗑️ Deleted {len(deleted)} messages.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
