import traceback
import nextcord
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getScrims, getScrim, getTeams
from Keys import DB
from BotData.colors import *
from BotCore.context import set_command_context, get_command_context
from BotCore.scrim_utils import record_player_stat


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
        await interaction.response.edit_message(embed=embed, view=MatchResultView(interaction, scrim_name, list(teams.keys())))


class WinnerSelect(nextcord.ui.Select):
    def __init__(self, interaction, scrim_name, team_keys):
        self.scrim_name = scrim_name
        teams = getTeams(interaction.guild.id, scrim_name)
        options = [nextcord.SelectOption(label=teams[k]["teamName"], value=k) for k in team_keys[:25]]
        super().__init__(placeholder="Select winning team", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        winner_key = interaction.data["values"][0]
        teams = getTeams(interaction.guild.id, self.scrim_name)
        loser_keys = [k for k in teams.keys() if k != winner_key]
        embed = nextcord.Embed(
            title="Record Match Result",
            description=f"Winner: **{teams[winner_key]['teamName']}**\nNow select the losing team.",
            color=White,
        )
        await interaction.response.edit_message(embed=embed, view=LoserSelectView(interaction, self.scrim_name, winner_key, loser_keys))


class LoserSelectView(nextcord.ui.View):
    def __init__(self, interaction, scrim_name, winner_key, loser_keys):
        super().__init__(timeout=120)
        self.add_item(LoserSelect(interaction, scrim_name, winner_key, loser_keys))


class LoserSelect(nextcord.ui.Select):
    def __init__(self, interaction, scrim_name, winner_key, loser_keys):
        self.scrim_name = scrim_name
        self.winner_key = winner_key
        teams = getTeams(interaction.guild.id, scrim_name)
        options = [nextcord.SelectOption(label=teams[k]["teamName"], value=k) for k in loser_keys[:25]]
        super().__init__(placeholder="Select losing team", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        loser_key = interaction.data["values"][0]
        guild_id = interaction.guild.id
        DB[str(guild_id)]["ScrimData"].update_one(
            {"scrimName": self.scrim_name},
            {
                "$inc": {
                    f"scrimTeams.{self.winner_key}.teamScore.wins": 1,
                    f"scrimTeams.{loser_key}.teamScore.losses": 1,
                }
            },
        )
        teams = getTeams(guild_id, self.scrim_name)
        winner = teams[self.winner_key]["teamName"]
        loser = teams[loser_key]["teamName"]
        for pid in (teams[self.winner_key].get("teamPlayer1"), teams[loser_key].get("teamPlayer1")):
            if pid:
                record_player_stat(guild_id, int(pid), "matchesPlayed")
        record_player_stat(guild_id, int(teams[self.winner_key]["teamPlayer1"]), "wins")
        record_player_stat(guild_id, int(teams[loser_key]["teamPlayer1"]), "losses")

        w_score = teams[self.winner_key].get("teamScore", {"wins": 0, "losses": 0})
        l_score = teams[loser_key].get("teamScore", {"wins": 0, "losses": 0})
        embed = nextcord.Embed(
            title="Score Updated",
            description=(
                f"**{winner}** defeated **{loser}**.\n"
                f"{winner}: **{w_score.get('wins', 0) + 1}** W | {loser}: **{l_score.get('losses', 0) + 1}** L"
            ),
            color=Green,
        )
        await interaction.response.edit_message(embed=embed, view=None)


class MatchResultView(nextcord.ui.View):
    def __init__(self, interaction, scrim_name, team_keys):
        super().__init__(timeout=120)
        if len(team_keys) >= 2:
            self.add_item(WinnerSelect(interaction, scrim_name, team_keys))


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
        set_command_context(interaction.application_command.name, interaction.guild.id, interaction.user.id)
        command = get_command_context()
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
