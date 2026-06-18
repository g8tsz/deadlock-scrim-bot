import copy
import traceback
import nextcord
from nextcord.ext import commands
from Main import formatOutput, errorResponse, getScrims, getScrim, getDefaults, getTeams, getGuildTeams
from Tasks import splitMessage, getMessages, logAction
from Keys import DB
from BotData.colors import *
from BotData.herodata import HERO_NAMES
from BotCore.pickban_rules import hero_is_available, team_pickban_complete, games_for_format
from BotCore.scrim_utils import post_reserve_list, promote_reserve_if_needed
from BotCore.context import set_command_context, get_command_context

placeholder_img = "https://github.com/user-attachments/assets/126753ee-e9a9-43d0-a21e-cbc32e555ff2"

TEAM_TYPE_PLAYERS = {
    "Solos": 1,
    "Duos": 2,
    "Trios": 3,
    "Sixes": 6,
}


def scrim_team_template():
    template = getDefaults("ScrimTeam")["ScrimTeam"]
    return copy.deepcopy(template)


def player_ids_from_team(team_data):
    ids = []
    for key in ("teamPlayer1", "teamPlayer2", "teamPlayer3", "teamPlayer4", "teamPlayer5", "teamPlayer6"):
        val = team_data.get(key)
        if val is not None:
            ids.append(int(val))
    for key in ("teamSub1", "teamSub2"):
        val = team_data.get(key)
        if val is not None:
            ids.append(int(val))
    return ids


def validate_registration(guild, scrim_name, team_name, team_type, player_ids, logo=None):
    scrim = getScrim(guild.id, scrim_name)
    if not scrim:
        return "Scrim not found."
    if scrim["scrimConfiguration"]["teamType"] != team_type:
        return f"This scrim requires **{scrim['scrimConfiguration']['teamType']}** teams."
    required = TEAM_TYPE_PLAYERS[team_type]
    if len(player_ids) < required:
        return f"{team_type} registration requires {required} unique players."

    teams = getTeams(guild.id, scrim_name)
    for _, data in teams.items():
        if data["teamName"].lower() == team_name.lower():
            return f"Team name **{team_name}** is already registered for this scrim."
        overlap = set(player_ids_from_team(data)) & set(player_ids)
        if overlap:
            mentions = ", ".join(f"<@{uid}>" for uid in overlap)
            return f"These players are already registered: {mentions}"

    for uid in player_ids:
        member = guild.get_member(uid)
        if not member:
            return f"Could not find member <@{uid}> in this server."
        if member.bot:
            return f"<@{uid}> is a bot and cannot register."

    if logo and logo.startswith("https://") is False:
        return "Logo must be a valid HTTPS URL."

    return None


def build_team_embed(team_data, reserve=False):
    team_type = team_data["teamType"]
    lines = [f"**Type:** {team_type}"]
    if team_type == "Solos":
        lines.append(f"**Player:** <@{team_data['teamPlayer1']}>")
    elif team_type == "Duos":
        lines.append(f"**C:** <@{team_data['teamPlayer1']}> | **P:** <@{team_data['teamPlayer2']}>")
    elif team_type == "Trios":
        lines.append(
            f"**C:** <@{team_data['teamPlayer1']}> | **P:** "
            f"<@{team_data['teamPlayer2']}> & <@{team_data['teamPlayer3']}>"
        )
    else:
        players = [f"<@{team_data[f'teamPlayer{i}']}>" for i in range(1, 7)]
        lines.append("**Roster:** " + ", ".join(players))

    if team_data.get("teamSub1"):
        subs = f"<@{team_data['teamSub1']}>"
        if team_data.get("teamSub2"):
            subs += f" & <@{team_data['teamSub2']}>"
        lines.append(f"**Subs:** {subs}")

    status = team_data.get("teamStatus", {})
    if status.get("checkin"):
        lines.append("**Check-in:** ✅")
    if status.get("pickBanComplete"):
        lines.append("**Pick/Bans:** ✅")

    title = team_data["teamName"]
    if reserve:
        title += " (Reserve)"
    embed = nextcord.Embed(title=title, description="\n".join(lines), color=Yellow if reserve else White)
    logo = team_data.get("teamLogo") or placeholder_img
    embed.set_thumbnail(url=logo)
    return embed


