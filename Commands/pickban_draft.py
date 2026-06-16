import nextcord
import traceback
from nextcord.ext import commands
from Keys import DB
from Main import formatOutput, errorResponse, getScrims, getScrim, getTeams, logAction
from BotData.colors import *
from BotData.herodata import HERO_NAMES

class ScrimSelectView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrims):
        super().__init__(timeout=None)
        self.add_item(ScrimSelectDropdown(interaction, scrims))

class ScrimSelectDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, scrims):
        self.interaction = interaction
        options = [nextcord.SelectOption(label=s["scrimName"], value=s["scrimName"]) for s in scrims]
        super().__init__(placeholder="Select a scrim", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            scrim_name = interaction.data["values"][0]
            scrim = getScrim(interaction.guild.id, scrim_name)
            teams = getTeams(interaction.guild.id, scrim_name)

            if scrim["scrimConfiguration"]["pickBanMode"] == "None":
                embed = nextcord.Embed(title="Pick/Ban Draft", description="Pick/bans are disabled for this scrim.", color=Yellow)
                await interaction.response.edit_message(embed=embed, view=None)
                return

            if len(teams) < 2:
                embed = nextcord.Embed(title="Pick/Ban Draft", description="At least 2 registered teams are required to run a draft.", color=Yellow)
                await interaction.response.edit_message(embed=embed, view=None)
                return

            team_names = [data["teamName"] for _, data in list(teams.items())[:2]]
            embed = nextcord.Embed(
                title=f"Pick/Ban Draft - {scrim_name}",
                description=f"Mode: **{scrim['scrimConfiguration']['pickBanMode']}**\nSelect a game to draft for.\n\nTeams: **{team_names[0]}** vs **{team_names[1]}**",
                color=White,
            )
            await interaction.response.edit_message(embed=embed, view=GameSelectView(interaction, scrim_name, scrim["scrimConfiguration"]["totalGames"]))

        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())

class GameSelectView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrim_name, total_games):
        super().__init__(timeout=None)
        self.add_item(GameSelectDropdown(interaction, scrim_name, total_games))

class GameSelectDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, scrim_name, total_games):
        self.interaction = interaction
        self.scrim_name = scrim_name
        options = [nextcord.SelectOption(label=f"Game {i}", value=str(i)) for i in range(1, total_games + 1)]
        super().__init__(placeholder="Select game", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            game_num = interaction.data["values"][0]
            embed = nextcord.Embed(
                title=f"Pick/Ban Draft - {self.scrim_name} - Game {game_num}",
                description="Choose whether to record a **ban** or **pick**, then select the hero.",
                color=White,
            )
            await interaction.response.edit_message(embed=embed, view=DraftActionView(interaction, self.scrim_name, game_num))

        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())

class DraftActionView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrim_name, game_num):
        super().__init__(timeout=None)
        self.add_item(DraftActionDropdown(interaction, scrim_name, game_num))

class DraftActionDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, scrim_name, game_num):
        self.interaction = interaction
        self.scrim_name = scrim_name
        self.game_num = game_num
        options = [
            nextcord.SelectOption(label="Ban", value="ban", emoji="🚫"),
            nextcord.SelectOption(label="Pick", value="pick", emoji="✅"),
        ]
        super().__init__(placeholder="Ban or Pick?", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            action = interaction.data["values"][0]
            embed = nextcord.Embed(
                title=f"Pick/Ban Draft - Game {self.game_num}",
                description=f"Select the hero to **{action}**, then choose the team.",
                color=White,
            )
            await interaction.response.edit_message(embed=embed, view=HeroSelectView(interaction, self.scrim_name, self.game_num, action))

        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())

class HeroSelectView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrim_name, game_num, action):
        super().__init__(timeout=None)
        self.add_item(HeroSelectDropdown(interaction, scrim_name, game_num, action))

class HeroSelectDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, scrim_name, game_num, action):
        self.interaction = interaction
        self.scrim_name = scrim_name
        self.game_num = game_num
        self.action = action
        options = [nextcord.SelectOption(label=hero, value=hero) for hero in HERO_NAMES[:25]]
        super().__init__(placeholder="Select hero", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            hero = interaction.data["values"][0]
            teams = getTeams(interaction.guild.id, self.scrim_name)
            team_options = [nextcord.SelectOption(label=data["teamName"], value=team_key) for team_key, data in teams.items()]
            embed = nextcord.Embed(
                title=f"Pick/Ban Draft - Game {self.game_num}",
                description=f"Record **{self.action}** of **{hero}** for which team?",
                color=White,
            )
            await interaction.response.edit_message(embed=embed, view=TeamSelectView(interaction, self.scrim_name, self.game_num, self.action, hero, team_options))

        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())

class TeamSelectView(nextcord.ui.View):
    def __init__(self, interaction, scrim_name, game_num, action, hero, team_options):
        super().__init__(timeout=None)
        self.add_item(TeamSelectDropdown(interaction, scrim_name, game_num, action, hero, team_options))

class TeamSelectDropdown(nextcord.ui.Select):
    def __init__(self, interaction, scrim_name, game_num, action, hero, team_options):
        self.interaction = interaction
        self.scrim_name = scrim_name
        self.game_num = game_num
        self.action = action
        self.hero = hero
        super().__init__(placeholder="Select team", min_values=1, max_values=1, options=team_options[:25])

    async def callback(self, interaction: nextcord.Interaction):
        try:
            team_key = interaction.data["values"][0]
            teams = getTeams(interaction.guild.id, self.scrim_name)
            team_name = teams[team_key]["teamName"]
            game_key = f"game{self.game_num}"
            field = f"scrimTeams.{team_key}.teamPickBans.{game_key}.{self.action}s"

            DB[str(interaction.guild.id)]["ScrimData"].update_one(
                {"scrimName": self.scrim_name},
                {"$addToSet": {field: self.hero}},
            )
            DB[str(interaction.guild.id)]["ScrimData"].update_one(
                {"scrimName": self.scrim_name},
                {"$set": {f"scrimTeams.{team_key}.teamStatus.pickBanComplete": True}},
            )

            await logAction(interaction.guild.id, interaction.user.name, f"{team_name} {self.action}ned {self.hero} (Game {self.game_num})", "Pick/Ban Draft")

            embed = nextcord.Embed(
                title="Pick/Ban Recorded",
                description=f"**{team_name}** {self.action}ned **{self.hero}** for Game {self.game_num}.",
                color=Green,
            )
            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())

class Command_pickban_draft_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="pickban_draft", description="Run or record pick/ban drafts for a scrim **Admin Only**", default_member_permissions=(nextcord.Permissions(administrator=True)))
    async def pickban_draft(self, interaction: nextcord.Interaction):
        global command
        command = {"name": interaction.application_command.name, "userID": interaction.user.id, "guildID": interaction.guild.id}
        formatOutput(output=f"/{command['name']} Used by {command['userID']} | @{interaction.user.name}", status="Normal", guildID=command["guildID"])

        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            scrims = getScrims(command["guildID"])
            if not scrims:
                embed = nextcord.Embed(title="Pick/Ban Draft", description="No scrims scheduled. Use `/schedule` first.", color=Yellow)
                await interaction.edit_original_message(embed=embed)
                return

            embed = nextcord.Embed(title="Pick/Ban Draft", description="Select a scrim to manage pick/bans for.", color=White)
            await interaction.edit_original_message(embed=embed, view=ScrimSelectView(interaction, scrims))

        except Exception as e:
            await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

def setup(bot):
    bot.add_cog(Command_pickban_draft_Cog(bot))
