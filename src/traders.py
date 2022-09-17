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

    def get_portfolio_value(self, true_price) -> float:
        return self.cash + self.lots * true_price

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
    def __init__(
        self,
        initial_cash: float,
        initial_lots: float,
        trade_size: int = 5,
        volatility: float = 25,
    ) -> None:
        self.size = trade_size
        self.vol = volatility
        self.id = str(uuid4())
        self.cash = initial_cash
        self.lots = initial_lots

    def _offer_bid(self, price: float) -> Order:
        bid = float(stats.norm.rvs(loc=price, scale=self.vol))
        return Order(price=bid, size=self.size, side=OrderSide.bid, sender_id=self.id)

    def _offer_ask(self, price: float) -> Order:
        ask = float(stats.norm.rvs(loc=price, scale=self.vol))
        return Order(price=ask, size=self.size, side=OrderSide.ask, sender_id=self.id)

    def generate_orders(self, market_state: MarketState) -> list[Order]:
        random_side = OrderSide.bid if float(stats.norm.rvs()) > 0 else OrderSide.ask
        best_bid = market_state.orderbook.get_best_bid()
        best_ask = market_state.orderbook.get_best_ask()
        if best_bid and best_ask:
            market_mid = (best_bid.price + best_ask.price) / 2
        elif best_bid:
            market_mid = best_bid.price
        elif best_ask:
            market_mid = best_ask.price
        else:
            # if there is no info we don't trade
            return []
        if random_side == OrderSide.bid:
            order = self._offer_bid(market_mid)
        elif random_side == OrderSide.ask:
            order = self._offer_ask(market_mid)
        else:
            raise KeyError(f"Invalid order side {random_side}")
        return [order]