class CheckInButton(nextcord.ui.Button):
    def __init__(self, captain_id, scrim_name, team_key):
        super().__init__(style=nextcord.ButtonStyle.success, label="Check In", emoji="✅")
        self.captain_id = captain_id
        self.scrim_name = scrim_name
        self.team_key = team_key

    async def callback(self, interaction: nextcord.Interaction):
        if interaction.user.id != self.captain_id:
            await interaction.response.send_message("Only the team captain can check in.", ephemeral=True)
            return
        DB[str(interaction.guild.id)]["ScrimData"].update_one(
            {"scrimName": self.scrim_name},
            {"$set": {f"scrimTeams.{self.team_key}.teamStatus.checkin": True}},
        )
        await interaction.response.send_message("Your team is checked in!", ephemeral=True)
        team = getTeams(interaction.guild.id, self.scrim_name)[self.team_key]
        await interaction.message.edit(embed=build_team_embed(team), view=AutomatedRegisterView(
            self.captain_id, "checkin", interaction.guild.id, interaction.channel.id, self.scrim_name, self.team_key
        ))


class CaptainPickBanModal(nextcord.ui.Modal):
    def __init__(self, captain_id, scrim_name, team_key, action):
        super().__init__(title=f"Captain {action.title()}", timeout=None)
        self.captain_id = captain_id
        self.scrim_name = scrim_name
        self.team_key = team_key
        self.action = action
        self.hero_input = nextcord.ui.TextInput(label="Hero name (exact)", placeholder="e.g. Haze", min_length=2, max_length=40)
        self.add_item(self.hero_input)

    async def callback(self, interaction: nextcord.Interaction):
        if interaction.user.id != self.captain_id:
            await interaction.response.send_message("Only the team captain can manage pick/bans.", ephemeral=True)
            return
        hero = self.hero_input.value.strip()
        if hero not in HERO_NAMES:
            await interaction.response.send_message(f"Unknown hero **{hero}**. Use exact hero names.", ephemeral=True)
            return
        scrim = getScrim(interaction.guild.id, self.scrim_name)
        game_key = "game1"
        if not hero_is_available(scrim.get("scrimTeams", {}), game_key, hero, exclude_team_key=self.team_key):
            await interaction.response.send_message(f"**{hero}** is already picked or banned.", ephemeral=True)
            return
        field = f"scrimTeams.{self.team_key}.teamPickBans.{game_key}.{self.action}s"
        DB[str(interaction.guild.id)]["ScrimData"].update_one(
            {"scrimName": self.scrim_name},
            {"$addToSet": {field: hero}},
        )
        mode = scrim["scrimConfiguration"]["pickBanMode"]
        updated = getTeams(interaction.guild.id, self.scrim_name)[self.team_key]
        total_games = games_for_format(scrim["scrimConfiguration"].get("matchFormat", "Bo1"))
        complete = team_pickban_complete(updated, total_games, mode)
        DB[str(interaction.guild.id)]["ScrimData"].update_one(
            {"scrimName": self.scrim_name},
            {"$set": {f"scrimTeams.{self.team_key}.teamStatus.pickBanComplete": complete}},
        )
        await interaction.response.send_message(f"Recorded **{self.action}**: {hero}", ephemeral=True)
        team = getTeams(interaction.guild.id, self.scrim_name)[self.team_key]
        await interaction.message.edit(
            embed=build_team_embed(team),
            view=AutomatedRegisterView(
                self.captain_id, "pickban", interaction.guild.id, interaction.channel.id, self.scrim_name, self.team_key
            ),
        )


class CaptainBanButton(nextcord.ui.Button):
    def __init__(self, captain_id, scrim_name, team_key):
        super().__init__(style=nextcord.ButtonStyle.danger, label="Ban Hero", emoji="🚫")
        self.captain_id = captain_id
        self.scrim_name = scrim_name
        self.team_key = team_key

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(CaptainPickBanModal(self.captain_id, self.scrim_name, self.team_key, "ban"))


class CaptainPickButton(nextcord.ui.Button):
    def __init__(self, captain_id, scrim_name, team_key):
        super().__init__(style=nextcord.ButtonStyle.success, label="Pick Hero", emoji="✅")
        self.captain_id = captain_id
        self.scrim_name = scrim_name
        self.team_key = team_key

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(CaptainPickBanModal(self.captain_id, self.scrim_name, self.team_key, "pick"))


