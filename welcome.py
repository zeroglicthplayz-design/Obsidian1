import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import config

class WelcomeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, emoji="✅", custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        verified_role = interaction.guild.get_role(config.VERIFIED_ROLE)
        if not verified_role:
            await interaction.response.send_message("❌ Verified role not set.", ephemeral=True)
            return
        if verified_role in interaction.user.roles:
            await interaction.response.send_message("✅ Already verified!", ephemeral=True)
            return

        await interaction.user.add_roles(verified_role)

        welcome_channel = interaction.guild.get_channel(config.WELCOME_CHANNEL)
        if welcome_channel:
            embed = discord.Embed(title="👋 New Member!", description=f"Welcome {interaction.user.mention}!", color=config.SUCCESS_COLOR, timestamp=datetime.now())
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name="Member Count", value=f"{interaction.guild.member_count}", inline=True)
            await welcome_channel.send(embed=embed)

        try:
            dm_embed = discord.Embed(title="🖤 Welcome!", description=config.WELCOME_MESSAGE.format(user=interaction.user.mention, rules=config.RULES_CHANNEL), color=config.EMBED_COLOR)
            await interaction.user.send(embed=dm_embed)
        except:
            pass

        await interaction.response.send_message("✅ Verified! Welcome to Obsidian Marketplace.", ephemeral=True)

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(WelcomeView())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            embed = discord.Embed(title="🖤 Welcome!", description=f"Hey {member.mention}!", color=config.EMBED_COLOR)
            embed.add_field(name="Next Steps", value="1. Verify\n2. Read rules\n3. Browse shop!", inline=False)
            await member.send(embed=embed)
        except:
            pass

    @app_commands.command(name="verifypanel", description="Send verification panel")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def verify_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(title="✅ Verification", description="Click to verify!", color=config.SUCCESS_COLOR)
        view = WelcomeView()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="rulespanel", description="Send rules panel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def rules_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📜 Server Rules", description="Breaking rules = warnings, mutes, kicks, or bans.", color=config.WARNING_COLOR)
        rules = [
            ("1. Respect Everyone", "No harassment, hate speech, racism, sexism."),
            ("2. No Scamming", "Scamming = instant permanent ban."),
            ("3. No Spam", "No repeated messages or excessive emoji."),
            ("4. No NSFW", "Keep it clean. No gore or explicit content."),
            ("5. No Advertising", "No promoting other servers without approval."),
            ("6. Use Channels Correctly", "Post in correct categories."),
            ("7. No Alts", "Alt accounts to bypass bans = banned."),
            ("8. Follow Roblox ToS", "All assets must comply with Roblox Terms."),
            ("9. Staff Have Final Say", "Don't argue with mod decisions."),
            ("10. English Only", "Keep public chat in English."),
        ]
        for title, desc in rules:
            embed.add_field(name=title, value=desc, inline=False)
        embed.add_field(name="⚠️ Disclaimer", value="Not affiliated with Roblox. Not responsible for P2P losses.", inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
