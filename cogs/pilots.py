import time
import discord
from discord.ext import commands
from datetime import datetime
from gspread import Worksheet
from utils.google_sheets_utils import cleanup

iracing_series = ['Sports Car', 'Formula Car', 'Oval']

cells_mapping = {
    'nickname': 'A',
    'name': 'B',
    'age': 'C',
    'Sports Car': 'D',
    'Formula Car': 'E',
    'Oval': 'F',
    'last_login': 'G',
    'last_race': 'H',
    'recent_30days_count': 'I',
    'prev_30days_count': 'J'
}

license_style_mapping = {
    'A': [102, 204, 255],
    'B': [153, 255, 153],
    'C': [255, 255, 153],
    'D': [255, 204, 153],
    'R': [255, 153, 153]
}


def calculate_cell_background_color(rgb):
    return {
        "red": rgb[0]/255,
        "green": rgb[1]/255,
        "blue": rgb[2]/255
    }


async def parse_pilots(pilots_sheet: Worksheet, pilots_count, message, settings_link):
    good_pilots = []
    bad_pilots = []
    for index in range(2, pilots_count + 2):  # Старт со 2й строки
        pilot_data = pilots_sheet.row_values(index)
        time.sleep(1)

        await message.edit(embed=discord.Embed(title=f'Найдено пилотов: *{pilots_count}*',
                                           description=f'**⏳ Шаг 1**\n⬇️ Загрузка из [Google Sheets]({settings_link}): {pilot_data[0]} ({index-1}/{pilots_count})',
                                           colour=discord.Color.green()))

        # 0 = Никнейм, 1 = Имя, 2 = Возраст, 3 = iRacing ID, 4 = Discord ID
        if len(pilot_data[3]) > 0:
            good_pilots.append({
                'nickname': pilot_data[0],
                'name': pilot_data[1],
                'age': pilot_data[2],
                'ir_id': pilot_data[3],
                'ds_id': pilot_data[4]
            })
        else:
            bad_pilots.append({
                'nickname': pilot_data[0][:25],
                'name': pilot_data[1],
                'age': pilot_data[2]
            })

    return good_pilots, bad_pilots


async def parse_member_profile(good_pilots, iracing_client, message):
    for index, good_pilot in enumerate(good_pilots, start=2): # со 2й строки таблицы
        await message.edit(embed=discord.Embed(title=f'Найдено пилотов: *{len(good_pilots)}*',
                                           description=f'**⏳ Шаг 2**\n✅ Загрузка из Google Sheets\n⬇️ Загрузка из iRacing: {good_pilot['nickname']} ({index-1}/{len(good_pilots)})',
                                           colour=discord.Color.green()))

        ir_profile = iracing_client.member_profile(cust_id=good_pilot['ir_id'])
        time.sleep(0.5)
        good_pilot['ir'] = {}

        licenses = ir_profile['member_info']['licenses']
        for car_license in licenses:
            if 'Dirt' not in car_license['category_name']:
                good_pilot['ir'][car_license['category_name']] = {
                    'safety_class': car_license['group_name'][-1] if car_license['group_name'].startswith('Class') else 'R',
                    'safety_rating': car_license['safety_rating'],
                    'irating': car_license['irating']
                }

        last_login = ir_profile['member_info']['last_login'][:10] # обрезка YYYY-MM-DD
        good_pilot['ir']['last_login'] = f'{datetime.strptime(last_login, '%Y-%m-%d').strftime('%d.%m.%Y')}'

        last_login_diff = (datetime.today() - datetime.strptime(last_login, '%Y-%m-%d')).days
        last_login_days = 'дней'
        if last_login_diff % 10 in [1]:
            last_login_days = 'день'
        elif last_login_diff % 10 in [2,3,4]:
            last_login_days = 'дня'

        good_pilot['ir']['last_login_diff'] = f'{'сегодня' if last_login_diff == 0 else f'{last_login_diff} {last_login_days} назад'}'

        if ir_profile['recent_events'] is not None:
            races = ir_profile['recent_events']
            for race in races:
                if race['event_type'] == 'RACE':
                    good_pilot['ir']['last_race'] = {
                        'race_name': race['event_name'],
                        'race_start_time': datetime.strptime(race['start_time'][:10], '%Y-%m-%d').strftime('%d.%m.%Y'),
                        'race_starting_position': race['starting_position'],
                        'race_finish_position': race['finish_position']
                    }
                    break
        else:
            good_pilot['ir']['last_race'] = None

        if ir_profile['activity'] is not None:
            good_pilot['ir']['activity'] = {
                'recent_30days_count': ir_profile['activity']['recent_30days_count'],
                'prev_30days_count': ir_profile['activity']['prev_30days_count'],
                'consecutive_weeks': ir_profile['activity']['consecutive_weeks'],
                'most_consecutive_weeks': ir_profile['activity']['most_consecutive_weeks']
        }
        else:
            good_pilot['ir']['activity'] = None

    return good_pilots


