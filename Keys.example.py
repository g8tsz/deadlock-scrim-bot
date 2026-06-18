# Discord bot token (or set DISCORD_BOT_TOKEN env var)
BOT_TOKEN = __import__("os").environ.get("DISCORD_BOT_TOKEN", "YOUR_DISCORD_BOT_TOKEN")

# Mongo URI (or set MONGODB_URI env var)
_mongo_uri = __import__("os").environ.get("MONGODB_URI", "mongodb://localhost:27017")
from pymongo import MongoClient
DB = MongoClient(_mongo_uri)

BOT_VERSION = __import__("os").environ.get("BOT_VERSION", "v2.2.0-deadlock")

ERROR_REPORT_GUILD_ID = int(__import__("os").environ.get("ERROR_REPORT_GUILD_ID", "0") or "0") or None
ERROR_REPORT_CHANNEL_ID = int(__import__("os").environ.get("ERROR_REPORT_CHANNEL_ID", "0") or "0") or None
BOT_OWNER_ID = int(__import__("os").environ.get("BOT_OWNER_ID", "0") or "0") or None