class PickBanNoticeButton(nextcord.ui.Button):
    def __init__(self, captain_id, scrim_name=None, team_key=None):
        super().__init__(style=nextcord.ButtonStyle.primary, label="Pick/Ban Info", emoji="🎯")
        self.captain_id = captain_id
        self.scrim_name = scrim_name
        self.team_key = team_key

    async def callback(self, interaction: nextcord.Interaction):
        if interaction.user.id != self.captain_id:
            await interaction.response.send_message("Only the team captain can manage pick/bans.", ephemeral=True)
            return
        await interaction.response.send_message(
            "Use **Ban Hero** / **Pick Hero** on your registration message, or `/pickban_draft` for full draft control.",
            ephemeral=True,
        )


class AutomatedRegisterView(nextcord.ui.View):
    def __init__(self, user_id, view_type, guildID, channelID, scrim_name=None, team_key=None):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.view_type = view_type
        self.guildID = guildID
        self.channelID = channelID
        self.scrim_name = scrim_name
        self.team_key = team_key

        if view_type == "checkin" and scrim_name and team_key:
            self.add_item(CheckInButton(user_id, scrim_name, team_key))
        elif view_type == "pickban":
            self.add_item(CaptainBanButton(user_id, scrim_name, team_key))
            self.add_item(CaptainPickButton(user_id, scrim_name, team_key))
            self.add_item(PickBanNoticeButton(user_id, scrim_name, team_key))


