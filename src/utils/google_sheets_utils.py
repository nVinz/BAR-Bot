import os
import gspread
from discord.ext import commands
from gspread import Worksheet


credentials = {
    'type': 'service_account',
    'project_id': f'{os.environ['GSPREAD_PROJECT_ID']}',
    'private_key_id': f'{os.environ['GSPREAD_PRIVATE_KEY_ID']}',
    'private_key': f'{os.environ['GSPREAD_PRIVATE_KEY'].replace('\\n', '\n')}',
    'client_email': f'{os.environ['GSPREAD_CLIENT_EMAIL']}',
    'client_id': f'{os.environ['GSPREAD_CLIENT_ID']}',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': f'{os.environ['GSPREAD_CLIENT_CERT_URI']}',
    'universe_domain': 'googleapis.com'
}


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

        self.gc = gspread.service_account_from_dict(credentials)

        self.settings_sheet = self.gc.open_by_key(os.environ['settings_sheet'])

        self.public_sheet = self.gc.open_by_key(os.environ['public_sheet'])


async def setup(bot: commands.Cog):
    await bot.add_cog(GoogleSheetsUtils(bot))
