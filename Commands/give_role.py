import nextcord
import traceback
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getTeams, getScrims, getScrim
from BotData.colors import *

class MainView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, scrims, filter, role):
        super().__init__(timeout=None)
        self.add_item(MainDropdown(interaction, scrims, filter, role))

class MainDropdown(nextcord.ui.Select):
    def __init__(self, interaction: nextcord.Interaction, scrims, filter, role):
        self.interaction = interaction
        self.scrims = scrims
        self.filter = filter
        self.role = role

        options = []

        for scrim in scrims: options.append(nextcord.SelectOption(label=scrim["scrimName"], value=scrim["scrimName"]))

        super().__init__(placeholder="Select a Scrim", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            teams = getTeams(interaction.guild.id, interaction.data["values"][0])
            for team, data in teams.items():
                if self.filter == "Captains":
                    await interaction.guild.get_member(int(data['teamPlayer1'])).add_roles(self.role)

                elif self.filter == "Players":
                    if data["teamType"] == "Trios": await interaction.guild.get_member(int(data['teamPlayer1'])).add_roles(self.role), await interaction.guild.get_member(int(data['teamPlayer2'])).add_roles(self.role), await interaction.guild.get_member(int(data['teamPlayer3'])).add_roles(self.role)
                    elif data["teamType"] == "Duos": await interaction.guild.get_member(int(data['teamPlayer1'])).add_roles(self.role), await interaction.guild.get_member(int(data['teamPlayer2'])).add_roles(self.role)
                    elif data["teamType"] == "Solos": await interaction.guild.get_member(int(data['teamPlayer1'])).add_roles(self.role)

                elif self.filter == "Subs":
                    if data["teamSub1"] == None and data["teamSub2"] == None: continue
                    elif data["teamSub2"] == None: await interaction.guild.get_member(int(data['teamSub1'])).add_roles(self.role), await interaction.guild.get_member(int(data['teamSub2'])).add_roles(self.role)
                    else: await interaction.guild.get_member(int(data['teamSub1'])).add_roles(self.role)

                elif self.filter == "All":
                    if data["teamType"] == "Trios":
                        await interaction.guild.get_member(int(data['teamPlayer1'])).add_roles(self.role), await interaction.guild.get_member(int(data['teamPlayer2'])).add_roles(self.role), await interaction.guild.get_member(int(data['teamPlayer3'])).add_roles(self.role)
                        if data["teamSub1"] == None and data["teamSub2"] == None: await interaction.guild.get_member(int(data['teamSub1'])).add_roles(self.role), await interaction.guild.get_member(int(data['teamSub2'])).add_roles(self.role)
                        elif data["teamSub2"] == None: await interaction.guild.get_member(int(data['teamSub1'])).add_roles(self.role), await interaction.guild.get_member(int(data['teamSub2'])).add_roles(self.role)
                        else: await interaction.guild.get_member(int(data['teamSub1'])).add_roles(self.role), await interaction.guild.get_member(int(data['teamSub2'])).add_roles(self.role)

                    elif data["teamType"] == "Duos":
                        await interaction.guild.get_member(int(data['teamPlayer1'])).add_roles(self.role), await interaction.guild.get_member(int(data['teamPlayer2'])).add_roles(self.role)
                        if data["teamSub1"] != None: await interaction.guild.get_member(int(data['teamSub1'])).add_roles(self.role)

                    elif data["teamType"] == "Solos":
                        await interaction.guild.get_member(int(data['teamPlayer1'])).add_roles(self.role)

            embed = nextcord.Embed(title=f"Roles Given - ({interaction.data["values"][0]})", color=White)
            embed.set_footer(text=f"Filtered By: {self.filter}")
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

        except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

class Command_give_role_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="give_role", description="Shows a list of all registered players and filters can be used **Admin Only**", default_member_permissions=(nextcord.Permissions(administrator=True)))
    async def give_role(self, interaction: nextcord.Interaction,
        roleID = nextcord.SlashOption(name="role_id", description="Input role ID", required=True),
        filter = nextcord.SlashOption(name="filter", description="Select a filter", choices=["Captains", "Players", "Subs", "All"], required=True)):

        global command
        command = {"name": interaction.application_command.name, "userID": interaction.user.id, "guildID": interaction.guild.id}
        formatOutput(output=f"/{command['name']} Used by {command['userID']} | @{interaction.user.name}", status="Normal", guildID=command["guildID"])

        try: await interaction.response.defer(ephemeral=True)
        except: pass # Discord can sometimes error on defer()

        try:
            if roleID.isnumeric() == False: # Role ID not numerical
                embed = nextcord.Embed(title=f"Give role @{roleID} - Filter: {filter}", description="Role ID must be numerical", color=Red)
                await interaction.edit_original_message(embed=embed)
                return

            else:
                role = interaction.guild.get_role(int(roleID))
                if role == None: # Role not found
                    embed = nextcord.Embed(title=f"Give role @{roleID} - Filter: {filter}", description="Role not found", color=Red)
                    await interaction.edit_original_message(embed=embed)
                    return

                else:
                    scrims = getScrims(command["guildID"])
                    if len(scrims) == 0: # No Scrims
                        embed = nextcord.Embed(title=f"Give role - Filter: {filter}", description="No scrims have been scheduled\nSchedule a scrim using `/schedule`", color=Yellow)
                        await interaction.edit_original_message(embed=embed)
                        return

                    else: # 1 or more scrims
                        embed = nextcord.Embed(title=f"Give role - Filter: {filter}", description=f"Selected role: {role.mention}\nUse the dropdown below to select a scrim to add roles for", color=White)
                        embed.set_footer(text="Giving roles may take some time to process")
                        await interaction.edit_original_message(embed=embed, view=MainView(interaction, scrims, filter, role))

        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

def setup(bot):
    bot.add_cog(Command_give_role_Cog(bot))