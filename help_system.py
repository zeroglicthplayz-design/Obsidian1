import discord
from discord.ext import commands
from discord.ui import View, Button
import config

class HelpView(View):
    def __init__(self, cog_data, author):
        super().__init__(timeout=120)
        self.cog_data = cog_data
        self.author = author
        self.current_page = 0
        self.pages = list(cog_data.keys())
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        prev = Button(emoji="◀️", style=discord.ButtonStyle.secondary, disabled=self.current_page == 0)
        prev.callback = self.prev_page
        self.add_item(prev)
        page_label = Button(label=f"Page {self.current_page + 1}/{len(self.pages)}", style=discord.ButtonStyle.primary, disabled=True)
        self.add_item(page_label)
        next_btn = Button(emoji="▶️", style=discord.ButtonStyle.secondary, disabled=self.current_page == len(self.pages) - 1)
        next_btn.callback = self.next_page
        self.add_item(next_btn)

    async def prev_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    def get_embed(self):
        page_name = self.pages[self.current_page]
        commands_list = self.cog_data[page_name]
        embed = discord.Embed(title=f"{page_name}", description="Use buttons to navigate.", color=config.COLOR_PRIMARY)
        for cmd_name, cmd_info in commands_list.items():
            embed.add_field(name=f"!{cmd_name}", value=cmd_info, inline=False)
        embed.set_footer(text="Obsidian Marketplace Bot")
        return embed

class HelpSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx, *, command_name: str = None):
        if command_name:
            cmd = self.bot.get_command(command_name.lower())
            if not cmd:
                embed = discord.Embed(title="Command Not Found", description=f"Command `{command_name}` doesn't exist.", color=config.COLOR_ERROR)
                await ctx.send(embed=embed)
                return
            embed = discord.Embed(title=f"!{cmd.name}", description=cmd.help or "No description.", color=config.COLOR_PRIMARY)
            embed.add_field(name="Usage", value=f"!{cmd.name} {cmd.signature}", inline=False)
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
            await ctx.send(embed=embed)
            return

        cog_data = {
            "Tickets": {"ticket": "Create a support ticket", "ticketpanel": "Send ticket panel (Staff)", "close": "Close ticket (Staff)"},
            "Moderation": {"ban": "Ban a user", "kick": "Kick a user", "mute": "Timeout user (10m, 1h, 1d)", "unmute": "Remove timeout", "warn": "Warn user (3 = auto-kick)", "warnings": "View warnings", "clearwarns": "Clear warnings (Admin)", "purge": "Delete messages (1-100)"},
            "Welcome": {"verifypanel": "Send verify panel (Staff)", "welcomepanel": "Send welcome panel (Staff)", "rulespanel": "Send rules panel (Staff)"},
            "Economy": {"balance": "Check G-Coins", "daily": "Claim daily reward", "pay": "Send G-Coins", "leaderboard": "Top 10 richest", "addcoins": "Add coins (Admin)", "removecoins": "Remove coins (Admin)"},
            "Shop": {"shop": "Browse items", "buy": "Purchase item", "inventory": "View inventory", "additem": "Add item (Admin)", "removeitem": "Remove item (Admin)"},
            "Utility": {"ping": "Check latency", "userinfo": "User info", "serverinfo": "Server stats", "vouch": "Leave review", "vouches": "View reviews", "avatar": "Get avatar", "poll": "Create poll", "announce": "Staff announcement", "embed": "Custom embed", "say": "Bot speaks", "sync": "Sync commands (Owner)"}
        }

        embed = discord.Embed(title="OBSIDIAN MARKETPLACE", description="Prefix: `!` | 25+ Commands | Click buttons to browse.", color=config.COLOR_PRIMARY)
        embed.add_field(name="Tickets", value="`ticket`, `ticketpanel`, `close`", inline=True)
        embed.add_field(name="Moderation", value="`ban`, `kick`, `mute`, `warn`, `purge`", inline=True)
        embed.add_field(name="Welcome", value="`verifypanel`, `welcomepanel`, `rulespanel`", inline=True)
        embed.add_field(name="Economy", value="`balance`, `daily`, `pay`, `leaderboard`", inline=True)
        embed.add_field(name="Shop", value="`shop`, `buy`, `inventory`, `additem`", inline=True)
        embed.add_field(name="Utility", value="`ping`, `userinfo`, `vouch`, `poll`", inline=True)
        embed.set_footer(text=f"Requested by {ctx.author} | !help <command> for details")

        view = HelpView(cog_data, ctx.author)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpSystem(bot))
