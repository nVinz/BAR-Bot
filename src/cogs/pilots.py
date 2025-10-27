import os
import time
import discord
from discord.ext import commands
from datetime import datetime
from gspread import Worksheet
from src.utils.google_sheets_utils import cleanup


iracing_series = ['Sports Car', 'Formula Car', 'Oval']

cells_mapping = {
    'nickname': 'A',
    'name': 'B',
    'age': 'C',
    'Sports Car': 'D',
    'Sports Car Change': 'E',
    'Formula Car': 'F',
    'Formula Car Change': 'G',
    'Oval': 'H',
    'Oval Change': 'I',
    'last_login': 'J',
    'last_race': 'K',
    'recent_30days_count': 'L',
    'prev_30days_count': 'M'
}

last_cell = 'M'

# Old background
"""license_style_mapping = {
    'A': [102, 204, 255],
    'B': [153, 255, 153],
    'C': [255, 255, 153],
    'D': [255, 204, 153],
    'R': [255, 153, 153]
}"""

license_style_mapping = {
    'A': [112, 169, 255],
    'B': [113, 224, 113],
    'C': [241, 194, 50],
    'D': [255, 153, 51],
    'R': [255, 127, 127]
}


def calculate_cell_background_color(rgb):
    return {
        "red": rgb[0]/255,
        "green": rgb[1]/255,
        "blue": rgb[2]/255
    }


async def parse_pilots(pilots_sheet: Worksheet, pilots_count, message):
    settings_link = f'https://docs.google.com/spreadsheets/d/{os.environ['SETTINGS_SHEET']}'
    good_pilots = []
    bad_pilots = []

    await message.edit(embed=discord.Embed(title=f'Найдено пилотов: *{pilots_count}*',
                                           description=f'**⏳ Шаг 1**\n⬇️ Загрузка из [Google Sheets]({settings_link})...',
                                           colour=discord.Color.green()))

    for index in range(2, pilots_count + 2):  # Старт со 2й строки
        pilot_data = pilots_sheet.row_values(index)
        time.sleep(1)

        """await message.edit(embed=discord.Embed(title=f'Найдено пилотов: *{pilots_count}*',
                                           description=f'**⏳ Шаг 1**\n⬇️ Загрузка из [Google Sheets]({settings_link}): {pilot_data[0]} ({index-1}/{pilots_count})',
                                           colour=discord.Color.green()))"""

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
    await message.edit(embed=discord.Embed(title=f'Найдено пилотов: *{len(good_pilots)}*',
                                       description=f'**⏳ Шаг 2**\n✅ Загрузка из Google Sheets\n⬇️ Загрузка из iRacing...',
                                       colour=discord.Color.green()))

    for index, good_pilot in enumerate(good_pilots, start=2): # со 2й строки таблицы
        """await message.edit(embed=discord.Embed(title=f'Найдено пилотов: *{len(good_pilots)}*',
                                           description=f'**⏳ Шаг 2**\n✅ Загрузка из Google Sheets\n⬇️ Загрузка из iRacing: {good_pilot['nickname']} ({index-1}/{len(good_pilots)})',
                                           colour=discord.Color.green()))"""

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

        good_pilot['ir']['recent_races'] = []
        for event in ir_profile['recent_events']:
            if event['event_type'] == 'RACE':
                result = iracing_client.result(event['subsession_id'])
                race_result = [p for p in result['session_results'] if p['simsession_name'] == 'RACE'][0]
                if 'cust_id' in race_result['results'][0]:
                    user_result = [p for p in race_result['results'] if p['cust_id'] == int(good_pilot['ir_id'])]
                    if len(user_result) > 0:
                        user_result = user_result[0]
                        good_pilot['ir']['recent_races'].append({
                            'subsession_id': event['subsession_id'],
                            'license_category': result['license_category'].replace('_', ' '),
                            'sof': result['event_strength_of_field'],
                            'incs': user_result['incidents'],
                            'irating_change': user_result['newi_rating'] - user_result['oldi_rating'],
                            'license_change': round((user_result['new_sub_level'] - user_result['old_sub_level']) / 100, 1)
                        })
                elif 'team_id' in race_result['results'][0]:
                    for res in race_result['results']:
                        if len([p for p in res['driver_results'] if p['cust_id'] == int(good_pilot['ir_id'])]):
                            user_result = [p for p in res['driver_results'] if p['cust_id'] == int(good_pilot['ir_id'])][0]
                            good_pilot['ir']['recent_races'].append({
                                'subsession_id': event['subsession_id'],
                                'license_category': result['license_category'].replace('_', ' '),
                                'sof': result['event_strength_of_field'],
                                'incs': user_result['incidents'],
                                'irating_change': user_result['newi_rating'] - user_result['oldi_rating'],
                                'license_change': round((user_result['new_sub_level'] - user_result['old_sub_level']) / 100, 1)
                            })


        if len(good_pilot['ir']['recent_races']) > 0:
            for recent_race in good_pilot['ir']['recent_races']:
                license_category = recent_race['license_category']

                if license_category != 'Dirt Oval':
                    if 'license_change' in good_pilot['ir'][license_category]:
                        good_pilot['ir'][license_category]['license_change'] = round(good_pilot['ir'][license_category]['license_change'] + recent_race['license_change'], 1)
                    else:
                        good_pilot['ir'][license_category]['license_change'] = round(recent_race['license_change'], 1)

                    if 'irating_change' in good_pilot['ir'][license_category]:
                        good_pilot['ir'][license_category]['irating_change'] = round(good_pilot['ir'][license_category]['irating_change'] + recent_race['irating_change'])
                    else:
                        good_pilot['ir'][license_category]['irating_change'] = round(recent_race['license_change'])

        last_login = ir_profile['member_info']['last_login'][:10] # обрезка YYYY-MM-DD
        good_pilot['ir']['last_login'] = f'{datetime.strptime(last_login, '%Y-%m-%d').strftime('%d.%m.%Y')}'

        last_login_diff = (datetime.today() - datetime.strptime(last_login, '%Y-%m-%d')).days
        good_pilot['ir']['last_login_diff_raw'] = last_login_diff

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

        """if ir_profile['activity'] is not None:
            good_pilot['ir']['activity'] = {
                'recent_30days_count': ir_profile['activity']['recent_30days_count'],
                'prev_30days_count': ir_profile['activity']['prev_30days_count'],
                'consecutive_weeks': ir_profile['activity']['consecutive_weeks'],
                'most_consecutive_weeks': ir_profile['activity']['most_consecutive_weeks']
        }
        else:
            good_pilot['ir']['activity'] = None"""

        pilot_activity = 0
        if good_pilot['ir']['last_login_diff_raw'] in list(range(0, 2)):
            pilot_activity +=3
        elif good_pilot['ir']['last_login_diff_raw'] in list(range(2, 7)):
            pilot_activity +=2
        elif good_pilot['ir']['last_login_diff_raw'] in list(range(7, 14)):
            pilot_activity +=1

        if len(good_pilot['ir']['recent_races']) > 2:
            pilot_activity +=2
        elif len(good_pilot['ir']['recent_races']) == 1:
            pilot_activity +=1
        good_pilot['ir']['activity'] = pilot_activity

    return good_pilots


