from util import Database
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import discord
import datetime
import asyncio



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
        
    
    async def setup_hook(self):
        self.bg_task = self.loop.create_task(self.poll_status_checker())

    async def poll_status_checker(self):
        await self.wait_until_ready()
        channel = self.get_channel(1316881823435063359)
        while not self.is_closed():
            async with self.db.async_session() as session:
                polls = await self.db.polls.get_polls(session, True)
                for poll in polls:
                    if poll.end.astimezone() <= datetime.datetime.now().astimezone():
                        await self.db.polls.set_state(session, poll.id, False)
                        _, channel_id, _ = list(map(int, poll.reference[29:].split('/')))
                        channel = self.get_channel(channel_id)
                        await channel.send(embed=discord.Embed(title=f'Betting for `{poll.title}` has locked', description=poll.reference))
            await asyncio.sleep(60)

    async def on_ready(self):
        print(f'{self.user.name}')
        if not self.is_synced:
            cmds = await self.tree.sync(guild=discord.Object(id=os.getenv('DEBUG_GUILD')))
            print(cmds)
            self.is_synced = True

        
        


        
