import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import asyncio
import config

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green, emoji="🎫", custom_id="ticket_button")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"❌ You already have a ticket: {existing.mention}", ephemeral=True)
            return

        category = guild.get_channel(config.TICKET_CATEGORY)
        staff_role = guild.get_role(config.TICKET_STAFF_ROLE)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=f"Hello {user.mention}, a staff member will be with you shortly.",
            color=config.TICKET_COLOR,
            timestamp=datetime.now()
        )
        embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Opened", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)

        view = TicketControlView()
        await ticket_channel.send(content=staff_role.mention, embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Only staff can close tickets.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Closing ticket in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.blurple, emoji="👤", custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Only staff can claim.", ephemeral=True)
            return
        embed = discord.Embed(title="👤 Ticket Claimed", description=f"Handled by {interaction.user.mention}", color=config.SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)
        button.disabled = True
        await interaction.message.edit(view=self)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketView())
        self.bot.add_view(TicketControlView())

    @app_commands.command(name="ticket", description="Create a support ticket")
    async def ticket_cmd(self, interaction: discord.Interaction, reason: str = None):
        guild = interaction.guild
        user = interaction.user

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"❌ You already have a ticket: {existing.mention}", ephemeral=True)
            return

        category = guild.get_channel(config.TICKET_CATEGORY)
        staff_role = guild.get_role(config.TICKET_STAFF_ROLE)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        ticket_channel = await guild.create_text_channel(name=f"ticket-{user.name}", category=category, overwrites=overwrites)

        embed = discord.Embed(title="🎫 Support Ticket", description=f"Hello {user.mention}", color=config.TICKET_COLOR, timestamp=datetime.now())
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=True)

        view = TicketControlView()
        await ticket_channel.send(content=staff_role.mention, embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)

    @app_commands.command(name="ticketpanel", description="Send ticket panel (Staff)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎫 Support Center", description="Click below to open a ticket!", color=config.TICKET_COLOR)
        embed.add_field(name="Response Time", value="1-2 hours", inline=True)
        embed.set_footer(text="Obsidian Marketplace Support")
        view = TicketView()
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
