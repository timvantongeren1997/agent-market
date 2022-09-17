from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Union
from uuid import uuid4
from scipy import stats
import matplotlib.pyplot as plt
from operator import attrgetter


class Underlying:
    def __init__(self, base_price: float) -> None:
        self.price = base_price

        # Random walk parameters
        self.mu = 0
        self.sigma = 0.25

    def simulate_one_step(self):
        self.price += float(stats.norm.rvs(loc=self.mu, scale=self.sigma, size=1))


class OrderSide(Enum):
    bid = auto()
    ask = auto()


@dataclass
class Order:
    price: float
    size: float
    side: OrderSide
    sender_id: str
    id: str = field(init=False)

    def __post_init__(self):
        self.id = str(uuid4())

    def __str__(self) -> str:
        return f"{self.price:.3f} ({self.size} lots)"


@dataclass
class Trade:
    buyer_id: str
    seller_id: str
    size: float
    price: float


@dataclass
class OrderBook:
    bids: list[Order]
    asks: list[Order]

    def __str__(self) -> str:
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        return f"Best bid is {best_bid} and best ask is {best_ask}"

    def add_order_to_book(self, order: Order):
        if order.side == OrderSide.ask:
            self.asks.append(order)
        elif order.side == OrderSide.bid:
            self.bids.append(order)
        else:
            raise KeyError(f"Invalid order side {order.side}")

    def get_best_bid(self) -> Order:
        return max(self.bids, key=attrgetter("price"))

    def get_best_ask(self) -> Order:
        return min(self.asks, key=attrgetter("price"))

    def cancel_order(self, order: Order):
        if order.side == OrderSide.bid:
            self.bids = [bid for bid in self.bids if not bid.id == order.id]
        elif order.side == OrderSide.ask:
            self.asks = [ask for ask in self.asks if not ask.id == order.id]
        else:
            raise KeyError(f"Invalid order side {order.side}")

    def amend_order(self, order: Order):
        if order.side == OrderSide.bid:
            self.bids = [bid for bid in self.bids if not bid.id == order.id]
            self.bids.append(order)
        elif order.side == OrderSide.ask:
            self.asks = [ask for ask in self.asks if not ask.id == order.id]
            self.asks.append(order)
        else:
            raise KeyError(f"Invalid order side {order.side}")


class MatchingEngine:
    def __init__(self) -> None:
        pass

    def _cross_orders(self, bid: Order, ask: Order) -> Trade:
        mid_price = (bid.price + ask.price) / 2
        size = min(bid.size, ask.size)
        return Trade(
            buyer_id=bid.sender_id,
            seller_id=ask.sender_id,
            size=size,
            price=mid_price,
        )

    def match_orders(self, book: OrderBook) -> list[Trade]:
        # We order them from worst to best, such that we can use pop to get
        # the last and thus best bid and ask from the arrays.
        sorted_bids = sorted(book.bids, key=lambda order: order.price, reverse=False)
        sorted_asks = sorted(book.asks, key=lambda order: order.price, reverse=True)

        best_bid = sorted_bids.pop()
        best_ask = sorted_asks.pop()
        trades: list[Trade] = []
        while True:
            if not best_bid.price >= best_ask.price:
                break  # No (more) trades possible
            trade = self._cross_orders(bid=best_bid, ask=best_ask)
            trades.append(trade)
            if best_bid.size > best_ask.size:
                book.cancel_order(best_ask)
                if len(sorted_asks) == 0:
                    break
                best_ask = sorted_asks.pop()
                best_bid.size -= trade.size
            elif best_bid.size < best_ask.size:
                book.cancel_order(best_bid)
                if len(sorted_bids) == 0:
                    break
                best_bid = sorted_bids.pop()
                best_ask.size -= trade.size
            elif best_bid.size == best_ask.size:
                book.cancel_order(best_bid)
                book.cancel_order(best_ask)
                if len(sorted_bids) == 0:
                    break
                if len(sorted_asks) == 0:
                    break
                best_bid = sorted_bids.pop()
                best_ask = sorted_asks.pop()

        # Best bid and ask get amended as the size might've changed
        book.add_order_to_book(best_bid)
        book.add_order_to_book(best_ask)

        return trades


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


def clear_trades(players: dict[str, Trader], trades: list[Trade]):
    for trade in trades:
        players[trade.buyer_id].cash -= trade.price
        players[trade.buyer_id].lots += trade.size
        players[trade.seller_id].cash += trade.price
        players[trade.seller_id].lots -= trade.size


def main():
    N = int(1e5)
    stock = Underlying(base_price=100)
    market_maker = MarketMaker(markup_factor=0.01)
    trader = DumbTrader()
    order_book = OrderBook(bids=[], asks=[])
    matching_engine = MatchingEngine()
    players: dict[str, Trader] = {
        trader.id: trader,
        market_maker.id: market_maker,
    }
    trader_portfolio = []
    for t in range(1, N + 1):
        # Setup
        stock.simulate_one_step()

        # Market making
        mm_bid = market_maker.offer_bid(stock.price)
        mm_ask = market_maker.offer_ask(stock.price)
        order_book.add_order_to_book(order=mm_bid)
        order_book.add_order_to_book(order=mm_ask)

        # Trader entering orders
        random_side = OrderSide.bid if float(stats.norm.rvs()) > 0 else OrderSide.ask
        if random_side == OrderSide.bid:
            trader_order = trader.offer_bid(stock.price)
        elif random_side == OrderSide.ask:
            trader_order = trader.offer_ask(stock.price)
        else:
            raise KeyError(f"Invalid order side {random_side}")
        order_book.add_order_to_book(trader_order)

        # Trading
        trades = matching_engine.match_orders(book=order_book)

        # Clearing
        clear_trades(players=players, trades=trades)
        trader_portfolio.append(trader.cash + trader.lots * stock.price)
        if trader_portfolio[-1] < 0:
            print(f"Trader went bankrupt at time {t}")
            break

        # Market makers cleaning up
        order_book.cancel_order(mm_bid)
        order_book.cancel_order(mm_ask)

        # Dumb trader also cleaning up
        order_book.cancel_order(trader_order)

    plt.plot(range(1, t + 1), trader_portfolio)
    plt.show()


if __name__ == "__main__":
    main()
