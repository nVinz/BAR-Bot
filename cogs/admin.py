import configparser
import gspread
import discord
from discord.ext import commands
from iracingdataapi.client import irDataClient
from itertools import groupby
from datetime import datetime

class Cog1(commands.Cog, name='Cog1'):
    def __init__(self, bot):
        self.bot = bot
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        self.iracing_client = irDataClient(username=self.config['Logins']['iracing'],
                                           password=self.config['Passwords']['iracing'])
        self.settings_sheet = gspread.service_account().open_by_key(self.config['Keys']['settings_sheet'])


    @commands.command(name='e')
    async def embed_test(self, ctx):
        embed = discord.Embed(title="Title", description="Desc", colour=discord.Color.green())
        embed.add_field(name="Name", value="you can make as much as fields you like to")
        embed.add_field(name="Name1", value="you can make as much as fields you like to1")
        embed.set_author(name='asd')
        embed.set_footer(text="footer")
        await ctx.send(embed=embed)


    @commands.command(name='u1')
    async def update_pilots(self, ctx):
        pilots_sheet = self.settings_sheet.worksheet('Участники')
        pilots_count = len(pilots_sheet.col_values(1)) - 1 # Минус заголовок

        await ctx.send(embed=discord.Embed(title=f'Найдено пилотов: *{pilots_count}*',
                                           description=f'🕐 Обновление...',
                                           colour=discord.Color.green()))

        # Парсинг Google Docs
        good_pilots = []
        bad_pilots = []
        for index in range(2, pilots_count + 2): # Старт со 2й строки
            pilot_data = pilots_sheet.row_values(index)

            # 0 = Никнейм, 1 = Имя, 2 = Возраст, 3 = iRacing ID, 4 = Discord ID
            if pilot_data[3] != '' and pilot_data[4] != '':
                good_pilots.append({
                    'nickname': pilot_data[0],
                    'name': pilot_data[1],
                    'age': pilot_data[2],
                    'ir_id': pilot_data[3],
                    'ds_id': pilot_data[4]
                })
            else:
                bad_pilots.append({
                    'nickname': pilot_data[0],
                    'name': pilot_data[1],
                    'age': pilot_data[2]
                })

        # Парсинг iRacing
        for index, good_pilot in enumerate(good_pilots, start=2): # со 2й строки таблицы
            ir_profile = self.iracing_client.member_profile(cust_id=good_pilot['ir_id'])
            good_pilot['ir'] = {}

            last_login = ir_profile['member_info']['last_login'][:10] # обрезка YYYY-MM-DD
            last_login_diff = (datetime.today() - datetime.strptime(last_login, '%Y-%m-%d')).days

            last_login_days = 'дней'
            if last_login_diff % 10 in [1]:
                last_login_days = 'день'
            elif last_login_diff % 10 in [2,3,4]:
                last_login_days = 'дня'

            last_activity = 'сегодня' if last_login_diff == 0 else f'{last_login_diff} {last_login_days} назад'
            good_pilot['ir']['last_activity'] = f'{datetime.strptime(last_login, '%Y-%m-%d').strftime('%d.%m.%Y')}\n({last_activity})'

            licenses = ir_profile['member_info']['licenses']
            good_pilot['ir']['licenses'] = []
            for car_license in licenses:
                if 'Dirt' not in car_license['group_name']:
                    good_pilot['ir']['licenses'].append({
                        
                    })
                    license_safety_rating = car_license['group_name']
                    license_safety_rating = license_safety_rating[-1] if license_safety_rating.startswith('Class') else 'R'
                    license_irating = car_license['irating']

        result = discord.Embed(title=f'Пилоты', colour=discord.Color.blue())
        for good_pilot in good_pilots:
            result.add_field(name=good_pilot['nickname'], value=f'{good_pilot['name']}, {good_pilot['age']}')
        await ctx.send(embed=result)

        if len(bad_pilots) == 0:
            await ctx.send(embed=discord.Embed(title=f'Обновлено пилотов: *{len(good_pilots)}* из *{pilots_count}*',
                                               description='✅',
                                               colour=discord.Color.green()))
        else:
            bad_result = discord.Embed(title=f'Обновлено пилотов: *{len(good_pilots)}* из *{pilots_count}*',
                                       description='❌ Отсутствуют ID (iR/Discord) у:',
                                       colour=discord.Color.red())
            for bad_pilot in bad_pilots:
                bad_result.add_field(name=bad_pilot['nickname'], value=f'{bad_pilot['name']}')
            await ctx.send(embed=bad_result)


    @commands.command(name='u2')
    async def update_teams(self, ctx):
        #teams_sheet = self.settings_sheet.worksheet('Команды')
        await ctx.send(embed=discord.Embed(title=f'WIP',
                                           colour=discord.Color.yellow()))

    @commands.command(name='u3')
    async def update_teams(self, ctx):
        pilots_sheet = self.settings_sheet.worksheet('Участники')
        pilots_count = len(pilots_sheet.col_values(1)) - 1 # Минус заголовок

        teams_sheet = self.settings_sheet.worksheet('Команды')
        teams_count = len(teams_sheet.col_values(1)) - 1 # Минус заголовок

        crews_sheet = self.settings_sheet.worksheet('Экипажи')
        crews_count = len(crews_sheet.col_values(1)) - 1 # Минус заголовок

        await ctx.send(embed=discord.Embed(title=f'Найдено экипажей: *{crews_count}*',
                                           description=f'🕐 Обновление...',
                                           colour=discord.Color.green()))

        good_pilots = []
        bad_pilots = []
        for index in range(2, pilots_count + 2): # Старт со 2й строки
            pilot_data = pilots_sheet.row_values(index)

            # 0 = Никнейм, 1 = Имя, 2 = Возраст, 3 = iRacing ID, 4 = Discord ID
            if pilot_data[3] != '' and pilot_data[4] != '':
                good_pilots.append({
                    'nickname': pilot_data[0],
                    'name': pilot_data[1],
                    'age': pilot_data[2],
                    'ir_id': pilot_data[3],
                    'ds_id': pilot_data[4]
                })
            else:
                bad_pilots.append({
                    'nickname': pilot_data[0],
                    'name': pilot_data[1],
                    'age': pilot_data[2]
                })

        teams = []
        for index in range(2, teams_count + 2): # Старт со 2й строки
            team_data = teams_sheet.row_values(index)

            # 0 = Название
            teams.append({
                'name': team_data[0]
            })

        good_crews = []
        bad_crews = []
        for index in range(2, crews_count + 2): # Старт со 2й строки
            crew_data = crews_sheet.row_values(index)

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

        good_crews.sort(key=lambda p: p['team_name'])
        grouped_good_crews = {key: list(group) for key, group in groupby(good_crews, key=lambda p: p['team_name'])}

        result = discord.Embed(title=f'Экипажи', colour=discord.Color.blue())
        for key, value in grouped_good_crews.items():
            crew_name = key
            crew_former = []
            crew_pilots = []
            for good_crew_pilots in value:
                if good_crew_pilots['role'] == 'Former':
                    crew_former.append(f'{good_crew_pilots['nickname']}👑')
                else:
                    crew_pilots.append(good_crew_pilots['nickname'])
            #crew_pilots = [item['nickname'] for item in good_crew]
            result.add_field(name=crew_name, value=f'{'\n'.join(crew_former + crew_pilots)}')
        await ctx.send(embed=result)

        if len(bad_crews) == 0:
            await ctx.send(embed=discord.Embed(title=f'Обновлено экипажей: *{len(good_crews)}* из *{crews_count}*',
                                               description='✅',
                                               colour=discord.Color.green()))
        else:
            bad_result = discord.Embed(title=f'Обновлено экипажей: *{len(good_crews)}* из *{crews_count}*',
                                       description='❌ Не удалось настроить:',
                                       colour=discord.Color.red())
            for bad_crew in bad_crews:
                bad_result.add_field(name=bad_crew['team_name'], value=f'{bad_crew['nickname']} ({bad_crew["role"]})')
            await ctx.send(embed=bad_result)


async def setup(bot: commands.Cog):
    await bot.add_cog(Cog1(bot))