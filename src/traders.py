from abc import ABC, abstractmethod
from typing import Union
from uuid import uuid4
from scipy import stats

from model import Order, OrderSide


class Trader(ABC):
    id: str
    cash: Union[int, float]
    lots: Union[int, float]

    @abstractmethod
    def offer_bid(self, *args, **kwargs) -> Order:  # type: ignore
        pass

    @abstractmethod
    def offer_ask(self, *args, **kwargs) -> Order:  # type: ignore
        pass


class MarketMaker(Trader):
    def __init__(self, markup_factor: float) -> None:
        self.markup = markup_factor
        self.size = 100
        self.id = str(uuid4())
        self.cash = 10e10
        self.lots = 10e10

    def offer_bid(self, price: float) -> Order:
        bid = price * (1 - self.markup)
        return Order(price=bid, size=self.size, side=OrderSide.bid, sender_id=self.id)

    def offer_ask(self, price: float) -> Order:
        ask = price * (1 + self.markup)
        return Order(price=ask, size=self.size, side=OrderSide.ask, sender_id=self.id)


class DumbTrader(Trader):
    def __init__(self) -> None:
        self.size = 5
        self.vol = 25
        self.id = str(uuid4())
        self.cash = 50_000
        self.lots = 100

    def offer_bid(self, price: float) -> Order:
        bid = float(stats.norm.rvs(loc=price, scale=self.vol))
        return Order(price=bid, size=self.size, side=OrderSide.bid, sender_id=self.id)

    def offer_ask(self, price: float) -> Order:
        ask = float(stats.norm.rvs(loc=price, scale=self.vol))
        return Order(price=ask, size=self.size, side=OrderSide.ask, sender_id=self.id)
