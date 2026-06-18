import nextcord
import traceback
from nextcord.ext import commands
from Main import formatOutput, errorResponse, public_command_list, admin_command_list
from BotData.colors import *

help_descriptions = {
"registrations": {
    "warning": ":warning: *Renamed (was `/team_list`)*",
    "small_text": "Shows a full list of teams, players and subs",
    "description": "Shows a full list of teams with players and subs for selected scrim.\nPlus a total team, player and sub count.\n\n**Usage:** \*optional\*\n/registrations",
    "last_updated": "Last Updated: v1.2.0 | 9/08/2024",
    },
"register_trio": {
    "warning": ":warning: *New checks added in v1.2.0*",
    "small_text": "Register a trio team for Scrims",
    "description": "Register a trio team for Scrims.\nInclude 3 players, upto 2 subs and an optional team logo.\nA dropdown will appear with all scheduled scrims to join\n\n**Usage:** \*optional\*\n`/register_trio team_name: player1: player2: player3: *sub1*: *sub2*: *logo*:`",
    "last_updated": "Last Updated: v1.2.0 | 9/08/2024",
    },
"register_duo": {
    "warning": ":bulb: *Registration commands*",
    "small_text": "Register a duo team for scrims",
    "description": "Register a duo team for scrims.\nInclude 2 players, up to 2 subs and an optional team logo.\n\n**Usage:**\n`/register_duo team_name: player1: player2:`",
    "last_updated": "Last Updated: v2.1.0 | 17/06/2026",
    },
"register_solo": {
    "warning": ":bulb: *Registration commands*",
    "small_text": "Register a solo player for scrims",
    "description": "Register for a solo scrim.\nA dropdown will appear with all scheduled scrims to join.\n\n**Usage:**\n`/register_solo player_name: *logo*:`",
    "last_updated": "Last Updated: v2.1.0 | 17/06/2026",
    },
"register_six": {
    "warning": ":bulb: *Six-stack registration*",
    "small_text": "Register a six-stack for scrims",
    "description": "Register a six-player team for Sixes scrims.\n\n**Usage:**\n`/register_six team_name: player1: ... player6:`",
    "last_updated": "Last Updated: v2.1.0 | 17/06/2026",
    },
"schedule": {
    "warning": ":warning: *Majorly Updated in v1.1.0*",
    "small_text": "Schedule Scrims",
    "description": "**Admin Only**\nSchedule scrims via guided menus and Discord events.\n\n**Usage:**\n`/schedule`",
    "last_updated": "Last Updated: v2.1.0 | 17/06/2026",
    },
"help": {
    "warning": ":warning: *Majorly Updated in v1.1.0*",
    "small_text": "Opens a help menu",
    "description": "Opens a help menu. Use the dropdown to get help on each command.\n\n**Usage:**\n`/help`",
    "last_updated": "Last Updated: v2.1.0 | 17/06/2026",
    },
"configure": {
    "warning": ":warning: *Reworked in v1.1.0*",
    "small_text": "Configure the bot for your server",
    "description": "**Admin Only**\nConfigure channels, messages, presets, and automation timings.\n\n**Usage:**\n`/configure`",
    "last_updated": "Last Updated: v2.1.0 | 17/06/2026",
    },
"create_team": {
    "warning": None,
    "small_text": "Create a persistent team role and dashboard",
    "description": "Create a team role and dashboard for your server.\nYou become the captain.\n\n**Usage:**\n`/create_team`",
    "last_updated": "Last Updated: v2.1.0 | 17/06/2026",
    },
"team": {
    "warning": None,
    "small_text": "View or manage a persistent team",
    "description": "View your team dashboard or look up another team by name.\n\n**Usage:**\n`/team *team_name*:`",
    "last_updated": "Last Updated: v2.1.0 | 17/06/2026",
    },
"score": {
    "warning": None,
    "small_text": "View and record scrim scores",
    "description": "**Admin Only**\nView team win/loss counts and record match results (winner + loser).\n\n**Usage:**\n`/score`",
    "last_updated": "Last Updated: v2.1.0 | 17/06/2026",
    },
"feedback": {
    "warning": ":bulb: *New in v1.1.0*",
    "small_text": "Submit Feedback / Suggestions / Bug Reports to the maintainers",
    "description": "Submit Feedback / Suggestions / Bug Reports to the maintainers.\nOpens a form to enter feedback which is sent to the maintainers.\n\n**Usage:** \*optional\*\n`/feedback`",
    "last_updated": "Last Updated: v1.1.0 | 26/06/2024",
    },
"scrims": {
    "warning": ":bulb: *New in v1.1.0*",
    "small_text": "View and edit all currently scheduled scrims",
    "description": "**Admin Only**\nView and edit all currently scheduled scrims.\nView all scrims with basic information\n**OR**\nView one scrim with all information and option to make edits.\n\n**Usage:** \*optional\*\n`/scrims`",
    "last_updated": "Last Updated: v1.1.0 | 26/06/2024",
    },
"team_list": {
    "warning": ":bulb: *New in v1.2.0*",
    "small_text": "Shows a full list of teams, players and subs + filters",
    "description": "**Admin Only**\nShows a full list of teams with players and subs for selected scrim.\nFilters can be applied to quickly find what your looking for\n\n**Usage:** \*optional\*\n`/team_list filter`",
    "last_updated": "Last Updated: v1.2.0 | 9/08/2024",
    },
"pickban_list": {
    "warning": ":bulb: *New in v2.0.0*",
    "small_text": "Shows pick/ban selections for scrims",
    "description": "**Admin Only**\nShows hero pick/ban selections per game.\nFilters can be applied to quickly find what you're looking for\n\n**Usage:** \*optional\*\n`/pickban_list filter:`",
    "last_updated": "Last Updated: v2.0.0 | 16/06/2026",
    },
"player_list": {
    "warning": ":bulb: *New in v1.2.0*",
    "small_text": "Shows a full list of players, filters can be used",
    "description": "**Admin Only**\nShows a full list of players.\nFilters can be applied to quickly find what your looking for\n\n**Usage:** \*optional\*\n`/player_list filter:`",
    "last_updated": "Last Updated: v1.2.0 | 9/08/2024",
    },
"give_role": {
    "warning": ":bulb: *New in v1.2.0*",
    "small_text": "Give roles to filtered users",
    "description": "**Admin Only**\nGive roles to filtered users\nEasily give roles to signed up users using filters\n\n**Usage:** \*optional\*\n`/give_role role_id: filter:`",
    "last_updated": "Last Updated: v1.2.0 | 9/08/2024",
    },
"save": {
    "warning": ":bulb: *New in v1.2.0*",
    "small_text": "Save all players, checkin status and pick/bans to a channel",
    "description": "**Admin Only**\nSave all players, checkin status and pick/ban data to a channel\nUseful for archiving previous scrims\n\n**Usage:** \*optional\*\n`/save channel_id:`",
    "last_updated": "Last Updated: v2.0.0 | 16/06/2026",
    },
"pickban_draft": {
    "warning": ":bulb: *New in v2.0.0*",
    "small_text": "Run or record pick/ban drafts",
    "description": "**Admin Only**\nOpen the pick/ban draft tool to record hero bans and picks per game for registered teams.\n\n**Usage:** \*optional\*\n`/pickban_draft`",
    "last_updated": "Last Updated: v2.0.0 | 16/06/2026",
    },
"register_my_team": {
    "warning": ":bulb: *New in v2.2.0*",
    "small_text": "Register your persistent team for a scrim",
    "description": "Register the persistent team you belong to for a matching scrim.\n\n**Usage:**\n`/register_my_team`",
    "last_updated": "Last Updated: v2.2.0 | 17/06/2026",
    },
"unregister": {
    "warning": ":bulb: *New in v2.2.0*",
    "small_text": "Leave a scrim registration",
    "description": "Remove your team from a scrim (captains only).\n\n**Usage:**\n`/unregister scrim_name:`",
    "last_updated": "Last Updated: v2.2.0 | 17/06/2026",
    },
"health": {
    "warning": None,
    "small_text": "Bot and database health check",
    "description": "Check Discord and MongoDB connectivity.\n\n**Usage:**\n`/health`",
    "last_updated": "Last Updated: v2.2.0 | 17/06/2026",
    },
"audit": {
    "warning": None,
    "small_text": "View audit log",
    "description": "**Staff Only**\nView recent bot audit log entries.\n\n**Usage:**\n`/audit *limit*:`",
    "last_updated": "Last Updated: v2.2.0 | 17/06/2026",
    },
"export": {
    "warning": None,
    "small_text": "Export scrim CSV",
    "description": "**Staff Only**\nExport team registration data for a scrim as CSV.\n\n**Usage:**\n`/export scrim_name:`",
    "last_updated": "Last Updated: v2.2.0 | 17/06/2026",
    },
"bracket": {
    "warning": None,
    "small_text": "Generate bracket pairings",
    "description": "**Staff Only**\nGenerate round 1 match pairings for a scrim.\n\n**Usage:**\n`/bracket scrim_name:`",
    "last_updated": "Last Updated: v2.2.0 | 17/06/2026",
    },
"global_message": {
    "warning": None,
    "small_text": "Queue global announcement",
    "description": "**Staff Only**\nQueue a message to all guild log channels.\n\n**Usage:**\n`/global_message title: message:`",
    "last_updated": "Last Updated: v2.2.0 | 17/06/2026",
    },
"caster": {
    "warning": None,
    "small_text": "Caster info for a scrim",
    "description": "**Staff Only**\nShow caster and voice channel info for a scrim.\n\n**Usage:**\n`/caster scrim_name:`",
    "last_updated": "Last Updated: v2.2.0 | 17/06/2026",
    },
"scrim_template": {
    "warning": None,
    "small_text": "List scrim presets",
    "description": "**Staff Only**\nList saved scrim configuration presets.\n\n**Usage:**\n`/scrim_template`",
    "last_updated": "Last Updated: v2.2.0 | 17/06/2026",
    },
"guild_stats": {
    "warning": None,
    "small_text": "Multi-guild overview",
    "description": "**Bot Owner Only**\nOverview of scrims across all guild databases.\n\n**Usage:**\n`/guild_stats`",
    "last_updated": "Last Updated: v2.2.0 | 17/06/2026",
    },
}

