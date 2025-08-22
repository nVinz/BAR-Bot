import time
import discord
from discord.ext import commands
from itertools import groupby
from gspread import Worksheet
from src.cogs.pilots import parse_pilots, parse_member_profile
from src.cogs.teams import parse_teams
from src.utils.google_sheets_utils import cleanup


iracing_series = ['Sports Car']

cells_mapping = {
    'team_name': 'A',
    'nickname': 'B',
    'sof': 'C',
    'avg_age': 'D'
}


async def parse_crews(crews_sheet: Worksheet, crews_count, good_pilots, teams, message, settings_link):
    good_crews = []
    bad_crews = []
    for index in range(2, crews_count + 2):  # Старт со 2й строки
        crew_data = crews_sheet.row_values(index)
        time.sleep(1)

        await message.edit(embed=discord.Embed(title=f'Найдено настроек экипажей: *{crews_count}*',
                                           description=f'**⏳ Шаг 1**\n⬇️ Загрузка из [Google Sheets]({settings_link}): {crew_data[0]} - {crew_data[1]} ({index-1}/{crews_count})',
                                           colour=discord.Color.green()))

        # 0 = Команда, 1 = Никнейм, 2 = Роль
        pilot_is_correct = True if len([p for p in good_pilots if p['nickname'] == crew_data[1]]) == 1 else False
        team_is_correct = True if len([p for p in teams if p['name'] == crew_data[0]]) else False

        if pilot_is_correct and team_is_correct:
            good_crews.append({
                'team_name': crew_data[0],
                'nickname': crew_data[1],
                'role': crew_data[2],
            })
        else:
            bad_crews.append({
                'team_name': crew_data[0],
                'nickname': crew_data[1],
                'role': crew_data[2],
            })

    return good_crews, bad_crews


def calculate_averages(grouped_good_crews, good_pilots):
    new_good_crews = {}

    for key, value in grouped_good_crews.items():
        new_good_crews[key] = {}

        sof = []
        age = []
        new_good_crews[key]['pilots'] = []

        for pilot in value:
            good_pilot = [p for p in good_pilots if p['nickname'] == pilot['nickname']][0]
            if pilot['role'] == 'Former':
                good_pilot['nickname'] = f'{pilot['nickname']} 👑'
            new_good_crews[key]['pilots'].append(good_pilot)

            good_pilot['role'] = pilot['role']

            for series in iracing_series:
                sof.append(good_pilot['ir'][series]['irating'])

            age.append(int(good_pilot['age']))

        new_good_crews[key]['sof'] = sum(sof)/len(sof)
        new_good_crews[key]['avg_age'] = sum(age)/len(age)

    return new_good_crews


async def update_crews(crews_sheet: Worksheet, grouped_good_crews, message, public_link):
    index = 2 # со 2й строки таблицы
    crew_index = 1
    for key, value in grouped_good_crews.items():
        await message.edit(embed=discord.Embed(title=f'Сформировано экипажей: *{len(grouped_good_crews)}*',
                                           description=f'**⏳ Шаг 3**\n✅ Загрузка из Google Sheets\n✅ Загрузка из iRacing\n⬆️Выгрузка в [Google Sheets]({public_link}): {key} ({crew_index}/{len(grouped_good_crews)})',
                                           colour=discord.Color.green()))
        crew_index += 1

        for pilot in value['pilots']:
            crews_sheet.update_acell(f'{cells_mapping['nickname']}{index}', f'{pilot['nickname']}')
            time.sleep(1)

            if pilot == value['pilots'][-1]:
                crews_sheet.update_acell(f'{cells_mapping['team_name']}{index}', f'{key}')
                time.sleep(1)
                crews_sheet.merge_cells(f'{cells_mapping['team_name']}{index}:{cells_mapping['team_name']}{index - (len(value['pilots']) - 1)}', merge_type='MERGE_ALL')
                time.sleep(1)

                crews_sheet.update_acell(f'{cells_mapping['sof']}{index}', f'{round(value['sof']/1000, 1)}k')
                time.sleep(1)
                crews_sheet.merge_cells(f'{cells_mapping['sof']}{index}:{cells_mapping['sof']}{index - (len(value['pilots']) - 1)}', merge_type='MERGE_ALL')
                time.sleep(1)

                crews_sheet.update_acell(f'{cells_mapping['avg_age']}{index}', f'{round(value['avg_age'])}')
                time.sleep(1)
                crews_sheet.merge_cells(f'{cells_mapping['avg_age']}{index}:{cells_mapping['avg_age']}{index - (len(value['pilots']) - 1)}', merge_type='MERGE_ALL')
                time.sleep(1)

            index += 1


