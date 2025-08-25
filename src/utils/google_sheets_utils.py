import os

import gspread
from discord.ext import commands
from gspread import Worksheet


def cleanup(worksheet: Worksheet):
    worksheet.unmerge_cells('A2:Z100')

    worksheet.batch_clear(['A2:Z100'])

    worksheet.format("A2:Z100", {
        "backgroundColor": {
            "red": 1.0,
            "green": 1.0,
            "blue": 1.0
        },
        #"horizontalAlignment": "LEFT",
        "textFormat": {
            "foregroundColor": {
                "red": 0.0,
                "green": 0.0,
                "blue": 0.0
            },
            "fontSize": 10,
            "bold": False
        }
    })


class GoogleSheetsUtils(commands.Cog, name='GoogleSheetsUtils'):
    def __init__(self, bot):
        self.bot = bot

        self.settings_sheet = gspread.service_account().open_by_key(os.environ['settings_sheet'])

        self.public_sheet = gspread.service_account().open_by_key(os.environ['public_sheet'])


async def setup(bot: commands.Cog):
    await bot.add_cog(GoogleSheetsUtils(bot))
