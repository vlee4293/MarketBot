from .db import Database as BaseDB
from .managers import AccountManager, StockManager, InvestmentManager


__all__ = [
    'Database'
]



class Database(BaseDB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.accounts = AccountManager(self)
        self.stocks = StockManager(self)
        self.investments = InvestmentManager(self, self.accounts, self.stocks)