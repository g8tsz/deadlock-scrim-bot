import nextcord
import traceback
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getTeams, getScrims, getScrim
from BotData.colors import *

class MainView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrims):
        super().__init__(timeout=None)
        self.add_item(MainDropdown(interaction, scrims))

class MainDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, scrims):
        self.interaction = interaction
        self.scrims = scrims

        options = []

        for scrim in scrims: options.append(nextcord.SelectOption(label=scrim["scrimName"], value=scrim["scrimName"]))

        super().__init__(placeholder="Select a Scrim", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        message = []
        try:
            teams = getTeams(interaction.guild.id, interaction.data["values"][0])
            max_teams = getScrim(interaction.guild.id, interaction.data["values"][0])["scrimConfiguration"]["maxTeams"]
            team_count = players = subs = 0
            for team, data in teams.items():
                if data["teamType"] == "Trios":
                    if data["teamSub1"] == None and data["teamSub2"] == None:
                        message.append(f"{team_count+1} | **{data['teamName']}** - **C:** {interaction.guild.get_member(int(data['teamPlayer1'])).mention} - **P:** {interaction.guild.get_member(int(data['teamPlayer2'])).mention} & {interaction.guild.get_member(int(data['teamPlayer3'])).mention}")
                    elif data["teamSub2"] == None:
                        subs += 1
                        message.append(f"{team_count+1} | **{data['teamName']}** - **C:** {interaction.guild.get_member(int(data['teamPlayer1'])).mention} - **P:** {interaction.guild.get_member(int(data['teamPlayer2'])).mention} & {interaction.guild.get_member(int(data['teamPlayer3'])).mention} - **S:** {interaction.guild.get_member(int(data['teamSub1'])).mention}")
                    else:
                        subs += 2
                        message.append(f"{team_count+1} | **{data['teamName']}** - **C:** {interaction.guild.get_member(int(data['teamPlayer1'])).mention} - **P:** {interaction.guild.get_member(int(data['teamPlayer2'])).mention} & {interaction.guild.get_member(int(data['teamPlayer3'])).mention} - **S:** {interaction.guild.get_member(int(data['teamSub1'])).mention} & {interaction.guild.get_member(int(data['teamSub2'])).mention}")
                    players += 3
                    team_count += 1

                elif data["teamType"] == "Duos":
                    if data["teamSub1"] == None:
                        message.append(f"{team_count+1} | **{data['teamName']}** - **C:** {interaction.guild.get_member(int(data['teamPlayer1'])).mention} - **P:** {interaction.guild.get_member(int(data['teamPlayer2'])).mention}")
                    else:
                        subs += 1
                        message.append(f"{team_count+1} | **{data['teamName']}** - **C:** {interaction.guild.get_member(int(data['teamPlayer1'])).mention} - **P:** {interaction.guild.get_member(int(data['teamPlayer2'])).mention} - **S:** {interaction.guild.get_member(int(data['teamSub1'])).mention}")
                    players += 2
                    team_count += 1

                elif data["teamType"] == "Solos":
                    message.append(f"{team_count+1} | **{data['teamName']}** - **P:** {interaction.guild.get_member(int(data['teamPlayer1'])).mention}")
                    players += 1
                    team_count += 1

                if team_count == max_teams: message.append("**-------------------RESERVES BELOW-------------------**")

            embed = nextcord.Embed(title=f"Registered Teams - {interaction.data["values"][0]}", description='\n'.join(message), color=White)
            embed.set_footer(text=f"Total Teams: {team_count} | Total Players: {players} | Total Subs: {subs}")
            await interaction.followup.edit_message(interaction.message.id, embed=embed)

        except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

class Command_registrations_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="registrations", description="Shows a list of all the teams that have been registered")
    async def registrations(self, interaction: nextcord.Interaction):
        global command
        command = {"name": interaction.application_command.name, "userID": interaction.user.id, "guildID": interaction.guild.id}
        formatOutput(output=f"/{command['name']} Used by {command['userID']} | @{interaction.user.name}", status="Normal", guildID=command["guildID"])

        try: await interaction.response.defer(ephemeral=True)
        except: pass # Discord can sometimes error on defer()

        try:
            scrims = getScrims(command["guildID"])
            if len(scrims) == 0: # No Scrims
                embed = nextcord.Embed(title=f"Team List", description="No scrims have been scheduled\nSchedule a scrim using `/schedule`", color=Yellow)
                await interaction.edit_original_message(embed=embed)
                return

            else: # 1 or more scrims
                embed = nextcord.Embed(title=f"Team List", description="Use the dropdown below to select a scrim to view teams for", color=White)
                await interaction.edit_original_message(embed=embed, view=MainView(interaction, scrims))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

def setup(bot):
    bot.add_cog(Command_registrations_Cog(bot))