"""Bot instance holder to avoid circular imports."""

bot = None


def set_bot(instance):
    global bot
    bot = instance
