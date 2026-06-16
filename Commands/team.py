import nextcord
import traceback
import time
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getGuildTeams, getGuildConfig
from Keys import DB
from BotData.colors import *

placeholder_img = "https://github.com/user-attachments/assets/126753ee-e9a9-43d0-a21e-cbc32e555ff2"

def updateTeam(interaction: nextcord.Interaction, team_name, field, value):
    if field == "teamName": # Since the team name is being updated, its not as simple as a k:v replace
        team_data = getGuildTeams(interaction.guild.id, team_name)

        DB[str(interaction.guild.id)]["Teams"].find_one_and_update(
            {team_name: {'$exists': True}},
            {"$set": {value: team_data}}
        )

        DB[str(interaction.guild.id)]["Teams"].find_one_and_update(
            {team_name: {'$exists': True}},
            {"$unset": {team_name: ""}}
        )
        team_name = value

    DB[str(interaction.guild.id)]["Teams"].find_one_and_update({team_name: {'$exists': True}}, {"$set": {f"{team_name}.{field}": value}})

class DefaultView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, team_name, permission):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.team_name = team_name
        self.permission = permission

        buttons = {
            "Edit:": {"id": "edit_placeholder", "color": "gray", "Permission":["Admin", "Captain"], "placeholder": True, "row": 1},
            "Name": {"id": "edit_name", "color": "gray", "Permission": ["Admin", "Captain"], "placeholder": False, "row": 1},
            "Logo": {"id": "edit_logo", "color": "gray", "Permission": ["Admin", "Captain"], "placeholder": False, "row": 1},
            "Members": {"id": "edit_members", "color": "gray", "Permission": ["Admin", "Captain"], "placeholder": False, "row": 1},

            "View:": {"id": "view_placeholder", "color": "main", "Permission":["Admin", "Captain", "Player", "Sub", "Coach", "Public"], "placeholder": True, "row": 2},
            "Recent Performance": {"id": "view_recent_performance", "color": "main", "Permission": ["Admin", "Captain", "Player", "Sub", "Coach", "Public"], "placeholder": False, "row": 2},
            "Stats": {"id": "view_team_stats", "color": "main", "Permission": ["Admin", "Captain", "Player", "Sub", "Coach", "Public"], "placeholder": False, "row": 2},
            "Logs": {"id": "view_logs", "color": "main", "Permission": ["Admin", "Captain", "Player", "Sub", "Coach", "Public"], "placeholder": False, "row": 2},

            "Danger:": {"id": "danger_placeholder", "color": "red", "Permission":["Admin", "Captain", "Player", "Sub", "Coach"], "placeholder": True, "row": 3},
            "Disband Team": {"id": "disband_team", "color": "red", "Permission": ["Captain"], "placeholder": False, "row": 3},
            "Delete Team": {"id": "delete_team", "color": "red", "Permission": ["Admin"], "placeholder": False, "row": 3},
            "Leave Team": {"id": "leave_team", "color": "red", "Permission": ["Player", "Sub", "Coach"], "placeholder": False, "row": 3},
            "Transfer Captain": {"id": "transfer_captain", "color": "red", "Permission": ["Admin", "Captain"], "placeholder": False, "row": 3}
        }

        permssion_overrides = getGuildConfig(interaction.guild.id).get("TeamViewerOverrides")
        for label, data in buttons.items():
            if self.permission not in data["Permission"]: continue

            if self.permission == "Public": # When public permission, check overrides
                if data["id"] == "view_recent_performance" or data["id"] == "view_team_stats" or data["id"] == "view_logs":
                    key = data["id"].split('_')
                    result = []
                    for part in key[1:]: result.append(part.capitalize())
                    if not permssion_overrides[f"view{''.join(result)}"]: data["placeholder"] = True

            if data["color"] == "red": style = nextcord.ButtonStyle.danger
            elif data["color"] == "gray": style = nextcord.ButtonStyle.secondary
            elif data["color"] == "main": style = nextcord.ButtonStyle.primary
            button = nextcord.ui.Button(style=style, label=label, disabled=data["placeholder"], row=data["row"])

            button.callback = self.create_callback(data["id"])
            self.add_item(button)

    def create_callback(self, custom_id):
        async def callback(interaction: nextcord.Interaction):
            try:
                if custom_id == "edit_name" or custom_id == "edit_logo": await interaction.response.send_modal(TextModal(interaction, self.team_name, self.permission, name=custom_id.split('_')[1]))
                elif "view_" in custom_id: pass
            except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())
        return callback