class dropdown_menu(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.add_item(dropdown_help_menu(interaction))

class dropdown_help_menu(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction):
        self.interaction = interaction
        if self.interaction.user.guild_permissions.administrator == True: super().__init__(placeholder="Select a command", min_values=1, max_values=1, options=[nextcord.SelectOption(label=i, value=i) for i in admin_command_list])
        else: super().__init__(placeholder="Select a command", min_values=1, max_values=1, options=[nextcord.SelectOption(label='/'+i, value=i) for i in public_command_list])

    async def callback(self, interaction: nextcord.Interaction):
        try:
            if help_descriptions[interaction.data['values'][0]]["warning"] == None: embed = nextcord.Embed(title=f"Help Menu | /{interaction.data['values'][0]}", description=f"\n{help_descriptions[interaction.data['values'][0]]['description']}", color=White)
            else: embed = nextcord.Embed(title=f"Help Menu | /{interaction.data['values'][0]}", description=f"\n{help_descriptions[interaction.data['values'][0]]['warning']}\n{help_descriptions[interaction.data['values'][0]]['description']}", color=White)

            embed.set_footer(text=f"/{interaction.data['values'][0]} {help_descriptions[interaction.data['values'][0]]['last_updated']}")
            await interaction.response.edit_message(embed=embed, view=dropdown_menu(self.interaction))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

class Command_help_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="help", description="Open a help menu for information on all commands")
    async def help(self, interaction: nextcord.Interaction):
        global command
        command = {"name": interaction.application_command.name, "userID": interaction.user.id, "guildID": interaction.guild.id}
        formatOutput(output=f"/{command['name']} Used by {command['userID']} | @{interaction.user.name}", status="Normal", guildID=command["guildID"])

        try: await interaction.response.defer(ephemeral=True)
        except: pass # Discord can sometimes error on defer()

        embed = nextcord.Embed(title="Help Menu", description="Find the command in the dropdown to get help on that command.", color=White)
        await interaction.edit_original_message(embed=embed, view=dropdown_menu(interaction))

def setup(bot):
    bot.add_cog(Command_help_Cog(bot))