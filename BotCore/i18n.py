"""Simple locale/message helper."""

DEFAULT_LOCALE = "en"

MESSAGES = {
    "en": {
        "registration_complete": "Registration complete for **{team}**.",
        "checkin_open": "Check-in is now open.",
        "pickban_open": "Pick/bans are now open.",
    },
}


def t(key: str, locale: str = DEFAULT_LOCALE, **kwargs) -> str:
    template = MESSAGES.get(locale, MESSAGES[DEFAULT_LOCALE]).get(key, key)
    return template.format(**kwargs)
