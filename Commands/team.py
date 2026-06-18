import nextcord
import traceback
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getGuildTeams, getGuildConfig
from Keys import DB
from BotData.colors import *

placeholder_img = "https://github.com/user-attachments/assets/126753ee-e9a9-43d0-a21e-cbc32e555ff2"

DEFAULT_VIEWER_OVERRIDES = {
    "viewRecentPerformance": True,
    "viewTeamStats": True,
    "viewLogs": True,
}


def updateTeam(guild_id, team_name, field, value):
    if field == "teamName":
        team_data = getGuildTeams(guild_id, team_name)
        if not team_data:
            return False
        team_data["teamName"] = value
        DB[str(guild_id)]["Teams"].delete_one({team_name: {"$exists": True}})
        DB[str(guild_id)]["Teams"].insert_one({value: team_data})
        return True

    DB[str(guild_id)]["Teams"].update_one(
        {team_name: {"$exists": True}},
        {"$set": {f"{team_name}.{field}": value}},
    )
    return True


def team_permission(interaction, team_data):
    if interaction.user.guild_permissions.administrator:
        return "Admin"
    uid = interaction.user.id
    if uid == team_data.get("teamCaptain"):
        return "Captain"
    if uid in (team_data.get("teamPlayer2"), team_data.get("teamPlayer3")):
        return "Player"
    if uid in (team_data.get("teamSub1"), team_data.get("teamSub2")):
        return "Sub"
    if uid == team_data.get("teamCoach"):
        return "Coach"
    return "Public"


def build_team_embed(team_name, team_data):
    embed = nextcord.Embed(title=team_name, description=f"-# Founded at <t:{team_data['createdAt']}:f>", color=White)
    embed.add_field(name="Captain", value=f"<@{team_data['teamCaptain']}>", inline=True)
    embed.add_field(name="Player 2", value=f"<@{team_data['teamPlayer2']}>", inline=True)
    embed.add_field(name="Player 3", value=f"<@{team_data['teamPlayer3']}>", inline=True)
    embed.add_field(name="Sub 1", value=f"<@{team_data['teamSub1']}>" if team_data.get("teamSub1") else "-# None", inline=True)
    embed.add_field(name="Sub 2", value=f"<@{team_data['teamSub2']}>" if team_data.get("teamSub2") else "-# None", inline=True)
    embed.add_field(name="Coach", value=f"<@{team_data['teamCoach']}>" if team_data.get("teamCoach") else "-# None", inline=True)
    embed.set_thumbnail(url=team_data.get("teamLogo") or placeholder_img)
    return embed


class DefaultView(nextcord.ui.View):
    def __init__(self, interaction: nextcord.Interaction, team_name, permission):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.team_name = team_name
        self.permission = permission

        buttons = {
            "Name": {"id": "edit_name", "color": "gray", "permissions": ["Admin", "Captain"], "row": 1},
            "Logo": {"id": "edit_logo", "color": "gray", "permissions": ["Admin", "Captain"], "row": 1},
            "Recent Performance": {"id": "view_recent_performance", "color": "main", "permissions": ["Admin", "Captain", "Player", "Sub", "Coach", "Public"], "row": 2},
            "Stats": {"id": "view_team_stats", "color": "main", "permissions": ["Admin", "Captain", "Player", "Sub", "Coach", "Public"], "row": 2},
            "Disband Team": {"id": "disband_team", "color": "red", "permissions": ["Captain"], "row": 3},
            "Delete Team": {"id": "delete_team", "color": "red", "permissions": ["Admin"], "row": 3},
            "Leave Team": {"id": "leave_team", "color": "red", "permissions": ["Player", "Sub", "Coach"], "row": 3},
        }

        config = getGuildConfig(interaction.guild.id)
        overrides = (config.get("config") or config).get("TeamViewerOverrides") or DEFAULT_VIEWER_OVERRIDES

        for label, data in buttons.items():
            if self.permission not in data["permissions"]:
                continue
            disabled = False
            if self.permission == "Public" and data["id"].startswith("view_"):
                key = "view" + "".join(part.capitalize() for part in data["id"].split("_")[1:])
                if not overrides.get(key, True):
                    disabled = True
            style = nextcord.ButtonStyle.danger if data["color"] == "red" else (
                nextcord.ButtonStyle.secondary if data["color"] == "gray" else nextcord.ButtonStyle.primary
            )
            button = nextcord.ui.Button(style=style, label=label, disabled=disabled, row=data["row"])
            button.callback = self.create_callback(data["id"])
            self.add_item(button)

    def create_callback(self, custom_id):
        async def callback(interaction: nextcord.Interaction):
            try:
                if custom_id in ("edit_name", "edit_logo"):
                    await interaction.response.send_modal(TextModal(interaction, self.team_name, name=custom_id.split("_")[1]))
                elif custom_id == "view_recent_performance":
                    await interaction.response.send_message("Recent performance tracking is not configured yet.", ephemeral=True)
                elif custom_id == "view_team_stats":
                    await interaction.response.send_message("Team stats are not configured yet.", ephemeral=True)
                elif custom_id == "disband_team":
                    await self._disband(interaction)
                elif custom_id == "delete_team":
                    await self._delete(interaction)
                elif custom_id == "leave_team":
                    await self._leave(interaction)
            except Exception as e:
                await errorResponse(e, command, interaction, traceback.format_exc())
        return callback

    async def _disband(self, interaction):
        team_data = getGuildTeams(interaction.guild.id, self.team_name)
        role = interaction.guild.get_role(team_data["roleID"])
        if role:
            await role.delete(reason="Team disbanded")
        DB[str(interaction.guild.id)]["Teams"].delete_one({self.team_name: {"$exists": True}})
        await interaction.response.edit_message(
            embed=nextcord.Embed(title="Team Disbanded", description=f"**{self.team_name}** has been disbanded.", color=Red),
            view=None,
        )

    async def _delete(self, interaction):
        await self._disband(interaction)

    async def _leave(self, interaction):
        team_data = getGuildTeams(interaction.guild.id, self.team_name)
        role = interaction.guild.get_role(team_data["roleID"])
        if role:
            await interaction.user.remove_roles(role)
        updates = {}
        uid = interaction.user.id
        for field in ("teamPlayer2", "teamPlayer3", "teamSub1", "teamSub2", "teamCoach"):
            if team_data.get(field) == uid:
                updates[f"{self.team_name}.{field}"] = None
        if updates:
            DB[str(interaction.guild.id)]["Teams"].update_one({self.team_name: {"$exists": True}}, {"$set": updates})
        await interaction.response.send_message("You have left the team.", ephemeral=True)


