from scipy import stats
import matplotlib.pyplot as plt

from products import Underlying
from traders import Trader, MarketMaker, DumbTrader
from market import MatchingEngine, OrderBook, clear_trades
from model import OrderSide


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

    plt.plot(range(1, t + 1), trader_portfolio)  # type: ignore
    plt.show()


if __name__ == "__main__":
    main()
