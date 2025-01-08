import os
import time
import calendar

import pandas as pd

from binance.client import Client
from binance import ThreadedWebsocketManager

class TradingBot:
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.secret_key = os.getenv("BINANCE_SECRET_KEY")
        self.client = Client(self.api_key, self.secret_key)
        self.client.API_URL = 'https://testnet.binance.vision/api'
        self.bsm = ThreadedWebsocketManager()
        self.btc_df = None

    def get_balance(self, asset):
        return self.client.get_asset_balance(asset=asset)

    def get_latest_price(self, symbol):
        return self.client.get_symbol_ticker(symbol=symbol)

    def btc_trade_history(self, msg):
        btc_price = {}
        if msg['e'] != 'error':
            btc_price['timestamp'] = msg['E']
            btc_price['open'] = msg['o']
            btc_price['high'] = msg['h']
            btc_price['low'] = msg['l']
            btc_price['close'] = msg['c']
            btc_price['volume'] = msg['v']

            btc_price['date'] = pd.to_datetime(btc_price['timestamp'], unit='ms', utc=True)
            print(btc_price['timestamp'], btc_price['date'])
            # Criar um DataFrame com a nova linha
            new_row_df = pd.DataFrame([btc_price])
            new_row_df.set_index('date', inplace=True)

            # Adicionar ao DataFrame original
            self.btc_df = pd.concat([self.btc_df, new_row_df])
        else:
            print(msg['e'])

        time.sleep(10)

    def start_trade(self):
        self.bsm.start()
        self.bsm.start_symbol_ticker_socket(callback=self.btc_trade_history, symbol='BTCUSDT')

    def stop_trade(self):
        self.bsm.stop()

    def get_btc_price(self):
        return self.btc_price

    def fill_btc_df_earlier_tickers(self):
        current_timestamp_seconds = calendar.timegm(time.gmtime())
        timestamp_seconds = current_timestamp_seconds - (24 * 60 * 60)

        try:
            bars = self.client.get_historical_klines('BTCUSDT', '5m', timestamp_seconds, limit=1000)
        except Exception as e:
            print("Erro completo:", e)

        for line in bars:
            del line[6:]

        self.btc_df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.btc_df['date'] = pd.to_datetime(self.btc_df['timestamp'], unit='ms', utc=True)
        self.btc_df.set_index('date', inplace=True)

    def get_btc_df(self):
        return self.btc_df.tail(5)

if __name__ == "__main__":
    trading_bot = TradingBot()
    trading_bot.fill_btc_df_earlier_tickers()
    trading_bot.start_trade()

    try:
        while True:
            print(trading_bot.get_btc_df())
            time.sleep(3)  # Evita que o loop consuma CPU desnecessariamente
    except KeyboardInterrupt:
        trading_bot.stop_trade()
        print("\nGracefully shutting down...")

