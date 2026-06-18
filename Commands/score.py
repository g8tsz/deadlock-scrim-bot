import traceback
import nextcord
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getScrims, getScrim, getTeams
from Keys import DB
from BotData.colors import *


class ScrimScoreDropdown(nextcord.ui.Select):
    def __init__(self, interaction, scrims):
        self.interaction = interaction
        options = [nextcord.SelectOption(label=s["scrimName"], value=s["scrimName"]) for s in scrims]
        super().__init__(placeholder="Select scrim", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        scrim_name = interaction.data["values"][0]
        scrim = getScrim(interaction.guild.id, scrim_name)
        teams = getTeams(interaction.guild.id, scrim_name)
        lines = [
            f"**Scrim:** {scrim_name}",
            f"**Format:** {scrim['scrimConfiguration'].get('matchFormat', 'Bo1')}",
            "",
        ]
        for _, data in teams.items():
            score = data.get("teamScore", {"wins": 0, "losses": 0})
            lines.append(f"**{data['teamName']}** — W: {score.get('wins', 0)} | L: {score.get('losses', 0)}")
        if len(lines) <= 3:
            lines.append("_No teams registered yet._")
        embed = nextcord.Embed(title="Scrim Scores", description="\n".join(lines), color=White)
        await interaction.response.edit_message(embed=embed, view=ScoreActionView(interaction, scrim_name, list(teams.keys())))


class ScoreActionView(nextcord.ui.View):
    def __init__(self, interaction, scrim_name, team_keys):
        super().__init__(timeout=120)
        self.add_item(RecordWinDropdown(interaction, scrim_name, team_keys))


class RecordWinDropdown(nextcord.ui.Select):
    def __init__(self, interaction, scrim_name, team_keys):
        self.scrim_name = scrim_name
        teams = getTeams(interaction.guild.id, scrim_name)
        options = []
        for key in team_keys[:25]:
            options.append(nextcord.SelectOption(label=teams[key]["teamName"], value=key))
        super().__init__(placeholder="Record a win for team", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        team_key = interaction.data["values"][0]
        DB[str(interaction.guild.id)]["ScrimData"].update_one(
            {"scrimName": self.scrim_name},
            {"$inc": {f"scrimTeams.{team_key}.teamScore.wins": 1}},
        )
        teams = getTeams(interaction.guild.id, self.scrim_name)
        name = teams[team_key]["teamName"]
        score = teams[team_key].get("teamScore", {"wins": 0, "losses": 0})
        wins = score.get("wins", 0) + 1
        embed = nextcord.Embed(
            title="Score Updated",
            description=f"Recorded a win for **{name}** (now **{wins}** wins).",
            color=Green,
        )
        await interaction.response.edit_message(embed=embed, view=None)


class ScoreView(nextcord.ui.View):
    def __init__(self, interaction, scrims):
        super().__init__(timeout=None)
        self.add_item(ScrimScoreDropdown(interaction, scrims))


class Command_score_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="score",
        description="View and record scrim match scores **Admin Only**",
        default_member_permissions=(nextcord.Permissions(administrator=True)),
    )
    async def score(self, interaction: nextcord.Interaction):
        global command
        command = {"name": interaction.application_command.name, "userID": interaction.user.id, "guildID": interaction.guild.id}
        formatOutput(output=f"/{command['name']} Used by {command['userID']}", status="Normal", guildID=command["guildID"])
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass
        try:
            scrims = getScrims(command["guildID"])
            if not scrims:
                embed = nextcord.Embed(title="Score", description="No scrims scheduled.", color=Yellow)
                await interaction.edit_original_message(embed=embed)
                return
            embed = nextcord.Embed(title="Score Manager", description="Select a scrim to view or update scores.", color=White)
            await interaction.edit_original_message(embed=embed, view=ScoreView(interaction, scrims))
        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())


def setup(bot):
    bot.add_cog(Command_score_Cog(bot))
