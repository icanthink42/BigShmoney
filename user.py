import pickle

import data


class Stock:
    def __init__(self, symbol: str, paid: float, amount: int):
        self.symbol: str = symbol
        self.paid: float = paid
        self.amount: int = amount

    def __add__(self, other):
        self.paid += other.paid
        self.amount += other.amount
        return self


class User:
    def __init__(self, discord_id: int, money: float):
        self.discord_id: int = discord_id
        self.money: float = money
        self.stocks: dict = {}

    def save(self):
        with open(data.config["users_save_dir"] + "/" + str(self.discord_id), "wb") as f:
            pickle.dump(self, f)

    def add_stock(self, stock: Stock):
        if stock.symbol not in self.stocks:
            self.stocks[stock.symbol] = stock
            return
        self.stocks[stock.symbol] += stock

    def remove_stock(self, symbol: str, amount: int):
        stock = self.stocks[symbol]
        stock.paid = stock.paid * (1 - abs(stock.amount - amount) / stock.amount)
        stock.amount -= amount
        self.stocks[symbol] = stock
        if stock.amount == 0:
            del self.stocks[symbol]
