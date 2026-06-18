"""
Normalize legacy guild config documents to the current 4-document schema.
Run: python migrate_guild_config.py
"""

from Keys import DB
from Tasks import seedGuildConfig


def migrate_guild(guild_id: str) -> bool:
    if guild_id in ("DeadlockAutomation", "admin", "local"):
        return False
    legacy = DB[guild_id]["Config"].find_one({"Config": {"$exists": True}})
    if not legacy:
        return False
    inner = legacy["Config"]
    log_channel = inner.get("channels", {}).get("scrimLogChannel")
    seedGuildConfig(int(guild_id), log_channel_id=log_channel)
    DB[guild_id]["Config"].delete_one({"Config": {"$exists": True}})
    print(f"Migrated guild {guild_id}")
    return True


def migrate_all():
    count = 0
    for db_name in DB.list_database_names():
        if migrate_guild(db_name):
            count += 1
    print(f"Migration complete. {count} guild(s) updated.")


if __name__ == "__main__":
    migrate_all()
