"""Database access layer."""

from Keys import DB
from Tasks import getConfigData, getChannels, getMessages, getPresets


def getAllGuilds():
    guilds = []
    for db in DB.list_database_names():
        if db in ("DeadlockAutomation", "local", "admin"):
            continue
        guilds.append(int(db))
    return guilds


def getDefaults(type_name):
    default_data = DB["DeadlockAutomation"]["Defaults"].find_one({type_name: {"$exists": True}})[type_name]
    return {type_name: default_data}


def getGuildConfig(guildID):
    doc = DB[str(guildID)]["Config"].find_one({"Config": {"$exists": True}})
    if doc:
        return doc["Config"]
    return {
        "config": getConfigData(guildID),
        "channels": getChannels(guildID),
        "messages": getMessages(guildID),
        "presets": getPresets(guildID),
    }


def getGuildData(guildID):
    return DB[str(guildID)]["GuildData"].find_one({"guildID": guildID})


def getGuildTeams(guildID, teamName=None):
    if teamName:
        team = DB[str(guildID)]["Teams"].find_one({teamName: {"$exists": True}})
        return team[teamName] if team else None
    teams = list(DB[str(guildID)]["Teams"].find({}))
    formatted = []
    for team in teams:
        for name, data in team.items():
            if name != "_id":
                formatted.append(data)
    return formatted


def getScrims(guildID):
    return list(DB[str(guildID)]["ScrimData"].find({}))


def getScrim(guildID, scrim_name):
    return DB[str(guildID)]["ScrimData"].find_one({"scrimName": scrim_name})


def getScrimInfo(guildID, scrim_name):
    scrim_data = DB[str(guildID)]["ScrimData"].find_one({"scrimName": scrim_name})
    return {"scrimName": scrim_data["scrimName"], "scrimEpoch": scrim_data["scrimEpoch"]}


def team_member_ids(team):
    ids = []
    for key in ("teamPlayer1", "teamPlayer2", "teamPlayer3", "teamPlayer4", "teamPlayer5", "teamPlayer6"):
        val = team.get(key)
        if val is not None:
            ids.append(int(val))
    for key in ("teamSub1", "teamSub2"):
        val = team.get(key)
        if val is not None:
            ids.append(int(val))
    return ids


def write_audit(guild_id: int, user: str, action: str, category: str = "Audit"):
    DB[str(guild_id)]["AuditLog"].insert_one({
        "user": user,
        "action": action,
        "category": category,
    })