class TextModal(nextcord.ui.Modal):
    def __init__(self, interaction: nextcord.Interaction, team_name, name):
        super().__init__(title=f"Edit {name.capitalize()}", timeout=None)
        self.interaction = interaction
        self.team_name = team_name
        self.name = name
        params = {"label": "Edit Team Name", "placeholder": "Enter a new unique name", "min": 3, "max": 20} if name == "name" else {
            "label": "Edit Team Logo", "placeholder": "Paste a new HTTPS logo URL", "min": 10, "max": 200
        }
        self.input = nextcord.ui.TextInput(
            label=params["label"],
            style=nextcord.TextInputStyle.short,
            placeholder=params["placeholder"],
            min_length=params["min"],
            max_length=params["max"],
            required=name == "name",
        )
        self.add_item(self.input)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            value = self.input.value.strip()
            if self.name == "name":
                teams = getGuildTeams(interaction.guild.id)
                if any(t["teamName"].lower() == value.lower() and t["teamName"] != self.team_name for t in teams):
                    await interaction.response.send_message("That team name is already taken.", ephemeral=True)
                    return
                field = "teamName"
            else:
                field = "teamLogo"
                if not value:
                    value = placeholder_img
            updateTeam(interaction.guild.id, self.team_name, field, value)
            new_name = value if self.name == "name" else self.team_name
            team_data = getGuildTeams(interaction.guild.id, new_name)
            embed = build_team_embed(new_name, team_data)
            await interaction.response.edit_message(embed=embed, view=DefaultView(interaction, new_name, team_permission(interaction, team_data)))
        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())


class team_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="team", description="View your team, or lookup a team by name")
    async def team(
        self,
        interaction: nextcord.Interaction,
        team_name: str = nextcord.SlashOption(name="team_name", description="Team to search for; leave blank for your team", required=False, autocomplete=True),
    ):
        global command
        command = {'name': interaction.application_command.name, 'guildID': interaction.guild.id, 'userID': interaction.user.id}
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            if not team_name:
                teams = getGuildTeams(interaction.guild.id)
                match = next((t for t in teams if interaction.user.id in (
                    t.get("teamCaptain"), t.get("teamPlayer2"), t.get("teamPlayer3"),
                    t.get("teamSub1"), t.get("teamSub2"), t.get("teamCoach"),
                )), None)
                if not match:
                    embed = nextcord.Embed(title="Team Not Found", description="You are not on a persistent team. Use `/create_team` or specify a team name.", color=Red)
                    await interaction.edit_original_message(embed=embed)
                    return
                team_name = match["teamName"]

            team_data = getGuildTeams(interaction.guild.id, team_name)
            if not team_data:
                embed = nextcord.Embed(title="Team Not Found", description=f"No team found with the name **{team_name}**", color=Red)
                await interaction.edit_original_message(embed=embed)
                return

            permission = team_permission(interaction, team_data)
            embed = build_team_embed(team_name, team_data)
            await interaction.edit_original_message(embed=embed, view=DefaultView(interaction, team_name, permission))
        except Exception as e:
            await errorResponse(e, command, interaction, traceback.format_exc())

    @team.on_autocomplete("team_name")
    async def team_name_autocomplete(self, interaction: nextcord.Interaction, string: str):
        teams = getGuildTeams(interaction.guild.id)
        choices = [team["teamName"] for team in teams if team.get("teamName") and (not string or string.lower() in team["teamName"].lower())]
        await interaction.response.send_autocomplete(choices[:10])


def setup(bot):
    bot.add_cog(team_Cog(bot))
