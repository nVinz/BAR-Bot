from discord.ext import commands
from iracingdataapi.client import irDataClient

class IracingUtils(commands.Cog, name='IracingUtils'):
    def __init__(self, bot):
        self.bot = bot

        self.tokens = self.bot.get_cog('ConfigUtils').tokens

        self.iracing_client = irDataClient(username=self.tokens['Logins']['iracing'],
                                           password=self.tokens['Passwords']['iracing'])

async def setup(bot: commands.Cog):
    await bot.add_cog(IracingUtils(bot))