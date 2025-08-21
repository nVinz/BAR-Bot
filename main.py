import logging
import asyncio
import configparser
import discord
from discord.ext import commands

intents = discord.Intents.all()
intents.message_content = True
intents.messages = True
intents.guild_messages = True


async def main(token):

    async with bot:
        await bot.load_extension("cogs.admin")
        await bot.start(token)

if __name__ == '__main__':
    bot = commands.Bot(command_prefix='!',intents=intents)
    config = configparser.ConfigParser()
    config.read('config.ini')

    logging.basicConfig(level=logging.ERROR)

    asyncio.run(main(config["Tokens"]["discord"]))



