from abc import ABC, abstractmethod
from typing import Union
from uuid import uuid4
from scipy import stats
from market import MarketState

from model import Order, OrderSide


class Trader(ABC):
    id: str
    cash: Union[int, float]
    lots: Union[int, float]

    @abstractmethod
    def _offer_bid(self, *args, **kwargs) -> Order:
        pass

    @abstractmethod
    def _offer_ask(self, *args, **kwargs) -> Order:
        pass

    @abstractmethod
    def generate_orders(self, market_state: MarketState) -> list[Order]:
        pass


class MarketMaker(Trader):
    def __init__(self, markup_factor: float) -> None:
        self.markup = markup_factor
        self.size = 100
        self.id = str(uuid4())
        self.cash = 10e10
        self.lots = 10e10

    def _offer_bid(self, price: float) -> Order:
        bid = price * (1 - self.markup)
        return Order(price=bid, size=self.size, side=OrderSide.bid, sender_id=self.id)

    def _offer_ask(self, price: float) -> Order:
        ask = price * (1 + self.markup)
        return Order(price=ask, size=self.size, side=OrderSide.ask, sender_id=self.id)

    def generate_orders(self, market_state: MarketState) -> list[Order]:
        orders = []
        bid = self._offer_bid(price=market_state.true_price)
        orders.append(bid)
        ask = self._offer_ask(price=market_state.true_price)
        orders.append(ask)
        return orders


class DumbTrader(Trader):
    def __init__(self) -> None:
        self.size = 5
        self.vol = 25
        self.id = str(uuid4())
        self.cash = 50_000
        self.lots = 100

    def _offer_bid(self, price: float) -> Order:
        bid = float(stats.norm.rvs(loc=price, scale=self.vol))
        return Order(price=bid, size=self.size, side=OrderSide.bid, sender_id=self.id)

    def _offer_ask(self, price: float) -> Order:
        ask = float(stats.norm.rvs(loc=price, scale=self.vol))
        return Order(price=ask, size=self.size, side=OrderSide.ask, sender_id=self.id)

    def generate_orders(self, market_state: MarketState) -> list[Order]:
        random_side = OrderSide.bid if float(stats.norm.rvs()) > 0 else OrderSide.ask
        market_mid = (
            market_state.orderbook.get_best_bid().price
            + market_state.orderbook.get_best_ask().price
        ) / 2
        if random_side == OrderSide.bid:
            order = self._offer_bid(market_mid)
        elif random_side == OrderSide.ask:
            order = self._offer_ask(market_mid)
        else:
            raise KeyError(f"Invalid order side {random_side}")
        return [order]
