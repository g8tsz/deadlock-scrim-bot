import copy
import datetime
import nextcord
from Keys import DB
from BotData.colors import Green, Red, Yellow, White


def getConfigData(guildID):
    doc = DB[str(guildID)]["Config"].find_one({"config": {"$exists": True}})
    if doc:
        return doc["config"]
    doc = DB[str(guildID)]["Config"].find_one({"Config": {"$exists": True}})
    if doc and isinstance(doc.get("Config"), dict):
        inner = doc["Config"]
        if "config" in inner:
            return inner["config"]
    return {}


def getChannels(guildID):
    doc = DB[str(guildID)]["Config"].find_one({"channels": {"$exists": True}})
    if doc:
        return doc["channels"]
    doc = DB[str(guildID)]["Config"].find_one({"Config": {"$exists": True}})
    if doc and isinstance(doc.get("Config"), dict) and "channels" in doc["Config"]:
        return doc["Config"]["channels"]
    return {}


def getMessages(guildID):
    doc = DB[str(guildID)]["Config"].find_one({"messages": {"$exists": True}})
    if doc:
        return doc["messages"]
    doc = DB[str(guildID)]["Config"].find_one({"Config": {"$exists": True}})
    if doc and isinstance(doc.get("Config"), dict) and "messages" in doc["Config"]:
        return doc["Config"]["messages"]
    return {}


def getPresets(guildID):
    doc = DB[str(guildID)]["Config"].find_one({"presets": {"$exists": True}})
    if doc:
        return doc["presets"]
    doc = DB[str(guildID)]["Config"].find_one({"Config": {"$exists": True}})
    if doc and isinstance(doc.get("Config"), dict) and "presets" in doc["Config"]:
        return doc["Config"]["presets"]
    return {}


def seedGuildConfig(guildID, log_channel_id=None):
    """Insert per-guild config documents using DeadlockAutomation defaults."""
    defaults = DB["DeadlockAutomation"]["Defaults"].find_one({"Config": {"$exists": True}})
    if not defaults:
        return
    cfg = copy.deepcopy(defaults["Config"])
    DB[str(guildID)]["Config"].delete_many({})
    DB[str(guildID)]["Config"].insert_one({"config": cfg["config"]})
    DB[str(guildID)]["Config"].insert_one({"channels": cfg["channels"]})
    DB[str(guildID)]["Config"].insert_one({"messages": cfg["messages"]})
    DB[str(guildID)]["Config"].insert_one({"presets": cfg["presets"]})
    if log_channel_id:
        DB[str(guildID)]["Config"].update_one(
            {"channels": {"$exists": True}},
            {"$set": {"channels.scrimLogChannel": log_channel_id}},
        )


def getLogChannelId(guildID):
    channels = getChannels(guildID)
    return channels.get("scrimLogChannel")


def getTeams(guildID, scrim_name=None):
    if scrim_name:
        scrim = DB[str(guildID)]["ScrimData"].find_one({"scrimName": scrim_name})
        if scrim:
            return scrim.get("scrimTeams", {})
        return {}

    teams = []
    for scrim in DB[str(guildID)]["ScrimData"].find({}):
        for team_name, team_data in scrim.get("scrimTeams", {}).items():
            teams.append(team_data)
    return teams


def splitMessage(message, guildID, scrim_name=None):
    if message is None:
        return ["Deadlock Scrim Bot", ""]
    parts = message.split("{}")
    title = parts[0].strip() if parts else ""
    description = "\n".join(parts[1:]).strip() if len(parts) > 1 else ""
    if scrim_name:
        title = title.replace("{scrim_name}", scrim_name)
        description = description.replace("{scrim_name}", scrim_name)
    return [title, description]


def unformatMessage(message):
    if message is None:
        return ""
    return message.replace("\n", "{}")


def automation_message_key(phase):
    """Map automation phase to config message key."""
    if phase == "checkin":
        return "scrimCheckin"
    if phase in ("pickban", "pickBan"):
        return "scrimPickBan"
    return f"scrim{phase.capitalize()}"


async def logAction(guildID, user, action, category):
    try:
        channel_id = getLogChannelId(guildID)
        if not channel_id:
            return

        from Main import bot
        channel = bot.get_channel(channel_id)
        if not channel:
            return

        color = Green
        if category == "Error":
            color = Red
        elif category == "Warning":
            color = Yellow

        embed = nextcord.Embed(
            title=f"Log | {category}",
            description=action,
            color=color,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=f"By {user}")
        await channel.send(embed=embed)
    except Exception:
        pass
