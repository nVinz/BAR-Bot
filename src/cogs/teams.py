import os
import time
import discord
from discord.ext import commands
from gspread import Worksheet


async def parse_teams(teams_sheet: Worksheet, teams_count, message):
    settings_link = f'https://docs.google.com/spreadsheets/d/{os.environ['settings_sheet']}'
    teams = []
    for index in range(2, teams_count + 2):  # Старт со 2й строки
        team_data = teams_sheet.row_values(index)
        time.sleep(1)

        await message.edit(embed=discord.Embed(title=f'Найдено команд: *{teams_count}*',
                                           description=f'**⏳ Шаг 1**\n⬇️ Загрузка из [Google Sheets]({settings_link}): {team_data[0]} ({index-1}/{teams_count})',
                                           colour=discord.Color.green()))

        # 0 = Название, 1 = Лого
        teams.append({
            'name': team_data[0],
            'logo': team_data[1]
        })

    return teams


class Teams(commands.Cog, name='Teams'):
    def __init__(self, bot):
        self.bot = bot

        self.iracing_client = self.bot.get_cog('IracingUtils').iracing_client

        self.settings_sheet = self.bot.get_cog('GoogleSheetsUtils').settings_sheet


    @commands.command(name='update_teams')
    async def update_teams_command(self, ctx):
        # teams_sheet = self.settings_sheet.worksheet('Команды')
        await ctx.send(embed=discord.Embed(title=f'WIP',
                                           colour=discord.Color.yellow()))


async def setup(bot: commands.Cog):
    await bot.add_cog(Teams(bot))