class Crews(commands.Cog, name='Crews'):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.get_cog('ConfigUtils').config

        self.iracing_client = self.bot.get_cog('IracingUtils').iracing_client

        self.settings_sheet = self.bot.get_cog('GoogleSheetsUtils').settings_sheet
        self.public_sheet = self.bot.get_cog('GoogleSheetsUtils').public_sheet


    @commands.command(name='update_crews')
    async def update_crews_command(self, ctx):
        pilots_sheet = self.settings_sheet.worksheet('Участники')
        pilots_count = len(pilots_sheet.col_values(1)) - 1  # Минус заголовок
        settings_link = f'https://docs.google.com/spreadsheets/d/{self.config['Keys']['settings_sheet']}'

        teams_sheet = self.settings_sheet.worksheet('Команды')
        teams_count = len(teams_sheet.col_values(1)) - 1  # Минус заголовок

        crews_sheet = self.settings_sheet.worksheet('Экипажи')
        crews_count = len(crews_sheet.col_values(1)) - 1  # Минус заголовок

        crews_public_sheet = self.public_sheet.worksheet('Экипажи')
        public_link = f'https://docs.google.com/spreadsheets/d/{self.config['Keys']['public_sheet']}'

        message = await ctx.send(embed=discord.Embed(title=f'Найдено настроек экипажей: *{crews_count}*',
                                           description=f'🕐 Обновление...',
                                           colour=discord.Color.green()))

        # Парсинг Google Docs
        # [Пилоты]
        good_pilots, bad_pilots = await parse_pilots(pilots_sheet, pilots_count, message, settings_link)
        # [Команды]
        teams = await parse_teams(teams_sheet, teams_count, message, settings_link)
        # [Экипажи]
        good_crews, bad_crews = await parse_crews(crews_sheet, crews_count, good_pilots, teams, message, settings_link)

        # Парсинг iRacing
        # /member_profile -> ['ir']
        good_pilots = await parse_member_profile(good_pilots, self.iracing_client, message)

        # Группировка
        good_crews.sort(key=lambda p: p['team_name'])
        grouped_good_crews = {key: list(group) for key, group in groupby(good_crews, key=lambda p: p['team_name'])}

        # Join good_crews + good_pilots
        grouped_good_crews = calculate_averages(grouped_good_crews, good_pilots)

        # Очистка
        cleanup(crews_public_sheet)

        # Апдейт Google Docs (публичный)
        await update_crews(crews_public_sheet, grouped_good_crews, message, public_link)

        # OK
        result = discord.Embed(title=f'Готово',
                               description=f'**✅ [Сформировано экипажей]({public_link}) - {len(grouped_good_crews)}:**',
                               colour=discord.Color.green())
        for key, value in grouped_good_crews.items():
            crew_former = []
            crew_pilots = []
            for good_crew_pilots in value['pilots']:
                if good_crew_pilots['role'] == 'Former':
                    crew_former.append(good_crew_pilots['nickname'])
                else:
                    crew_pilots.append(good_crew_pilots['nickname'])
            result.add_field(name=key, value=f'{'\n'.join(crew_former + crew_pilots)}')
        await message.edit(embed=result)

        # Not OK
        if len(bad_crews) != 0:
            final_bad_crews = []
            for bad_crew in bad_crews:
                final_bad_crews.append(f'{bad_crew['team_name']} - {bad_crew['nickname']} ({bad_crew["role"]})')
            await ctx.send(embed=discord.Embed(title=f'Ошибки',
                                       description=f'**❌ Не обновлены экпиажи - {len(final_bad_crews)}:**\n{'\n'.join(final_bad_crews)}',
                                       colour=discord.Color.red()))

async def setup(bot: commands.Cog):
    await bot.add_cog(Crews(bot))