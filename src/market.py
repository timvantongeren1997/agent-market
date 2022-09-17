from dataclasses import dataclass
from operator import attrgetter

from model import Order, OrderSide, Trade


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

    def clear_book(self):
        self.bids = []
        self.asks = []


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


@dataclass
class MarketState:
    orderbook: OrderBook
    true_price: float
