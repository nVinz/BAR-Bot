from discord.ext import commands
from iracingdataapi.client import irDataClient

class IracingUtils(commands.Cog, name='IracingUtils'):
    def __init__(self, bot):
        self.bot = bot

        self.config = self.bot.get_cog('ConfigUtils').config

        self.iracing_client = irDataClient(username=self.config['Logins']['iracing'],
                                           password=self.config['Passwords']['iracing'])

async def setup(bot: commands.Cog):
    await bot.add_cog(IracingUtils(bot))