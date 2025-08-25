import logging
import asyncio
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

    if os.environ['LOGGING'] == 'DEBUG':
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    asyncio.run(main(os.environ['DISCORD_TOKEN']))
