import nextcord
import traceback
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getTeams, getScrims, getScrim
from BotData.colors import *

def format_pickbans(team_data, game_key):
    pickbans = team_data.get("teamPickBans", {}).get(game_key, {})
    bans = pickbans.get("bans", [])
    picks = pickbans.get("picks", [])
    ban_str = ", ".join(bans) if bans else "None"
    pick_str = ", ".join(picks) if picks else "None"
    return f"Bans: {ban_str} | Picks: {pick_str}"

class MainView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrims, filter):
        super().__init__(timeout=None)
        self.add_item(MainDropdown(interaction, scrims, filter))

class MainDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, scrims, filter):
        self.interaction = interaction
        self.scrims = scrims
        self.filter = filter

        options = [nextcord.SelectOption(label=scrim["scrimName"], value=scrim["scrimName"]) for scrim in scrims]
        super().__init__(placeholder="Select a Scrim", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        message = []
        try:
            scrim_name = interaction.data["values"][0]
            teams = getTeams(interaction.guild.id, scrim_name)
            scrim = getScrim(interaction.guild.id, scrim_name)
            max_teams = scrim["scrimConfiguration"]["maxTeams"]
            team_count = 0
            total_games = scrim["scrimConfiguration"]["totalGames"]

            if scrim["scrimConfiguration"]["pickBanMode"] != "None":
                if self.filter == "Selections":
                    for game_num in range(1, total_games + 1):
                        message.append(f"\n**Game {game_num}**")
                        for team, data in teams.items():
                            line = f"{team_count + 1} | **{data['teamName']}** - {format_pickbans(data, f'game{game_num}')}"
                            message.append(line)
                            team_count += 1
                            if team_count == max_teams:
                                message.append("**-------------------RESERVES BELOW-------------------**")
                        team_count = 0

                embed = nextcord.Embed(
                    title=f"Pick/Ban List - {scrim_name} - Filter: {self.filter}",
                    description="\n".join(message) if message else "No pick/ban data submitted yet.",
                    color=White,
                )
                embed.set_footer(text=f"Filtered By: {self.filter}")
                await interaction.followup.edit_message(interaction.message.id, embed=embed)

            else:
                embed = nextcord.Embed(
                    title=f"Pick/Ban List - {scrim_name} - Filter: {self.filter}",
                    description="Pick/bans are disabled for this scrim",
                    color=Yellow,
                )
                await interaction.followup.edit_message(interaction.message.id, embed=embed)

        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())

class Command_pickban_list_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="pickban_list", description="Shows pick/ban selections for scheduled scrims **Admin Only**", default_member_permissions=(nextcord.Permissions(administrator=True)))
    async def pickban_list(
        self,
        interaction: nextcord.Interaction,
        filter=nextcord.SlashOption(name="filter", description="Select a filter", choices=["Selections"], required=True),
    ):
        global command
        command = {"name": interaction.application_command.name, "userID": interaction.user.id, "guildID": interaction.guild.id}
        formatOutput(output=f"/{command['name']} Used by {command['userID']} | @{interaction.user.name}", status="Normal", guildID=command["guildID"])

        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            scrims = getScrims(command["guildID"])
            if len(scrims) == 0:
                embed = nextcord.Embed(title=f"Pick/Ban List - Filter: {filter}", description="No scrims have been scheduled\nSchedule a scrim using `/schedule`", color=Yellow)
                await interaction.edit_original_message(embed=embed)
                return

            embed = nextcord.Embed(title=f"Pick/Ban List - Filter: {filter}", description="Use the dropdown below to select a scrim to view pick/bans for", color=White)
            embed.set_footer(text="Filtering may take some time to process")
            await interaction.edit_original_message(embed=embed, view=MainView(interaction, scrims, filter))

        except Exception as e:
            await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

def setup(bot):
    bot.add_cog(Command_pickban_list_Cog(bot))
