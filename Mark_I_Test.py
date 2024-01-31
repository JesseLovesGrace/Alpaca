from config import ALPACA_CONFIG
from datetime import datetime, timedelta
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies import Strategy
from lumibot.traders import Trader
import numpy as np
import pandas as pd


class MultiAssetStrategy(Strategy):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._positions = None

    def initialize(self):
        self.assets = ["AAPL", "TSLA", "AMD", "GS", "HD", "IBM", "JNJ", "JPM"]  # Add more symbols as needed
        self._positions = {symbol: {'quantity': 0, 'avg_price': 0.0} for symbol in self.assets}
        self.sleeptime = "1D"
        self.iteration_count = 0

    @property
    def positions(self):
        return self._positions

    @positions.setter
    def positions(self, value):
        raise AttributeError(" 'positions' property is read-only")

    def on_trading_iteration(self):
        for symbol in self.assets:
            bars = self.get_historical_prices(symbol, 6, "day")
            asset_data = bars.df
            asset_data['Target'] = asset_data['close'] * 1.05  # Set target as 5% profit

            # Buy when asset price has been going down for 6 days
            if all(asset_data['close'].iloc[-i] < asset_data['close'].iloc[-(i + 1)] for i in range(1, 6)):
                quantity = 4000
                pos = self.get_position(symbol)

                if pos is None:
                    order = self.create_order(symbol, quantity, "buy")
                    self.submit_order(order)
                    self._positions[symbol] = {'quantity': quantity, 'avg_price': asset_data['close'].iloc[-1]}
                else:
                    # If already in position, buy more and update the average price
                    new_quantity = 1000
                    new_avg_price = (self._positions[symbol]['quantity'] * self._positions[symbol]['avg_price'] + new_quantity * asset_data['close'].iloc[-1]) / (self._positions[symbol]['quantity'] + new_quantity)
                    self._positions[symbol]['quantity'] += new_quantity
                    self._positions[symbol]['avg_price'] = new_avg_price

            # Sell when reaching 5% profit of the average price
            elif self._positions[symbol]['quantity'] > 0 and asset_data['close'].iloc[-1] >= self._positions[symbol]['avg_price'] * 1.05:
                self.sell_all(symbol)

        self.iteration_count += 1


if __name__ == "__main__":
    trade = False
    if trade:
        broker = Alpaca(ALPACA_CONFIG)
        strategy = MultiAssetStrategy(broker=broker)
        bot = Trader()
        bot.add_strategy(strategy)
        bot.run_all()
    else:
        start = datetime(2012, 1, 1)
        end = datetime(2023, 12, 31)
        MultiAssetStrategy.backtest(
            YahooDataBacktesting,
            start,
            end
        )