async def update_pilots(pilots_sheet: Worksheet, good_pilots, message, public_link):
    for index, good_pilot in enumerate(good_pilots, start=2): # со 2й строки таблицы
        await message.edit(embed=discord.Embed(title=f'Настроенных пилотов: *{len(good_pilots)}*',
                                           description=f'**⏳ Шаг 3**\n✅ Загрузка из Google Sheets\n✅ Загрузка из iRacing\n⬆️Выгрузка в [Google Sheets]({public_link}): {good_pilot['nickname']} ({index-1}/{len(good_pilots)})',
                                           colour=discord.Color.green()))

        pilots_sheet.update_acell(f'{cells_mapping['nickname']}{index}', f'{good_pilot['nickname']}')
        time.sleep(1)
        pilots_sheet.update_acell(f'{cells_mapping['name']}{index}', f'{good_pilot['name']}')
        time.sleep(1)
        pilots_sheet.update_acell(f'{cells_mapping['age']}{index}', f'{good_pilot['age']}')
        time.sleep(1)

        for series in  iracing_series:
            pilots_sheet.update_acell(f'{cells_mapping[series]}{index}',
                                   f'[{good_pilot['ir'][series]['safety_class']}] {round(good_pilot['ir'][series]['safety_rating'], 1)}\n{round(good_pilot['ir'][series]['irating']/1000, 1)}k')
            time.sleep(1)
            pilots_sheet.format(f'{cells_mapping[series]}{index}', {
                "backgroundColor": calculate_cell_background_color(license_style_mapping[good_pilot['ir'][series]['safety_class']])
            })
            time.sleep(1)

        pilots_sheet.update_acell(f'{cells_mapping['last_login']}{index}',
                               f'{good_pilot['ir']['last_login']}\n({good_pilot['ir']['last_login_diff']})')
        time.sleep(1)

        if 'last_race' in good_pilot['ir']:
            pilots_sheet.update_acell(f'{cells_mapping['last_race']}{index}',
                                   f'{good_pilot['ir']['last_race']['race_name']} ({good_pilot['ir']['last_race']['race_start_time']})\nQ{good_pilot['ir']['last_race']['race_starting_position']} → P{good_pilot['ir']['last_race']['race_finish_position']}')
            time.sleep(1)


class Pilots(commands.Cog, name='Pilots'):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.get_cog('ConfigUtils').config

        self.iracing_client = self.bot.get_cog('IracingUtils').iracing_client

        self.settings_sheet = self.bot.get_cog('GoogleSheetsUtils').settings_sheet
        self.public_sheet = self.bot.get_cog('GoogleSheetsUtils').public_sheet


    @commands.command(name='update_pilots')
    async def update_pilots_command(self, ctx):
        pilots_sheet = self.settings_sheet.worksheet('Участники')
        pilots_count = len(pilots_sheet.col_values(1)) - 1 # Минус заголовок
        settings_link = f'https://docs.google.com/spreadsheets/d/{self.config['Keys']['settings_sheet']}'

        pilots_public_sheet = self.public_sheet.worksheet('Пилоты')
        public_link = f'https://docs.google.com/spreadsheets/d/{self.config['Keys']['public_sheet']}'

        message = await ctx.send(embed=discord.Embed(title=f'Найдено пилотов: *{pilots_count}*',
                                           description=f'⏳ Обновление...',
                                           colour=discord.Color.green()))

        # Парсинг Google Docs (закрытый)
        # [Пилоты] -> {}
        try:
            good_pilots, bad_pilots = await parse_pilots(pilots_sheet, pilots_count, message, settings_link)
        except:
            await ctx.send(embed=discord.Embed(title=f'ОШИБКА',
                                               description=f'При чтении листа [Пилоты]',
                                               colour=discord.Color.red()))
        else:
            # Парсинг iRacing
            # /member_profile -> ['ir']
            good_pilots = await parse_member_profile(good_pilots, self.iracing_client, message)

            # Очистка
            # Очистка
            cleanup(pilots_public_sheet)

            # Апдейт Google Docs (публичный)
            await update_pilots(pilots_public_sheet, good_pilots, message, public_link)

            # OK
            final_good_pilots = []
            for good_pilot in good_pilots:
                final_good_pilots.append(good_pilot['nickname'])
            await message.edit(embed=discord.Embed(title=f'Готово',
                                                   description=f'**✅ [Обновлено]({public_link}) {len(good_pilots)} пилотов:**\n{'\n'.join(final_good_pilots)}',
                                                   colour=discord.Color.green()))

            # Not OK
            if len(bad_pilots) != 0:
                final_bad_pilots = []
                for bad_pilot in bad_pilots:
                    final_bad_pilots.append(bad_pilot['nickname'])
                await ctx.send(embed=discord.Embed(title=f'Ошибки',
                                           description=f'**❌ Не обновлено {len(final_bad_pilots)} пилотов (нет iRacing ID):**\n{'\n'.join(final_bad_pilots)}',
                                           colour=discord.Color.red()))


async def setup(bot: commands.Cog):
    await bot.add_cog(Pilots(bot))