async def update_pilots(pilots_sheet: Worksheet, good_pilots, message):
    public_link = f'https://docs.google.com/spreadsheets/d/{os.environ['PUBLIC_SHEET']}'
    await message.edit(embed=discord.Embed(title=f'Настроенных пилотов: *{len(good_pilots)}*',
                                           description=f'**⏳ Шаг 3**\n✅ Загрузка из Google Sheets\n✅ Загрузка из iRacing\n⬆️Выгрузка в [Google Sheets]({public_link})...',
                                           colour=discord.Color.green()))

    for index, good_pilot in enumerate(good_pilots, start=2): # со 2й строки таблицы
        """await message.edit(embed=discord.Embed(title=f'Настроенных пилотов: *{len(good_pilots)}*',
                                           description=f'**⏳ Шаг 3**\n✅ Загрузка из Google Sheets\n✅ Загрузка из iRacing\n⬆️Выгрузка в [Google Sheets]({public_link}): {good_pilot['nickname']} ({index-1}/{len(good_pilots)})',
                                           colour=discord.Color.green()))"""

        pilots_sheet.update_acell(f'{cells_mapping['nickname']}{index}', f'{good_pilot['nickname']}')
        time.sleep(1)
        pilots_sheet.update_acell(f'{cells_mapping['name']}{index}', f'{good_pilot['name']}')
        time.sleep(1)
        pilots_sheet.update_acell(f'{cells_mapping['age']}{index}', f'{good_pilot['age']}')
        time.sleep(1)

        for series in iracing_series:
            safety_class = good_pilot['ir'][series]['safety_class']
            safety_rating = round(good_pilot['ir'][series]['safety_rating'], 1)
            irating = round(good_pilot['ir'][series]['irating']/1000, 1)

            pilots_sheet.update_acell(f'{cells_mapping[series]}{index}',
                                   f'[{safety_class}] {safety_rating}\n{irating}k')
            time.sleep(1)
            pilots_sheet.format(f'{cells_mapping[series]}{index}', {
                'textFormat': {
                    'foregroundColor': calculate_cell_background_color(license_style_mapping[good_pilot['ir'][series]['safety_class']]),
                    'bold': True
                }
            })
            time.sleep(1)

            license_change = ''
            if 'license_change' in good_pilot['ir'][series]:
                license_change = good_pilot['ir'][series]['license_change']
                if license_change > 0:
                    license_change = f'↑{abs(license_change)}'
                elif license_change < 0:
                    license_change = f'↓{abs(license_change)}'
                else:
                    license_change = f'~{abs(license_change)}'

            irating_change = ''
            if 'irating_change' in good_pilot['ir'][series]:
                irating_change = good_pilot['ir'][series]['irating_change']
                if irating_change > 0:
                    irating_change = f'↑{abs(irating_change)}'
                elif irating_change < 0:
                    irating_change = f'↓{abs(irating_change)}'
                else:
                    irating_change = f'~{abs(irating_change)}'

            pilots_sheet.update_acell(f'{cells_mapping[f'{series} Change']}{index}',
                                   f'{license_change}\n{irating_change}')
            time.sleep(1)
            pilots_sheet.format(f'{cells_mapping[f'{series} Change']}{index}', {
                'textFormat': {
                    'foregroundColor': calculate_cell_background_color(license_style_mapping[good_pilot['ir'][series]['safety_class']]),
                    'bold': True
                }
            })
            time.sleep(1)

        pilots_sheet.update_acell(f'{cells_mapping['last_login']}{index}',
                               f'{good_pilot['ir']['last_login']}\n({good_pilot['ir']['last_login_diff']})')
        time.sleep(1)

        if good_pilot['ir']['last_login_diff_raw'] > 7:
            pilots_sheet.format(f'{cells_mapping['last_login']}{index}', {
                'textFormat': {
                    'foregroundColor': {
                        "red": 1.,
                        "green": 0.3,
                        "blue": 0.3
                    }
                }
            })
            time.sleep(1)

        if 'last_race' in good_pilot['ir']:
            pilots_sheet.update_acell(f'{cells_mapping['last_race']}{index}',
                                   f'{good_pilot['ir']['last_race']['race_name']} ({good_pilot['ir']['last_race']['race_start_time']})\nQ{good_pilot['ir']['last_race']['race_starting_position']} → P{good_pilot['ir']['last_race']['race_finish_position']}')
            time.sleep(1)

        if index % 2 == 0:
            pilots_sheet.format(f'A{index}:{last_cell}{index}', {
                "backgroundColor": {
                    "red": 0.93,
                    "green": 0.93,
                    "blue": 0.93
                }
            })


