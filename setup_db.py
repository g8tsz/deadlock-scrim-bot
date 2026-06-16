"""
Seed the DeadlockAutomation MongoDB database with default config and messages.
Run once after installing: python setup_db.py
"""

from Keys import DB

DEFAULT_CONFIG = {
    "toggleSetup": False,
    "toggleSetupTime": 1,
    "toggleCheckin": True,
    "toggleCheckinTime": 2,
    "togglePickBan": True,
    "togglePickBanTime": 1,
    "caster": False,
    "casterRole": None,
}

DEFAULT_CHANNELS = {
    "scrimAnnouncementChannel": None,
    "scrimRulesChannel": None,
    "scrimFormatChannel": None,
    "scrimLogChannel": None,
}

DEFAULT_MESSAGES = {
    "scrimRegistration": "**{scrim_name} Registration**{}\nUse the registration commands to sign up your team.",
    "scrimAnnouncement": "**Scrim Announcement**{}\nA new Deadlock scrim has been scheduled.",
    "scrimCheckin": "**Check-in Open**{}\nCaptains, please check in your team.",
    "scrimPickBan": "**Pick/Bans Open**{}\nSubmit your hero picks and bans for each game.",
    "scrimRules": "**Scrim Rules**{}\nAdd your server rules here via /configure.",
    "scrimFormat": "**Scrim Format**{}\nAdd match format details here via /configure.",
    "scrimReserve": "**Reserve List**{}\nTeams on the reserve list.",
}

DEFAULT_PRESETS = {
    "preset1": {"presetName": None, "presetData": {"matchFormat": None, "pickBanTime": None, "pickBanMode": None, "teamType": None, "maxTeams": None, "totalGames": None, "interval": None, "recurrence": None}},
    "preset2": {"presetName": None, "presetData": {"matchFormat": None, "pickBanTime": None, "pickBanMode": None, "teamType": None, "maxTeams": None, "totalGames": None, "interval": None, "recurrence": None}},
    "preset3": {"presetName": None, "presetData": {"matchFormat": None, "pickBanTime": None, "pickBanMode": None, "teamType": None, "maxTeams": None, "totalGames": None, "interval": None, "recurrence": None}},
    "preset4": {"presetName": None, "presetData": {"matchFormat": None, "pickBanTime": None, "pickBanMode": None, "teamType": None, "maxTeams": None, "totalGames": None, "interval": None, "recurrence": None}},
    "preset5": {"presetName": None, "presetData": {"matchFormat": None, "pickBanTime": None, "pickBanMode": None, "teamType": None, "maxTeams": None, "totalGames": None, "interval": None, "recurrence": None}},
}

GUILD_DEFAULT = {
    "Config": {
        "config": DEFAULT_CONFIG,
        "channels": DEFAULT_CHANNELS,
        "messages": DEFAULT_MESSAGES,
        "presets": DEFAULT_PRESETS,
    }
}


def seed():
    db = DB["DeadlockAutomation"]

    db["Defaults"].delete_many({})
    db["Defaults"].insert_one({"Config": GUILD_DEFAULT["Config"]})

    db["GlobalData"].delete_many({})
    db["GlobalData"].insert_one({
        "defaultMessages": DEFAULT_MESSAGES,
        "defaultConfig": DEFAULT_CONFIG,
        "defaultChannels": DEFAULT_CHANNELS,
        "defaultPresets": DEFAULT_PRESETS,
    })

    if "SavedMessages" not in db.list_collection_names():
        db.create_collection("SavedMessages")
    if "ScheduledMessages" not in db.list_collection_names():
        db.create_collection("ScheduledMessages")

    print("DeadlockAutomation database seeded successfully.")


if __name__ == "__main__":
    seed()
