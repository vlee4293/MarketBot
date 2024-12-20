import discord
from discord.ext import commands
from discord.embeds import Embed
from bot import MarketBot
from datetime import datetime, timedelta

class Market(commands.Cog):
    def __init__(self, client: MarketBot):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{__name__} is online!')

    @commands.guild_only()
    @commands.command(name='balance', aliases=['bal'])
    async def balance(self, ctx: commands.Context, option = None):
        async with self.client.db.async_session() as session:
            account = await self.client.db.accounts.get_or_create_account(session, ctx.author)
            embed = Embed(
                title=f'{ctx.author.display_name}\'s Balance', 
                description=f'${account.balance:.2f}'
            )
            await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name='bet')
    async def bet(self, ctx: commands.Context, amount):
        async with self.client.db.async_session() as session:
            account = await self.client.db.accounts.get_or_create_account(session, ctx.author)
            polls = await self.client.db.polls.get_polls(session, True)
            await self.client.db.subscribers.subscribe(session, account, polls[0], amount)

    @commands.guild_only()
    @commands.command(name='poll')
    async def poll(self, ctx: commands.Context, title: str, mins=0, hrs=0, days=1):
        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.create_poll(session, title, datetime.now() + timedelta(minutes=mins, hours=hrs, days=days))
            
                

async def setup(client: MarketBot):
    await client.add_cog(Market(client))