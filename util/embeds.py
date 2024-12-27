
from datetime import datetime
from typing import List
import discord
from util.models import Poll, PollOption

class poll_embed_maker:
    @classmethod
    def new_poll(cls, poll: Poll, options: List[PollOption]) -> discord.Embed:
        embed = discord.Embed(title=f'[OPEN] {poll.question}')
        prefixed_options = [f':number_{option.index}: {option.value}' for option in sorted(options, key=lambda option: option.index)]
        embed.add_field(name='Options', value='\n'.join(prefixed_options))
        embed.add_field(name='Place your stake with:', value=f'`/poll bet {poll.id} [option_number] [stake]`', inline=False)
        embed.set_footer(text='Lock in by: '+ datetime.strftime(poll.lockin_by.astimezone(), '%-m/%-d/%y %-I:%M %p'))
        return embed
    
    @classmethod
    def close_poll(cls, poll: Poll, winning_option: PollOption) -> discord.Embed:
        embed = discord.Embed(title=f'The poll `{poll.question}` has finalized', description=poll.reference)
        embed.add_field(name='Winning Outcome', value=f':number_{winning_option.index}: {winning_option.value}')
        return embed