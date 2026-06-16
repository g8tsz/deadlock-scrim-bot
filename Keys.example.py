"""
Copy this file to `Keys.py` and fill in the values. `Keys.py` is gitignored.

Required:
    BOT_TOKEN      - your Discord bot token
    DB             - a pymongo MongoClient (or compatible) connected to your Mongo instance
    BOT_VERSION    - version string shown in embeds, e.g. "v1.2.0"

Optional (for forwarding feedback + errors into your own Discord reporting channel):
    ERROR_REPORT_GUILD_ID    - int, guild/server id where the bot posts error reports
    ERROR_REPORT_CHANNEL_ID  - int, channel id inside that guild
    Leave both as None to disable forwarding.
"""

from pymongo import MongoClient

BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN"
DB = MongoClient("mongodb://localhost:27017")
BOT_VERSION = "v2.0.0-deadlock"

ERROR_REPORT_GUILD_ID: int | None = None
ERROR_REPORT_CHANNEL_ID: int | None = None
