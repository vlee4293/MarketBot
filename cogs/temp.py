import discord
from discord.ext import commands
from discord.embeds import Embed
from bot import MarketBot
from datetime import datetime, timedelta
from discord import app_commands
from typing import Literal
import os


class Market(commands.Cog):
    poll_group = app_commands.Group(name='poll', description='...')


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


    @poll_group.command(name='create')
    async def poll(self, interaction: discord.Interaction, title: str, duration_unit: Literal['minutes', 'hours', 'days'], amount: app_commands.Range[int, 0, None], 
            option1: str, option2: str = None, option3: str = None, option4: str = None, option5: str = None, 
            option6: str = None, option7: str = None, option8: str = None, option9: str = None, option10: str = None): 
        
        """Create a poll (max 10 options)

        Parameters
        -----------
        title: str
            Title
        duration_unit: Literal['minutes', 'hours', 'days']
            Unit used to calculate lock in period
        amount: app_commands.Range[int, 0, None]
            Amount used to calculate lock in period
        option1: str
            Option 1
        option2: str
            Option 2
        option3: str
            Option 3
        option4: str
            Option 4
        option5: str
            Option 5
        option6: str
            Option 6
        option7: str
            Option 7
        option8: str
            Option 8
        option9: str
            Option 9
        option10: str
            Option 10
        """

        options = list(filter(lambda x: x is not None, [option1, option2, option3, option4, option5, option6, option7, option8, option9, option10]))
        start = datetime.now()
        duration = timedelta(**{duration_unit: amount})

        await interaction.response.defer()
        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.create_poll(session, title, start, duration)
        embed = Embed(title=f'{title}')

        prefixed_options = [f':number_{index + 1}: {option}' for index, option in enumerate(options)]

        embed.add_field(name='Options', value='\n'.join(prefixed_options))
        embed.add_field(name='Place your stake with:', value=f'`/poll bet {poll.id} [option] [stake]`', inline=False)
        embed.set_footer(text='Lock in by: '+ datetime.strftime(start+duration, '%-m/%-d/%y %-I:%-M %p'))
        await interaction.followup.send(embed=embed)

    @poll_group.command(name='bet')
    async def bet(self, interaction: discord.Interaction, poll_id: int, option: int, stake: float):
        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.get_poll(session, poll_id)
            if poll:
                account = await self.client.db.accounts.get_or_create_account(session, interaction.user)
                subscriber = await self.client.db.subscribers.subscribe(session, account, poll, option, stake)
                if subscriber:
                    await interaction.response.send_message(f'${stake:.2f} placed on "{poll.title}"', ephemeral=True)
                else:
                    await interaction.response.send_message(f'You got no money to bet you broke ass bitch!', ephemeral=True)
            else:
                await interaction.response.send_message('There is no poll to bet stupid', ephemeral=True)

    @app_commands.guild_only()
    @app_commands.command(name='reset')
    async def hardreset(self, interaction: discord.Interaction):
        await self.client.db.drop_tables()
        await self.client.db.create_tables()
        await interaction.response.send_message('Tables reset', ephemeral=True)

async def setup(client: MarketBot):
    await client.add_cog(Market(client), guild=discord.Object(id=os.getenv('DEBUG_GUILD')))
