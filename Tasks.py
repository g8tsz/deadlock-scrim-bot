import datetime
import nextcord
from Keys import DB
from BotData.colors import Green, Red, Yellow, White

def getConfigData(guildID):
    doc = DB[str(guildID)]["Config"].find_one({"config": {"$exists": True}})
    if doc:
        return doc["config"]
    doc = DB[str(guildID)]["Config"].find_one({"Config": {"$exists": True}})
    return doc["Config"] if doc else {}

def getChannels(guildID):
    doc = DB[str(guildID)]["Config"].find_one({"channels": {"$exists": True}})
    return doc["channels"] if doc else {}

def getMessages(guildID):
    doc = DB[str(guildID)]["Config"].find_one({"messages": {"$exists": True}})
    return doc["messages"] if doc else {}

def getPresets(guildID):
    doc = DB[str(guildID)]["Config"].find_one({"presets": {"$exists": True}})
    return doc["presets"] if doc else {}

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

async def logAction(guildID, user, action, category):
    try:
        channels = getChannels(guildID)
        channel_id = channels.get("scrimLogChannel")
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
