import os
from time import sleep
from utils.trading_bot import TradingBot
from utils.btcplotter import BTCPlotter


if __name__ == "__main__":
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")
    api_url = 'https://testnet.binance.vision/api'

    trading_bot = TradingBot(api_key, secret_key, api_url)
    plotter = BTCPlotter()

    while True:
        trading_bot.execute_trading()
        print(trading_bot.get_last_row(), "\n\n")
        plotter.plot(trading_bot.get_btc_to_plot())
        sleep(150)
