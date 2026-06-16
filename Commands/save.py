import nextcord
import traceback
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getTeams, getScrims, getScrim
from BotData.colors import *

def format_team_pickbans(data, scrim_data):
    if scrim_data['scrimConfiguration'].get('pickBanMode', 'None') == 'None':
        return None
    lines = []
    total_games = scrim_data['scrimConfiguration']['totalGames']
    for game_num in range(1, total_games + 1):
        game_key = f"game{game_num}"
        pickbans = data.get('teamPickBans', {}).get(game_key, {})
        bans = ", ".join(pickbans.get('bans', [])) or "None"
        picks = ", ".join(pickbans.get('picks', [])) or "None"
        lines.append(f"**Game {game_num}:** Bans: {bans} | Picks: {picks}")
    return "\n".join(lines)

class MainView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrims, channelID):
        super().__init__(timeout=None)
        self.add_item(MainDropdown(interaction, scrims, channelID))

class MainDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, scrims, channelID):
        self.interaction = interaction
        self.scrims = scrims
        self.channelID = channelID

        options = []

        for scrim in scrims: options.append(nextcord.SelectOption(label=scrim["scrimName"], value=scrim["scrimName"]))
        super().__init__(placeholder="Select a Scrim", min_values=1, max_values=1, options=options, custom_id=channelID)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        message = []
        try:
            channelID = interaction.data['custom_id']
            teams = getTeams(interaction.guild.id, interaction.data["values"][0])
            scrim_data = getScrim(interaction.guild.id, interaction.data["values"][0])
            teams_signed_up = len(teams)

            message.append(f"**Scrim Name:** {scrim_data['scrimName']}")
            message.append(f"**Scrim Time:** <t:{scrim_data['scrimEpoch']}:f>")
            message.append(f"**Max Teams:** {scrim_data['scrimConfiguration']['maxTeams']}")
            message.append(f"**Team Type:** {scrim_data['scrimConfiguration']['teamType']}")
            message.append(f"**Pick/Ban Mode:** {scrim_data['scrimConfiguration'].get('pickBanMode', 'None')}")
            message.append(f"**Match Format:** {scrim_data['scrimConfiguration'].get('matchFormat', 'Bo1')}")
            message.append("**-------------------REGISTERED TEAMS BELOW-------------------**")
            if teams_signed_up > scrim_data['scrimConfiguration']['maxTeams']:
                reserve_teams = teams_signed_up - scrim_data['scrimConfiguration']['maxTeams']
                teams_signed_up = scrim_data['scrimConfiguration']['maxTeams']
                message.append(f"**Teams:** **({teams_signed_up}/{scrim_data['scrimConfiguration']['maxTeams']})** (+ {reserve_teams})")
            message.append(f"**Teams:** **({teams_signed_up}/{scrim_data['scrimConfiguration']['maxTeams']})**")

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

                    pickban_info = format_team_pickbans(data, scrim_data)
                    if pickban_info: message.append(pickban_info)
                    if scrim_data['scrimConfiguration']['open']['checkin'] != False: message.append(f"**Checkin Status:** {data['teamStatus']['checkin']}")

                elif data["teamType"] == "Duos":
                    if data["teamSub1"] == None:
                        message.append(f"{team_count+1} | **{data['teamName']}** - **C:** {interaction.guild.get_member(int(data['teamPlayer1'])).mention} - **P:** {interaction.guild.get_member(int(data['teamPlayer2'])).mention}")
                    else:
                        subs += 1
                        message.append(f"{team_count+1} | **{data['teamName']}** - **C:** {interaction.guild.get_member(int(data['teamPlayer1'])).mention} - **P:** {interaction.guild.get_member(int(data['teamPlayer2'])).mention} - **S:** {interaction.guild.get_member(int(data['teamSub1'])).mention}")
                    players += 2
                    team_count += 1

                    pickban_info = format_team_pickbans(data, scrim_data)
                    if pickban_info: message.append(pickban_info)
                    if scrim_data['scrimConfiguration']['open']['checkin'] != False: message.append(f"**Checkin Status:** {data['teamStatus']['checkin']}")

                elif data["teamType"] == "Solos":
                    message.append(f"{team_count+1} | **{data['teamName']}** - **P:** {interaction.guild.get_member(int(data['teamPlayer1'])).mention}")
                    players += 1
                    team_count += 1

                    pickban_info = format_team_pickbans(data, scrim_data)
                    if pickban_info: message.append(pickban_info)
                    if scrim_data['scrimConfiguration']['open']['checkin'] != False: message.append(f"**Checkin Status:** {data['teamStatus']['checkin']}")

                if team_count == scrim_data['scrimConfiguration']['maxTeams']: message.append("**-------------------RESERVES BELOW-------------------**")

            message.append(f"\n**Total Teams:** {team_count} | **Total Players:** {players} | **Total Subs:** {subs}")

            embed = nextcord.Embed(title=f"{scrim_data['scrimName']} - Archive", description='\n'.join(message), color=White)
            embed.set_footer(text=f"Saved by @{interaction.user.name}")
            await interaction.guild.get_channel(int(channelID)).send(embed=embed)

            embed = nextcord.Embed(title=f"Save Complete", description=f"Scrim data for **{scrim_data['scrimName']}** has been saved to <#{channelID}>", color=Green)
            await interaction.followup.edit_message(interaction.message.id, embed=embed)

        except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

class Command_save_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="save", description="Save all players, checkin status and pick/bans to a channel **Admin Only**")
    async def save(self, interaction: nextcord.Interaction,
        channelID = nextcord.SlashOption(name="channel_id", description="Enter a channel id to pick where the data is saved to", required=True)):
        global command
        command = {"name": interaction.application_command.name, "userID": interaction.user.id, "guildID": interaction.guild.id}
        formatOutput(output=f"/{command['name']} Used by {command['userID']} | @{interaction.user.name}", status="Normal", guildID=command["guildID"])

        try: await interaction.response.defer(ephemeral=True)
        except: pass # Discord can sometimes error on defer()

        try:
            if channelID.isnumeric() == False: # Channel ID is not a number
                embed = nextcord.Embed(title=f"Save Error", description="The channel ID you entered is not a number", color=Red)
                await interaction.edit_original_message(embed=embed)
                return

            else:
                channel = self.bot.get_channel(int(channelID))
                if channel == None: # Channel not found
                    embed = nextcord.Embed(title=f"Save Error", description="The channel ID you entered was not found", color=Red)
                    await interaction.edit_original_message(embed=embed)
                    return

                else:
                    scrims = getScrims(command["guildID"])
                    if len(scrims) == 0: # No Scrims
                        embed = nextcord.Embed(title=f"Save Select", description="No scrims have been scheduled, there is nothing to save!\nSchedule a scrim using `/schedule`", color=Yellow)
                        await interaction.edit_original_message(embed=embed)
                        return

                    else: # 1 or more scrims
                        embed = nextcord.Embed(title=f"Save Select", description="Use the dropdown below to select a scrim to save", color=White)
                        await interaction.edit_original_message(embed=embed, view=MainView(interaction, scrims, channelID))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

def setup(bot):
    bot.add_cog(Command_save_Cog(bot))