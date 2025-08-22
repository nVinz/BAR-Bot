import configparser
from discord.ext import commands

class ConfigUtils(commands.Cog, name='ConfigUtils'):
    def __init__(self, bot):
        self.bot = bot

        self.config = configparser.ConfigParser()
        self.config.read('cfg/config.ini')

        self.tokens = configparser.ConfigParser()
        self.tokens.read('cfg/tokens.ini')


async def setup(bot: commands.Cog):
    await bot.add_cog(ConfigUtils(bot))
