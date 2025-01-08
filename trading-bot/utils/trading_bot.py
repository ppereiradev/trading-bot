from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from binance.client import Client

class TradingBot:
    def __init__(self, api_key, secret_key, api_url):
        self.client = Client(api_key, secret_key)
        self.client.API_URL = api_url

    def get_balance(self, asset):
        return self.client.get_asset_balance(asset=asset)

    def get_latest_price(self, symbol):
        return self.client.get_symbol_ticker(symbol=symbol)

    def update_btc_df(self):
        try:
            bars = self.client.get_historical_klines('BTCUSDT', '1m', str(datetime.now() - timedelta(days=1)), limit=1000)
        except Exception as e:
            print("Erro completo:", e)

        for line in bars:
            del line[6:]

        self.btc_df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.btc_df['date'] = pd.to_datetime(self.btc_df['timestamp'], unit='ms', utc=True)
        self.btc_df.set_index('date', inplace=True)

    def get_btc_df(self):
        return self.btc_df

    def get_btc_to_plot(self):
        btc_df_copy = self.btc_df.copy(deep=True)

        btc_df_copy['sma_short'] = pd.to_numeric(btc_df_copy['sma_short'], errors='coerce')
        btc_df_copy['sma_long'] = pd.to_numeric(btc_df_copy['sma_long'], errors='coerce')
        btc_df_copy['close'] = pd.to_numeric(btc_df_copy['close'], errors='coerce')

        btc_df_copy = btc_df_copy.dropna(subset=['sma_short', 'sma_long', 'close'])

        return btc_df_copy

    def get_sma(self):
        self.update_btc_df()

        short_window = 10
        long_window = 30

        self.btc_df['sma_short'] = self.btc_df['close'].rolling(window=short_window).mean()
        self.btc_df['sma_long'] = self.btc_df['close'].rolling(window=long_window).mean()

        # Inicializa a coluna 'signal' com 0
        self.btc_df['signal'] = 0

        # Usando iloc para evitar problemas com o índice DatetimeIndex
        self.btc_df.iloc[short_window:, self.btc_df.columns.get_loc('signal')] = np.where(
            self.btc_df.iloc[short_window:]['sma_short'] > self.btc_df.iloc[short_window:]['sma_long'], 1, 0)

        # Calcula a diferença entre os sinais para identificar as mudanças
        self.btc_df['position'] = self.btc_df['signal'].diff()

    def place_buy_order(self, quantity, symbol):
        try:
            order = self.client.order_market_buy(
                symbol=symbol,
                quantity=quantity)
            print('Bought BTC')
            return order
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def place_sell_order(self, quantity, symbol):
        try:
            order = self.client.order_market_sell(
                symbol=symbol,
                quantity=quantity)
            print('Sold BTC')
            return order
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def get_last_row(self):
        return self.btc_df.iloc[-1]

    def execute_trading(self):
        self.get_sma()

        balance = self.client.get_asset_balance(asset='USDT')
        usdt_balance = float(balance['free'])
        btc_price = float(self.client.get_symbol_ticker(symbol='BTCUSDT')['price'])
        quantity = (usdt_balance / btc_price) * 0.02
        quantity = round(quantity, 6)

        if self.btc_df['position'].iloc[-1] == 1:
            self.place_buy_order(quantity, 'BTCUSDT')
        elif self.btc_df['position'].iloc[-1] == -1:
            self.place_sell_order(quantity, 'BTCUSDT')
        else:
            print('No trade signal at this time.')


