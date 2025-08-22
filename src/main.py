import logging
import asyncio
import configparser
import os
import discord
from discord.ext import commands


intents = discord.Intents.all()
intents.message_content = True
intents.messages = True
intents.guild_messages = True


async def main(token):
    async with bot:
        for filename in os.listdir('src/utils'):
            if filename.endswith('.py'):
                await bot.load_extension(f'utils.{filename[:-3]}')

        for filename in os.listdir('src/cogs'):
            if filename.endswith('.py'):
                await bot.load_extension(f'cogs.{filename[:-3]}')

        await bot.start(token)


if __name__ == '__main__':
    bot = commands.Bot(command_prefix='!',intents=intents)

    config = configparser.ConfigParser()
    config.read('cfg/config.ini')

    tokens = configparser.ConfigParser()
    tokens.read('cfg/tokens.ini')

    if config['Logging']['level'] == 'DEBUG':
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    asyncio.run(main(tokens['Tokens']['discord']))
