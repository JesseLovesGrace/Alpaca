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
        self.spy_held = False  # Flag to track if SPY is currently held

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
            pos = self.get_position(symbol)

            # Check if there are 6 consecutive down days or in the initial iteration
            if all(asset_data['close'].iloc[-i] < asset_data['close'].iloc[-(i + 1)] for i in range(1, 6)) or self.iteration_count == 0:
                if symbol != "SPY":
                    if self.spy_held:
                        # Sell all 700 shares of SPY if held
                        self.sell_all("SPY")
                        self.spy_held = False

                    quantity = 3000

                    if pos is None:
                        # Buy 4000 shares and set the initial average price
                        order = self.create_order(symbol, quantity, "buy")
                        self.submit_order(order)
                        self._positions[symbol] = {'quantity': quantity, 'avg_price': asset_data['close'].iloc[-1]}
                    else:
                        # If already in position, buy more and update the average price
                        new_quantity = 2000
                        # Update the code to use correct attribute names
                        new_avg_price = (pos['quantity'] * pos['avg_price'] + new_quantity * asset_data['close'].iloc[
                            -1]) / (pos['quantity'] + new_quantity) if hasattr(pos, 'quantity') and hasattr(
                            pos, 'avg_price') else 0.0

                        # pos.buy(new_quantity, new_avg_price)  # Remove this line
                        order = self.create_order(symbol, new_quantity, "buy")  # Create a new order
                        self.submit_order(order)  # Submit the order


                # Sell when reaching 5% profit of the average price, excluding SPY
                elif pos is not None and pos['quantity'] > 0 and asset_data['close'].iloc[-1] >= pos['avg_price'] * 1.05 and symbol != "SPY":
                    pos.sell(pos['quantity'])

        # Buy 700 shares of SPY after liquidating other positions, if not already held
        if not self.spy_held:
            initial_spy_quantity = 700
            initial_spy_avg_price = self.get_historical_prices("SPY", 1, "day").df['close'].iloc[0]
            self._positions["SPY"] = {'quantity': initial_spy_quantity, 'avg_price': initial_spy_avg_price}
            self.spy_held = True

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
