from util import Database
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import discord



class MarketBot(commands.Bot):
    def __init__(self, command_prefix: str, **kwargs):
        super().__init__(command_prefix=command_prefix, **kwargs)
        load_dotenv()

        self.db = Database(
            user=os.getenv('DB_USER'), 
            passwd=os.getenv('DB_PASSWD'), 
            db_name=os.getenv('DB_NAME'), 
            host=os.getenv('DB_HOST'), 
            port=os.getenv('DB_PORT')
        )

        self.is_synced = False
        
    
    

    async def on_ready(self):
        print(f'{self.user.name}')
        if not self.is_synced:
            cmds = await self.tree.sync(guild=discord.Object(id=os.getenv('DEBUG_GUILD')))
            print(cmds)
            self.is_synced = True

        
        
        


        
