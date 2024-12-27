import os

import discord
from discord import app_commands
from discord.ext import commands

from bot import MarketBot
from util.transformers import Duration


class ExperimentCog(commands.Cog):
    def __init__(self, client: MarketBot):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{__name__} is online!')

    @app_commands.command(name='parse')
    async def parse_duration(self, interaction: discord.Interaction, duration: Duration):
        await interaction.response.send_message(duration.value)
    
    @app_commands.command(name='total_stake')
    async def get_stake(self, interaction: discord.Interaction, poll_id: int):
        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.get(session, poll_id)
            if poll:
                result = await self.client.db.bets.get_total_stake(session, poll=poll, winners=False)
        await interaction.response.send_message(result)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.response.send_message(error, delete_after=30, ephemeral=True)

async def setup(client: MarketBot):
    await client.add_cog(ExperimentCog(client), guild=discord.Object(id=os.getenv('DEBUG_GUILD')))