class ScrimSelectDropdown(nextcord.ui.Select):
    def __init__(self, interaction, team_payload):
        self.interaction = interaction
        self.team_payload = team_payload
        scrims = getScrims(interaction.guild.id)
        options = []
        for scrim in scrims:
            team_type = scrim["scrimConfiguration"]["teamType"]
            if team_type != team_payload["teamType"]:
                continue
            teams = getTeams(interaction.guild.id, scrim["scrimName"])
            count = len(teams)
            options.append(nextcord.SelectOption(
                label=scrim["scrimName"],
                value=scrim["scrimName"],
                description=f"{team_type} | {count} teams registered",
            ))
        if not options:
            options = [nextcord.SelectOption(label="No matching scrims", value="none")]
        super().__init__(placeholder="Select a scrim to join", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        if interaction.data["values"][0] == "none":
            await interaction.response.send_message("No open scrims match your team type.", ephemeral=True)
            return

        scrim_name = interaction.data["values"][0]
        payload = self.team_payload
        err = validate_registration(
            interaction.guild, scrim_name, payload["teamName"], payload["teamType"], payload["player_ids"], payload.get("teamLogo")
        )
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        scrim = getScrim(interaction.guild.id, scrim_name)
        teams = getTeams(interaction.guild.id, scrim_name)
        max_teams = scrim["scrimConfiguration"]["maxTeams"]
        reserve = len(teams) >= max_teams

        team_key = payload["teamName"].replace(" ", "_")
        suffix = 1
        while team_key in teams:
            team_key = f"{payload['teamName'].replace(' ', '_')}_{suffix}"
            suffix += 1

        team_data = scrim_team_template()
        team_data.update({
            "teamName": payload["teamName"],
            "teamType": payload["teamType"],
            "teamLogo": payload.get("teamLogo") or placeholder_img,
        })
        for i, pid in enumerate(payload["player_ids"], start=1):
            team_data[f"teamPlayer{i}"] = pid
        if payload.get("teamSub1"):
            team_data["teamSub1"] = payload["teamSub1"]
        if payload.get("teamSub2"):
            team_data["teamSub2"] = payload["teamSub2"]

        channel = interaction.guild.get_channel(scrim["scrimConfiguration"]["registrationChannel"])
        embed = build_team_embed(team_data, reserve=reserve)
        view = AutomatedRegisterView(
            payload["captain_id"], "registration", interaction.guild.id, channel.id, scrim_name, team_key
        )
        message = await channel.send(embed=embed, view=view)
        team_data["messageID"] = message.id

        DB[str(interaction.guild.id)]["ScrimData"].update_one(
            {"scrimName": scrim_name},
            {"$set": {f"scrimTeams.{team_key}": team_data}},
        )
        DB["DeadlockAutomation"]["SavedMessages"].insert_one({
            "guildID": interaction.guild.id,
            "channelID": channel.id,
            "messageID": message.id,
            "interactionID": payload["captain_id"],
            "viewType": "registration",
            "scrimName": scrim_name,
            "teamKey": team_key,
        })

        for pid in payload["player_ids"]:
            DB[str(interaction.guild.id)]["ScrimData"].update_one(
                {"scrimName": scrim_name},
                {"$addToSet": {"scrimConfiguration.playerIDs": pid}},
            )

        note = "registered as a **reserve**" if reserve else "registered successfully"
        result = nextcord.Embed(
            title="Registration Complete",
            description=f"**{payload['teamName']}** {note} for **{scrim_name}**.",
            color=Yellow if reserve else Green,
        )
        await interaction.edit_original_message(embed=result)
        await logAction(interaction.guild.id, interaction.user.name, f"{payload['teamName']} registered for {scrim_name}", "Registration")
        if reserve:
            from BotCore import bot_holder
            if bot_holder.bot:
                await post_reserve_list(bot_holder.bot, interaction.guild.id, scrim_name)


class ScrimSelectView(nextcord.ui.View):
    def __init__(self, interaction, team_payload):
        super().__init__(timeout=None)
        self.add_item(ScrimSelectDropdown(interaction, team_payload))


class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _start_registration(self, interaction, team_type, team_name, players, sub1=None, sub2=None, logo=None):
        set_command_context(interaction.application_command.name, interaction.guild.id, interaction.user.id)

        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        player_ids = list(dict.fromkeys(players))
        required = TEAM_TYPE_PLAYERS[team_type]
        if len(player_ids) < required:
            embed = nextcord.Embed(title="Registration Error", description=f"{team_type} requires {required} unique players.", color=Red)
            await interaction.edit_original_message(embed=embed)
            return

        payload = {
            "teamName": team_name,
            "teamType": team_type,
            "captain_id": interaction.user.id,
            "player_ids": player_ids,
            "teamSub1": sub1.id if sub1 else None,
            "teamSub2": sub2.id if sub2 else None,
            "teamLogo": logo,
        }
        embed = nextcord.Embed(title="Select a Scrim", description="Choose which scrim to register for.", color=White)
        await interaction.edit_original_message(embed=embed, view=ScrimSelectView(interaction, payload))

    @nextcord.slash_command(name="register_solo", description="Register for a solo scrim")
    async def register_solo(
        self,
        interaction: nextcord.Interaction,
        player_name: nextcord.Member = nextcord.SlashOption(description="The solo player", required=True),
        logo: str = nextcord.SlashOption(description="Optional team logo URL", required=False),
    ):
        team_name = player_name.display_name
        await self._start_registration(interaction, "Solos", team_name, [player_name.id], logo=logo)

    @nextcord.slash_command(name="register_duo", description="Register for a duo scrim")
    async def register_duo(
        self,
        interaction: nextcord.Interaction,
        team_name: str = nextcord.SlashOption(description="Team name", required=True),
        player1: nextcord.Member = nextcord.SlashOption(description="Captain / player 1", required=True),
        player2: nextcord.Member = nextcord.SlashOption(description="Player 2", required=True),
        sub1: nextcord.Member = nextcord.SlashOption(description="Substitute 1", required=False),
        sub2: nextcord.Member = nextcord.SlashOption(description="Substitute 2", required=False),
        logo: str = nextcord.SlashOption(description="Optional team logo URL", required=False),
    ):
        await self._start_registration(interaction, "Duos", team_name, [player1.id, player2.id], sub1, sub2, logo)

    @nextcord.slash_command(name="register_trio", description="Register for a trio scrim")
    async def register_trio(
        self,
        interaction: nextcord.Interaction,
        team_name: str = nextcord.SlashOption(description="Team name", required=True),
        player1: nextcord.Member = nextcord.SlashOption(description="Captain / player 1", required=True),
        player2: nextcord.Member = nextcord.SlashOption(description="Player 2", required=True),
        player3: nextcord.Member = nextcord.SlashOption(description="Player 3", required=True),
        sub1: nextcord.Member = nextcord.SlashOption(description="Substitute 1", required=False),
        sub2: nextcord.Member = nextcord.SlashOption(description="Substitute 2", required=False),
        logo: str = nextcord.SlashOption(description="Optional team logo URL", required=False),
    ):
        await self._start_registration(
            interaction, "Trios", team_name, [player1.id, player2.id, player3.id], sub1, sub2, logo
        )

    @nextcord.slash_command(name="register_six", description="Register for a six-stack scrim")
    async def register_six(
        self,
        interaction: nextcord.Interaction,
        team_name: str = nextcord.SlashOption(description="Team name", required=True),
        player1: nextcord.Member = nextcord.SlashOption(description="Captain / player 1", required=True),
        player2: nextcord.Member = nextcord.SlashOption(description="Player 2", required=True),
        player3: nextcord.Member = nextcord.SlashOption(description="Player 3", required=True),
        player4: nextcord.Member = nextcord.SlashOption(description="Player 4", required=True),
        player5: nextcord.Member = nextcord.SlashOption(description="Player 5", required=True),
        player6: nextcord.Member = nextcord.SlashOption(description="Player 6", required=True),
        sub1: nextcord.Member = nextcord.SlashOption(description="Substitute 1", required=False),
        sub2: nextcord.Member = nextcord.SlashOption(description="Substitute 2", required=False),
        logo: str = nextcord.SlashOption(description="Optional team logo URL", required=False),
    ):
        await self._start_registration(
            interaction,
            "Sixes",
            team_name,
            [player1.id, player2.id, player3.id, player4.id, player5.id, player6.id],
            sub1,
            sub2,
            logo,
        )

    @nextcord.slash_command(name="register_my_team", description="Register your persistent team for a matching scrim")
    async def register_my_team(self, interaction: nextcord.Interaction):
        set_command_context("register_my_team", interaction.guild.id, interaction.user.id)
        teams = getGuildTeams(interaction.guild.id)
        my_team = None
        my_name = None
        for doc in DB[str(interaction.guild.id)]["Teams"].find({}):
            for name, data in doc.items():
                if name == "_id":
                    continue
                member_ids = [data.get("teamCaptain"), data.get("teamPlayer2"), data.get("teamPlayer3"), data.get("teamSub1"), data.get("teamSub2")]
                if interaction.user.id in [m for m in member_ids if m]:
                    my_team = data
                    my_name = name
                    break
        if not my_team:
            await interaction.response.send_message("You are not on a persistent team. Use `/create_team` first.", ephemeral=True)
            return
        player_ids = [my_team["teamCaptain"], my_team["teamPlayer2"], my_team["teamPlayer3"]]
        player_ids = [int(p) for p in player_ids if p]
        await self._start_registration(
            interaction,
            "Trios",
            my_team["teamName"],
            player_ids,
            interaction.guild.get_member(my_team["teamSub1"]) if my_team.get("teamSub1") else None,
            interaction.guild.get_member(my_team["teamSub2"]) if my_team.get("teamSub2") else None,
            my_team.get("teamLogo"),
        )

    @nextcord.slash_command(name="unregister", description="Remove your team from a scrim")
    async def unregister(
        self,
        interaction: nextcord.Interaction,
        scrim_name: str = nextcord.SlashOption(description="Scrim to leave", required=True),
    ):
        set_command_context("unregister", interaction.guild.id, interaction.user.id)
        scrim = getScrim(interaction.guild.id, scrim_name)
        if not scrim:
            await interaction.response.send_message("Scrim not found.", ephemeral=True)
            return
        teams = getTeams(interaction.guild.id, scrim_name)
        team_key = None
        for key, data in teams.items():
            if interaction.user.id == data.get("teamPlayer1"):
                team_key = key
                break
        if not team_key:
            await interaction.response.send_message("You are not registered as a captain for this scrim.", ephemeral=True)
            return
        team_data = teams[team_key]
        message_id = team_data.get("messageID")
        channel = interaction.guild.get_channel(scrim["scrimConfiguration"]["registrationChannel"])
        if message_id and channel:
            try:
                msg = await channel.fetch_message(message_id)
                await msg.delete()
            except Exception:
                pass
        DB["DeadlockAutomation"]["SavedMessages"].delete_one({"messageID": message_id})
        DB[str(interaction.guild.id)]["ScrimData"].update_one(
            {"scrimName": scrim_name},
            {"$unset": {f"scrimTeams.{team_key}": ""}},
        )
        from BotCore import bot_holder
        if bot_holder.bot:
            await promote_reserve_if_needed(bot_holder.bot, interaction.guild.id, scrim_name)
        await interaction.response.send_message(f"**{team_data['teamName']}** unregistered from **{scrim_name}**.", ephemeral=True)
        await logAction(interaction.guild.id, interaction.user.name, f"{team_data['teamName']} unregistered from {scrim_name}", "Registration")


def setup(bot):
    bot.add_cog(RegisterCog(bot))
