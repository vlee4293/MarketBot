from util import Database
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import discord
from datetime import datetime, timezone
import asyncio
from util.models import PollStatus



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
        while not self.is_closed():
            async with self.db.async_session() as session:
                polls = await self.db.polls.get_all(session, status=PollStatus.OPEN)
                for poll in polls:
                    if poll.lockin_by <= datetime.now(timezone.utc):
                        await self.db.polls.update(session, poll, status=PollStatus.LOCKED)
                        _, channel_id, message_id = list(map(int, poll.reference[29:].split('/')))
                        channel = self.get_channel(channel_id)
                        await channel.send(embed=discord.Embed(title=f'Betting for `{poll.question}` has locked', description=poll.reference))
                        msg = await channel.fetch_message(message_id)
                        new_embed = msg.embeds[0]
                        new_embed.title = '[LOCKED] ' + new_embed.title[7:] 
                        new_embed.set_footer(text=f'Total Stake: {await self.db.bets.get_total_stake(session, poll=poll):.2f}')
                        await msg.edit(embed=new_embed)

            await asyncio.sleep(60)

    async def on_ready(self):
        print(f'{self.user.name}')
        if not self.is_synced:
            cmds = await self.tree.sync(guild=discord.Object(id=os.getenv('DEBUG_GUILD')))
            print(cmds)
            self.is_synced = True

        
        


        