class TextModal(nextcord.ui.Modal):
    def __init__(self, interaction: nextcord.Interaction, team_name, permission, name):
        super().__init__(title=name, timeout=None)
        self.interaction = interaction
        self.team_name = team_name
        self.permission = permission
        self.name = name

        if name == "name": params = {"label": "Edit Team Name", "placeholder": "Enter a new unique name", "min": 3, "max": 20}
        elif name == "logo": params = {"label": "Edit Team Logo", "placeholder": "Paste a new URL or leave blank to use a default logo", "min": 10, "max": 99} 

        self.input = nextcord.ui.TextInput(
            label=params["label"],
            style=nextcord.TextInputStyle.short,
            placeholder=params["placeholder"],
            min_length=params["min"],
            max_length=params["max"]
        )

        self.input.callback = self.callback
        self.add_item(self.input)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            # TODO:Add check to team name (see if taken)
            print(f"RAW INPUT '{self.input.value}'")
            updateTeam(interaction, self.team_name, field=f"team{self.name.capitalize()}", value=self.input.value)
        except Exception as e: await errorResponse(e, command, interaction, error_traceback=traceback.format_exc())

class team_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="team", description="View your team, or lookup a team by name")
    async def team(self, interaction: nextcord.Interaction,
        team_name: str = nextcord.SlashOption(name="team_name", description="Team to search for, leave blank to lookup your team", required=True, autocomplete=True)):

        global command
        command = {'name': interaction.application_command.name, 'guildID': interaction.guild.id, 'userID': interaction.user.id}
        try: await interaction.response.defer(ephemeral=True)
        except: pass # Discord can sometimes error on defer()

        try:
            embed = nextcord.Embed(title="Searching for team", description="This may take a few minutes, please wait", color=White)
            await interaction.edit_original_message(embed=embed)

            team_data = getGuildTeams(interaction.guild.id, team_name)
            if not team_data:
                embed = nextcord.Embed(title="Team Not Found", description=f"No team found with the name **{team_name}**", color=Red)
                await interaction.edit_original_message(embed=embed)
                return

            # Permissions | Admin, Captain, Player, Sub, Coach, Public = Everyone Else
            if interaction.user.guild_permissions.administrator: permission = "Admin"
            if interaction.user.id == team_data['teamCaptain']: permission = "Captain" # override Admin if Captain
            elif interaction.user.id == team_data['teamPlayer2']: permission = "Player"
            elif interaction.user.id == team_data['teamPlayer3']: permission = "Player"
            elif interaction.user.id == team_data['teamSub1']: permission = "Sub"
            elif interaction.user.id == team_data['teamSub2']: permission = "Sub"
            elif interaction.user.id == team_data['teamCoach']: permission = "Coach"
            else: permission = "Public"

            embed = nextcord.Embed(title=team_name, description=f"-# Founded at <t:{team_data['createdAt']}:f>", color=White)
            embed.add_field(name="Captain", value=f"<@{team_data['teamCaptain']}>", inline=True)
            embed.add_field(name="Player 2", value=f"<@{team_data['teamPlayer2']}>", inline=True)
            embed.add_field(name="Player 3", value=f"<@{team_data['teamPlayer3']}>", inline=True)
            embed.add_field(name="Sub 1", value=f"<@{team_data['teamSub1']}>" if team_data['teamSub1'] else "-# None", inline=True)
            embed.add_field(name="Sub 2", value=f"<@{team_data['teamSub2']}>" if team_data['teamSub2'] else "-# None", inline=True)
            embed.add_field(name="Coach", value=f"<@{team_data['teamCoach']}>" if team_data['teamCoach'] else "-# None", inline=True)

            try: # Attempt to put team logo in embed, may be expired or changed
                team_logo = team_data['teamLogo']
                embed.set_thumbnail(url=team_logo)

            except:
                team_logo = placeholder_img
                embed.set_thumbnail(url=team_logo)

            await interaction.edit_original_message(embed=embed, view=DefaultView(interaction, team_name, permission))

        except Exception as e: await errorResponse(e, command, interaction, traceback.format_exc())

    @team.on_autocomplete("team_name")
    async def team_name_autocomplete(self, interaction: nextcord.Interaction, string: str):
        teams = getGuildTeams(interaction.guild.id)
        choices = []
        for team in teams:
            name = team.get("teamName")
            if name and (not string or string.lower() in name.lower()):
                choices.append(name)

        await interaction.response.send_autocomplete(choices[:10])

def setup(bot):
    bot.add_cog(team_Cog(bot))