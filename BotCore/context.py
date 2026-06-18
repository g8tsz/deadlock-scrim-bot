"""Thread-safe command context (replaces global command dict)."""
from contextvars import ContextVar

_command_ctx: ContextVar[dict | None] = ContextVar("command_ctx", default=None)


def set_command_context(name: str, guild_id: int, user_id: int) -> None:
    _command_ctx.set({"name": name, "guildID": guild_id, "userID": user_id})


def get_command_context() -> dict:
    ctx = _command_ctx.get()
    if ctx is None:
        return {"name": "unknown", "guildID": 0, "userID": 0}
    return ctx
