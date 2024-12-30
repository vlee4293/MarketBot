import os
import discord
from discord import app_commands
from discord.ext import commands
from bot import MarketBot


class AdminCog(commands.Cog):
    def __init__(self, client: MarketBot):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        
        print(f'{__name__} is online!')
    
    @app_commands.guild_only()
    @app_commands.command(name='reset')
    async def hardreset(self, interaction: discord.Interaction):
        """Reset DB Data"""

        if interaction.user.id == 246534330657144832:
            await self.client.db.drop_tables()
            await self.client.db.create_tables()
            await interaction.response.send_message('Tables reset', ephemeral=True)
        else:
            await interaction.response.send_message('You must be the owner to use this command!', ephemeral=True)
    
    @app_commands.guild_only()
    @app_commands.command(name='sync')
    async def sync(self, interaction: discord.Interaction):
        """Sync Global Commands"""
        if interaction.user.id == 246534330657144832:
            print(self.client.tree.get_commands())
            await self.client.tree.sync()
            await interaction.response.send_message('Synced Successfully', ephemeral=True)
        else:
            await interaction.response.send_message('You must be the owner to use this command!', ephemeral=True)

async def setup(client: MarketBot):
    guild_id = os.getenv('DEBUG_GUILD')
    if guild_id:
        await client.add_cog(AdminCog(client), guild=discord.Object(id=guild_id))
    else:
        await client.add_cog(AdminCog(client))