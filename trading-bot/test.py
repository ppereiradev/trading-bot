import os
import calendar
import time

import pandas as pd

from binance.client import Client
from binance import ThreadedWebsocketManager


api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")
client = Client(api_key, secret_key)
client.API_URL = 'https://testnet.binance.vision/api'
btc_price = {'error':False}

def btc_trade_history(msg):
    if msg['e'] != 'error':
        print(msg['c'])
        btc_price['last'] = msg['c']
        btc_price['bid'] = msg['b']
        btc_price['last'] = msg['a']
        btc_price['volume'] = msg['v']
        btc_price['error'] = False
    else:
        btc_price['error'] = True


if __name__ == "__main__":

    current_timestamp_seconds = calendar.timegm(time.gmtime())
    timestamp_seconds = current_timestamp_seconds - (24 * 60 * 60)

    try:
        bars = client.get_historical_klines('BTCUSDT', '5m', timestamp_seconds, limit=1000)
    except Exception as e:
        print("Erro completo:", e)

    for line in bars:
        del line[6:]

    btc_df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    btc_df['date'] = pd.to_datetime(btc_df['timestamp'], unit='ms', utc=True)
    btc_df.set_index('date', inplace=True)

    print(btc_df)