class Pilots(commands.Cog, name='Pilots'):
    def __init__(self, bot):
        self.bot = bot

        self.iracing_client = self.bot.get_cog('IracingUtils').iracing_client

        self.settings_sheet = self.bot.get_cog('GoogleSheetsUtils').settings_sheet
        self.public_sheet = self.bot.get_cog('GoogleSheetsUtils').public_sheet


    @commands.command(name='update_pilots')
    async def update_pilots_command(self, ctx):
        pilots_sheet = self.settings_sheet.worksheet('Участники')
        pilots_count = len(pilots_sheet.col_values(1)) - 1 # Минус заголовок

        pilots_public_sheet = self.public_sheet.worksheet('Пилоты')

        message = await ctx.send(embed=discord.Embed(title=f'Найдено пилотов: *{pilots_count}*',
                                           description=f'⏳ Обновление...',
                                           colour=discord.Color.green()))

        # Парсинг Google Docs (закрытый)
        # [Пилоты] -> {}
        try:
            good_pilots, bad_pilots = await parse_pilots(pilots_sheet, pilots_count, message)
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
            await update_pilots(pilots_public_sheet, good_pilots, message)

            # OK
            final_good_pilots = []
            for good_pilot in good_pilots:
                final_good_pilots.append(good_pilot['nickname'])
            await message.edit(embed=discord.Embed(title=f'Готово',
                                                   description=f'**✅ [Обновлено](https://docs.google.com/spreadsheets/d/{os.environ['PUBLIC_SHEET']}) {len(good_pilots)} пилотов:**\n{'\n'.join(final_good_pilots)}',
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
