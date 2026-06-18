"""Scrim lifecycle helpers: reserves, announcements, cleanup, promotion."""

import nextcord
from Keys import DB
from Tasks import getChannels, getMessages, getTeams, splitMessage, logAction
from BotData.colors import White, Yellow, Green


def ordered_teams(scrim, teams: dict) -> tuple[list, list]:
    max_teams = scrim["scrimConfiguration"]["maxTeams"]
    items = list(teams.items())
    main = items[:max_teams]
    reserves = items[max_teams:]
    return main, reserves


async def post_reserve_list(bot, guild_id: int, scrim_name: str):
    scrim = DB[str(guild_id)]["ScrimData"].find_one({"scrimName": scrim_name})
    if not scrim:
        return
    teams = getTeams(guild_id, scrim_name)
    _, reserves = ordered_teams(scrim, teams)
    if not reserves:
        return
    channels = getChannels(guild_id)
    channel_id = scrim["scrimConfiguration"]["registrationChannel"]
    channel = bot.get_channel(channel_id)
    if not channel:
        return
    lines = [f"{i+1}. **{data['teamName']}**" for i, (_, data) in enumerate(reserves)]
    msg_parts = splitMessage(getMessages(guild_id).get("scrimReserve", "Reserve List"), guild_id, scrim_name)
    embed = nextcord.Embed(title=msg_parts[0], description=msg_parts[1] + "\n" + "\n".join(lines), color=Yellow)
    message = await channel.send(embed=embed)
    DB[str(guild_id)]["ScrimData"].update_one(
        {"scrimName": scrim_name},
        {"$set": {"scrimConfiguration.IDs.reserveMessage": message.id}},
    )


async def post_scrim_announcement(bot, guild, scrim_name: str, schedule_data: dict):
    channels = getChannels(guild.id)
    ann_id = channels.get("scrimAnnouncementChannel")
    if not ann_id:
        return
    channel = guild.get_channel(ann_id)
    if not channel:
        return
    parts = splitMessage(getMessages(guild.id).get("scrimAnnouncement"), guild.id, scrim_name)
    embed = nextcord.Embed(title=parts[0], description=parts[1], color=Green)
    embed.add_field(name="Format", value=schedule_data.get("match_format", "Bo1"), inline=True)
    embed.add_field(name="Team Type", value=schedule_data.get("team_type", "?"), inline=True)
    embed.add_field(name="Starts", value=f"<t:{schedule_data['scrim_time']}:F>", inline=False)
    await channel.send(embed=embed)


async def delete_scrim_roles(guild, team_data: dict):
    for _, data in team_data.items():
        role_id = data.get("teamSetup", {}).get("roleID")
        if role_id:
            role = guild.get_role(role_id)
            if role:
                try:
                    await role.delete(reason="Scrim ended")
                except Exception:
                    pass


async def promote_reserve_if_needed(bot, guild_id: int, scrim_name: str) -> str | None:
    scrim = DB[str(guild_id)]["ScrimData"].find_one({"scrimName": scrim_name})
    if not scrim:
        return None
    teams = getTeams(guild_id, scrim_name)
    max_teams = scrim["scrimConfiguration"]["maxTeams"]
    main_keys = list(teams.keys())[:max_teams]
    reserve_keys = list(teams.keys())[max_teams:]
    if not reserve_keys:
        return None
    # Promote first reserve if a main-slot team was removed
    if len(main_keys) < max_teams:
        promote_key = reserve_keys[0]
        await logAction(guild_id, "AUTOMATION", f"Promoted reserve team {teams[promote_key]['teamName']}", "Good")
        reg_channel = bot.get_channel(scrim["scrimConfiguration"]["registrationChannel"])
        if reg_channel:
            embed = nextcord.Embed(
                title="Reserve Promoted",
                description=f"**{teams[promote_key]['teamName']}** moved from reserve to main slot.",
                color=Green,
            )
            await reg_channel.send(embed=embed)
        return promote_key
    return None


def record_player_stat(guild_id: int, user_id: int, field: str, amount: int = 1):
    DB[str(guild_id)]["PlayerStats"].update_one(
        {"userID": user_id},
        {"$inc": {field: amount}, "$setOnInsert": {"userID": user_id}},
        upsert=True,
    )
