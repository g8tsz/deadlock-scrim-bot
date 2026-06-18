import nextcord
import traceback
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getTeams, getScrims, getScrim
from BotData.colors import *


async def add_role_safe(guild, member_id, role):
    member = guild.get_member(int(member_id))
    if member and role:
        await member.add_roles(role)


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
        options = [nextcord.SelectOption(label=scrim["scrimName"], value=scrim["scrimName"]) for scrim in scrims]
        super().__init__(placeholder="Select a Scrim", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            teams = getTeams(interaction.guild.id, interaction.data["values"][0])
            for _, data in teams.items():
                if self.filter == "Captains":
                    await add_role_safe(interaction.guild, data['teamPlayer1'], self.role)

                elif self.filter == "Players":
                    player_keys = ["teamPlayer1"]
                    if data["teamType"] in ("Duos", "Trios", "Sixes"):
                        player_keys.append("teamPlayer2")
                    if data["teamType"] in ("Trios", "Sixes"):
                        player_keys.append("teamPlayer3")
                    if data["teamType"] == "Sixes":
                        player_keys.extend(["teamPlayer4", "teamPlayer5", "teamPlayer6"])
                    for key in player_keys:
                        await add_role_safe(interaction.guild, data[key], self.role)

                elif self.filter == "Subs":
                    if data.get("teamSub1"):
                        await add_role_safe(interaction.guild, data["teamSub1"], self.role)
                    if data.get("teamSub2"):
                        await add_role_safe(interaction.guild, data["teamSub2"], self.role)

                elif self.filter == "All":
                    for member_id in _all_member_ids(data):
                        await add_role_safe(interaction.guild, member_id, self.role)

            embed = nextcord.Embed(title=f"Roles Given - ({interaction.data['values'][0]})", color=White)
            embed.set_footer(text=f"Filtered By: {self.filter}")
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())


def _all_member_ids(data):
    ids = []
    for key in ("teamPlayer1", "teamPlayer2", "teamPlayer3", "teamPlayer4", "teamPlayer5", "teamPlayer6", "teamSub1", "teamSub2"):
        val = data.get(key)
        if val is not None:
            ids.append(val)
    return ids


class Command_give_role_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="give_role", description="Give roles to filtered users **Admin Only**", default_member_permissions=(nextcord.Permissions(administrator=True)))
    async def give_role(self, interaction: nextcord.Interaction,
        role_id: str = nextcord.SlashOption(name="role_id", description="Role ID to give", required=True),
        filter: str = nextcord.SlashOption(name="filter", description="Filter users", required=True, choices=["Captains", "Players", "Subs", "All"])):

        global command
        command = {"name": interaction.application_command.name, "userID": interaction.user.id, "guildID": interaction.guild.id}
        formatOutput(output=f"/{command['name']} Used by {command['userID']}", status="Normal", guildID=command["guildID"])

        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            if not role_id.isnumeric():
                embed = nextcord.Embed(title="Give Role Error", description="Role ID must be a number.", color=Red)
                await interaction.edit_original_message(embed=embed)
                return

            role = interaction.guild.get_role(int(role_id))
            if role is None:
                embed = nextcord.Embed(title="Give Role Error", description="Role not found.", color=Red)
                await interaction.edit_original_message(embed=embed)
                return

            scrims = getScrims(command["guildID"])
            if not scrims:
                embed = nextcord.Embed(title="Give Role", description="No scrims scheduled.", color=Yellow)
                await interaction.edit_original_message(embed=embed)
                return

            embed = nextcord.Embed(title="Give Role", description="Select a scrim.", color=White)
            await interaction.edit_original_message(embed=embed, view=MainView(interaction, scrims, filter, role))
        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())


def setup(bot):
    bot.add_cog(Command_give_role_Cog(bot))
