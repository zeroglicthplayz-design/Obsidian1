import discord
from discord.ext import commands
from discord.ui import View, Button
import config

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success, emoji="✅", custom_id="verify_btn")
    async def verify(self, interaction: discord.Interaction, button: Button):
        role = interaction.guild.get_role(config.VERIFIED_ROLE)
        if not role:
            await interaction.response.send_message("Verification role not configured.", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.response.send_message("Already verified!", ephemeral=True)
            return
        await interaction.user.add_roles(role)
        embed = discord.Embed(title="Verified", description=f"Welcome {interaction.user.mention}! Access granted.", color=config.COLOR_SUCCESS)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try:
            dm = discord.Embed(title="Welcome to Obsidian Marketplace", description="Thanks for verifying!

📜 Read rules
💰 Browse shop
🎫 Open ticket for support", color=config.COLOR_PRIMARY)
            await interaction.user.send(embed=dm)
        except: pass

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.get_channel(config.WELCOME_CHANNEL)
        if channel:
            embed = discord.Embed(title="New Member", description=f"Welcome {member.mention} to **Obsidian Marketplace**!

Member #{member.guild.member_count}
Please verify to access channels.", color=config.COLOR_PRIMARY)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

    @commands.command(name="verifypanel")
    @commands.has_permissions(manage_roles=True)
    async def verify_panel(self, ctx):
        """Send verification panel with button"""
        embed = discord.Embed(title="Verification Required", description="Click below to verify.

**Requirements:**
✅ Account 7+ days old
✅ No previous bans", color=config.COLOR_PRIMARY)
        embed.set_footer(text="Obsidian Marketplace")
        view = VerifyView()
        await ctx.send(embed=embed, view=view)
        await ctx.message.delete()

    @commands.command(name="welcomepanel")
    @commands.has_permissions(manage_channels=True)
    async def welcome_panel(self, ctx):
        """Send welcome info embed"""
        embed = discord.Embed(title="Welcome to Obsidian Marketplace", description="Premier Roblox asset marketplace.

**What We Offer:**
🌿 Vegetation Models
🏯 Chinese Theme Models
🚗 Car Models
🚀 Rocket Models

**Price Tiers:**
🥉 1K-4K Robux
🥈 5K-10K Robux
🥇 11K-15K Robux", color=config.COLOR_PRIMARY)
        embed.set_footer(text="Obsidian Marketplace")
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command(name="rulespanel")
    @commands.has_permissions(manage_channels=True)
    async def rules_panel(self, ctx):
        """Send rules embed"""
        embed = discord.Embed(title="Server Rules", description="By using this server, you agree to these rules.", color=config.COLOR_PRIMARY)
        rules = [
            ("1. Respect Everyone", "No harassment, hate speech, racism, or discrimination."),
            ("2. No Scamming", "All transactions documented. Scammers banned permanently."),
            ("3. No Spam", "No repeated messages, excessive emoji, or mass mentions."),
            ("4. No NSFW", "Keep content clean. Roblox-related marketplace."),
            ("5. No Advertising", "No promoting other servers without staff approval."),
            ("6. Use Channels Correctly", "Post assets in correct price tier and category."),
            ("7. No Alts", "Alternate accounts to bypass bans not allowed."),
            ("8. Follow Roblox ToS", "All transactions comply with Roblox Terms of Service."),
            ("9. Staff Final Say", "Do not argue with moderator decisions."),
            ("10. English Only", "Keep public communication in English."),
        ]
        for title, desc in rules:
            embed.add_field(name=title, value=desc, inline=False)
        embed.add_field(name="Disclaimer", value="Obsidian Marketplace is not affiliated with Roblox Corporation. Not responsible for peer-to-peer transaction losses. Always verify sellers before payment.", inline=False)
        embed.set_footer(text="Obsidian Marketplace")
        await ctx.send(embed=embed)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Welcome(bot))
