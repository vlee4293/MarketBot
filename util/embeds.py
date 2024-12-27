
from datetime import datetime
from typing import List
import discord
from util.models import Poll, PollOption

def percentBar(stake):
    segments = round(stake * 10)
    return '`|`' + ':green_square:' * (segments) + ':red_square:' * (10-segments) + '`|`'

class poll_embed_maker:
    @classmethod
    def new_poll(cls, poll: Poll, options: List[PollOption]) -> discord.Embed:
        embed = discord.Embed(title=f'[OPEN] {poll.question}')
        prefixed_options = [f':number_{option.index}: `{option.value}`' for option in sorted(options, key=lambda option: option.index)]
        embed.add_field(name='Options', value='\n'.join(prefixed_options))
        embed.add_field(name='Place your stake with:', value=f'`/poll bet {poll.id} [option_number] [stake]`', inline=False)
        embed.set_footer(text='Lock in by: '+ datetime.strftime(poll.lockin_by.astimezone(), '%-m/%-d/%y %-I:%M %p'))
        return embed
    
    @classmethod
    def locked_poll(cls, original: discord.Embed, poll: Poll, stakes: List[float]) -> discord.Embed:
        total_stake = sum(stakes)
        normal_stakes = [stake / total_stake for stake in stakes]
        votes = [len(option.bets) for option in poll.options]
        original.title = '[LOCKED] ' + original.title[7:]
        original.remove_field(1)
        original.add_field(name='Stake Share (%)', value='\n'.join(list(map(percentBar, normal_stakes))))
        original.add_field(name='Close the poll with:', value=f'`/poll close {poll.id} [winning_number]`', inline=False)
        footer = [
            f'Total stake: ${total_stake:.2f}',
            f'Total votes: {sum(votes)}',
        ]
        original.set_footer(text='\n'.join(footer))
        return original

    @classmethod
    def closed_poll(cls, poll: Poll, winning_option: PollOption) -> discord.Embed:
        embed = discord.Embed(title=f'The poll `{poll.question}` has finalized', description=poll.reference)
        embed.add_field(name='Winning Outcome', value=f':number_{winning_option.index}: `{winning_option.value}`')
        return embed
    
    @classmethod
    def edit_closed_poll(cls, original: discord.Embed) -> discord.Embed:
        original.title = '[CLOSED] ' + original.title[9:]
        original.remove_field(2)
        return original
    




    
