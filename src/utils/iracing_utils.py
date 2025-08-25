import os

from discord.ext import commands
from iracingdataapi.client import irDataClient


class IracingUtils(commands.Cog, name='IracingUtils'):
    def __init__(self, bot):
        self.bot = bot

        self.iracing_client = irDataClient(username=os.environ['ir_login'],
                                           password=os.environ['ir_password'])


async def setup(bot: commands.Cog):
    await bot.add_cog(IracingUtils(bot))
