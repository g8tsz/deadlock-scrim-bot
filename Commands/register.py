"""Loads registration slash commands and persistent registration views."""


def setup(bot):
    from Commands.register_trio import RegisterCog
    bot.add_cog(RegisterCog(bot))
