import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
import asyncio
import config

class TicketModal(Modal, title="Open Support Ticket"):
    reason = TextInput(
        label="What do you need help with?",
        style=discord.TextStyle.paragraph,
        placeholder="Describe your issue or request...",
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        category = guild.get_channel(config.TICKET_CATEGORY)
        staff_role = guild.get_role(config.TICKET_STAFF_ROLE)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True) if staff_role else discord.PermissionOverwrite()
        }

        ticket_num = len([c for c in guild.channels if c.name.startswith("ticket-")]) + 1
        channel = await guild.create_text_channel(
            name=f"ticket-{ticket_num:04d}",
            category=category,
            overwrites=overwrites,
            topic=f"Ticket by {interaction.user}"
        )

        embed = discord.Embed(
            title=f"Ticket #{ticket_num:04d}",
            description=f"**User:** {interaction.user.mention}
**Reason:** {self.reason.value}",
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text=f"Opened at {discord.utils.format_dt(discord.utils.utcnow())}")

        close_btn = Button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒")

        async def close_callback(btn_interaction):
            if not btn_interaction.user.guild_permissions.manage_channels:
                await btn_interaction.response.send_message("No permission!", ephemeral=True)
                return
            await btn_interaction.response.send_message("Closing in 5s...", ephemeral=True)
            log_channel = guild.get_channel(config.TICKET_LOG_CHANNEL)
            if log_channel:
                log_embed = discord.Embed(title=f"Ticket #{ticket_num:04d} Closed", description=f"Closed by: {btn_interaction.user.mention}", color=config.COLOR_ERROR)
                await log_channel.send(embed=log_embed)
            await asyncio.sleep(5)
            await channel.delete()

        close_btn.callback = close_callback
        view = View(timeout=None)
        view.add_item(close_btn)

        await channel.send(content=staff_role.mention if staff_role else None, embed=embed, view=view)
        await interaction.followup.send(f"Ticket created: {channel.mention}", ephemeral=True)

class TicketPanel(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="ticket_open")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        modal = TicketModal()
        await interaction.response.send_modal(modal)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticket")
    async def ticket_cmd(self, ctx, *, reason: str = "No reason provided"):
        """Create a support ticket"""
        guild = ctx.guild
        category = guild.get_channel(config.TICKET_CATEGORY)
        staff_role = guild.get_role(config.TICKET_STAFF_ROLE)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True) if staff_role else discord.PermissionOverwrite()
        }

        ticket_num = len([c for c in guild.channels if c.name.startswith("ticket-")]) + 1
        channel = await guild.create_text_channel(name=f"ticket-{ticket_num:04d}", category=category, overwrites=overwrites)

        embed = discord.Embed(title=f"Ticket #{ticket_num:04d}", description=f"**User:** {ctx.author.mention}
**Reason:** {reason}", color=config.COLOR_PRIMARY)
        if staff_role:
            await channel.send(content=staff_role.mention, embed=embed)
        else:
            await channel.send(embed=embed)
        await ctx.send(f"Ticket created: {channel.mention}")

    @commands.command(name="ticketpanel")
    @commands.has_permissions(manage_channels=True)
    async def ticket_panel(self, ctx):
        """Send the ticket panel embed with button"""
        embed = discord.Embed(title="Support Center", description="Need help? Click the button below to open a ticket.

**Response Time:** 1-2 hours
**Support Hours:** 24/7", color=config.COLOR_PRIMARY)
        embed.set_footer(text="Obsidian Marketplace Support")
        view = TicketPanel()
        await ctx.send(embed=embed, view=view)
        await ctx.message.delete()

    @commands.command(name="close")
    @commands.has_permissions(manage_channels=True)
    async def close_ticket(self, ctx):
        """Close the current ticket channel"""
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.send(embed=discord.Embed(title="Error", description="Use this in a ticket channel only.", color=config.COLOR_ERROR))
            return

        await ctx.send(embed=discord.Embed(title="Closing Ticket", description="Closing in 5 seconds...", color=config.COLOR_WARNING))
        log_channel = ctx.guild.get_channel(config.TICKET_LOG_CHANNEL)
        if log_channel:
            await log_channel.send(embed=discord.Embed(title=f"{ctx.channel.name} Closed", description=f"Closed by: {ctx.author.mention}", color=config.COLOR_ERROR))
        await asyncio.sleep(5)
        await ctx.channel.delete()

async def setup(bot):
    await bot.add_cog(Tickets(bot))
