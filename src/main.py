import matplotlib.pyplot as plt
from tqdm import tqdm

from products import Stock
from traders import Trader, MarketMaker, DumbTrader
from market import MarketState, MatchingEngine, OrderBook
from model import Trade


def clear_trades(players: dict[str, Trader], trades: list[Trade]):
    for trade in trades:
        players[trade.buyer_id].cash -= trade.price
        players[trade.buyer_id].lots += trade.size
        players[trade.seller_id].cash += trade.price
        players[trade.seller_id].lots -= trade.size


def main():
    N = int(1e5)
    stock = Stock(base_price=100)
    order_book = OrderBook(bids=[], asks=[])
    matching_engine = MatchingEngine()
    players: list[Trader] = [
        MarketMaker(markup_factor=0.01),
    ]
    trader = DumbTrader()
    players.append(trader)
    player_id_mapping: dict[str, Trader] = {player.id: player for player in players}
    trader_portfolio = []
    for t in tqdm(range(1, N + 1)):
        # Setup
        stock.simulate_one_step()

        # Generating orders for each player
        market_state = MarketState(
            orderbook=order_book,
            true_price=stock.price,
        )
        for player in players:
            orders = player.generate_orders(market_state=market_state)
            for order in orders:
                order_book.add_order_to_book(order=order)

        # Trading
        trades = matching_engine.match_orders(book=order_book)

        # Clearing
        clear_trades(players=player_id_mapping, trades=trades)

        # Calculating the size of our trader's portfolio
        trader_portfolio.append(trader.cash + trader.lots * stock.price)
        if trader_portfolio[-1] < 0:
            print(f"Trader went bankrupt at time {t}")
            break

        # Whole order book is cleared each iteration
        order_book.clear_book()

    plt.plot(range(1, t + 1), trader_portfolio)  # type: ignore
    plt.show()


if __name__ == "__main__":
    main()
