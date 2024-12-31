import asyncio
import discord
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from discord.ext import commands
from util import Database
from util.models import PollStatus
from util.embeds import poll_embed_maker


class MarketBot(commands.Bot):
    def __init__(self, command_prefix: str, **kwargs):
        super().__init__(command_prefix=command_prefix, **kwargs)
        load_dotenv(override=True)

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
                        await channel.send(embed=discord.Embed(title=f'Betting for `{poll.question:.45}` has locked', description=f'<@{poll.account.account_number}>', url=poll.reference))
                        msg = await channel.fetch_message(message_id)
                        original = msg.embeds[0]
                        stakes = await self.db.bets.get_stake_totals(session, poll=poll)
                        embed = poll_embed_maker.update_open_poll(original, poll, stakes)
                        embed = poll_embed_maker.lock_open_poll(original, poll)
                        await msg.edit(embed=embed)

            await asyncio.sleep(60)

    async def on_ready(self):
        print(f'{self.user.name}')
        print([command.qualified_name for command in self.tree.get_commands()])
        if not self.is_synced:
            self.is_synced = True

        
        


        
