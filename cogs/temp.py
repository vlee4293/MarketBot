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

    @app_commands.guild_only()
    @app_commands.command(name='balance')
    async def balance(self, interaction: discord.Interaction):
        async with self.client.db.async_session() as session:
            account = await self.client.db.accounts.get_or_create_account(session, interaction.user)
            embed = Embed(
                title=f'{interaction.user.display_name}\'s Balance', 
                description=f'${account.balance:.2f}'
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.guild_only()
    @poll_group.command(name='create')
    async def poll_create(self, interaction: discord.Interaction, title: str, duration: str, 
            option1: str, option2: str = None, option3: str = None, option4: str = None, option5: str = None, 
            option6: str = None, option7: str = None, option8: str = None, option9: str = None, option10: str = None): 
        
        """Create a poll (max 10 options)

        Parameters
        -----------
        title: str
            Title
        duration: str
            The lock in period duration. Ex. 1m = 1 minute, 1h = 1 hour, 1d = 1 day
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

        duration = duration.strip()
        try:
            amount = int(duration[:-1])
            if amount < 0:
                await interaction.response.send_message('This isn\'t Dr.Who. Fuck off, and give me a positive duration!', ephemeral=True, delete_after=60)
                return
        except:
            await interaction.response.send_message('Instructions aren\'t your strong suit. Give me a duration in the right format!', ephemeral=True, delete_after=60)
            return

        if duration.endswith('m'):
            duration = timedelta(minutes=amount)
        elif duration.endswith('h'):
            duration = timedelta(hours=amount)
        elif duration.endswith('d'):
            duration = timedelta(days=amount)
        else:
            await interaction.response.send_message('How many what... braincells? I need a unit for duration!', ephemeral=True, delete_after=60)
            return


        await interaction.response.defer()
        message = await interaction.original_response()
        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.create_poll(session, message, title, len(options), start, duration)
        embed = Embed(title=f'{title}')
        prefixed_options = [f':number_{index + 1}: {option}' for index, option in enumerate(options)]

        embed.add_field(name='Options', value='\n'.join(prefixed_options))
        embed.add_field(name='Place your stake with:', value=f'`/poll bet {poll.id} [option] [stake]`', inline=False)
        embed.set_footer(text='Lock in by: '+ datetime.strftime(start+duration, '%-m/%-d/%y %-I:%M %p'))
        await interaction.followup.send(embed=embed)

    @app_commands.guild_only()
    @poll_group.command(name='bet')
    async def poll_bet(self, interaction: discord.Interaction, poll_id: int, option: int, stake: float):
        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.get_poll(session, poll_id)
            if poll is None:
                await interaction.response.send_message('There is no poll to bet on stupid', ephemeral=True, delete_after=60)
            elif poll and option > 0 and option <= poll.num_options:
                account = await self.client.db.accounts.get_or_create_account(session, interaction.user)
                subscriber = await self.client.db.subscribers.subscribe(session, account, poll, option, stake)
                if subscriber:
                    await interaction.response.send_message(f'${stake:.2f} placed on "{poll.title}"', ephemeral=True, delete_after=60)
                else:
                    await interaction.response.send_message(f'You got no money to bet you broke ass bitch!', ephemeral=True, delete_after=60)
            else:
                await interaction.response.send_message(f'Are you blind? There are clearly only {poll.num_options} options loser.', ephemeral=True, delete_after=60)

    @app_commands.guild_only()
    @poll_group.command(name='close')
    async def poll_close(self, interaction: discord.Interaction, poll_id: int, winning_option: int):
        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.get_poll(session, poll_id)
            if poll is None:
                await interaction.response.send_message(f'Try y\'know... picking an existing poll?', ephemeral=True, delete_after=60)
                return
            if winning_option > poll.num_options or winning_option < 1:
                await interaction.response.send_message(f'Are you blind? There are clearly only {poll.num_options} options loser.', ephemeral=True, delete_after=60)
                return
            if poll.is_open:
                await interaction.response.send_message(f'The poll `{poll.title}` is still open.', ephemeral=True, delete_after=60)
                return
            if poll.is_finalized:
                await interaction.response.send_message(f'Can\'t close what is already closed.', ephemeral=True, delete_after=60)
                return
            await self.client.db.polls.set_winning_option(session, poll, winning_option)

        embed = Embed(
            title=f'The poll `{poll.title}` has finalized',
            description=poll.reference
        )

        embed.add_field(name='Winning Outcome', value=f':number_{poll.winning_option}:')


        await interaction.response.send_message(embed=embed)


    @app_commands.guild_only()
    @app_commands.command(name='reset')
    async def hardreset(self, interaction: discord.Interaction):
        await self.client.db.drop_tables()
        await self.client.db.create_tables()
        await interaction.response.send_message('Tables reset', ephemeral=True)

async def setup(client: MarketBot):
    await client.add_cog(Market(client), guild=discord.Object(id=os.getenv('DEBUG_GUILD')))
