import discord
from discord.ext import commands

class TestCog(commands.Cog, name='TestCog'):
    def __init__(self, bot):
        self.bot = bot
        self.shared_data = "Hello from CogA!"

    @commands.command(name='e')
    async def embed_test(self, ctx):
        embed = discord.Embed(title="Title", description="Desc", colour=discord.Color.green())
        embed.add_field(name="Name", value="you can make as much as fields you like to")
        embed.add_field(name="Name1", value="you can make as much as fields you like to1")
        embed.set_author(name='asd')
        embed.set_footer(text="footer")
        await ctx.send(embed=embed)

async def setup(bot: commands.Cog):
    await bot.add_cog(TestCog(bot))