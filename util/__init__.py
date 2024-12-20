from .db import Database as BaseDB
from .managers import AccountManager, PollManager, PollSubscriberManager


__all__ = [
    'Database'
]



class Database(BaseDB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.accounts = AccountManager()
        self.polls = PollManager()
        self.subscribers = PollSubscriberManager()