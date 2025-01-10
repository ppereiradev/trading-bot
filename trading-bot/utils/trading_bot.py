from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from binance.client import Client
from binance.helpers import round_step_size

class TradingBot:
    def __init__(self, api_key, secret_key, api_url, asset, symbol):
        self.client = Client(api_key, secret_key)

        if api_url:
            self.client.API_URL = api_url

        self.position_to_sell = False
        self.asset = asset
        self.symbol = symbol
        self.total_profit = 0
        self.order_buy = []
        self.order_sell = []

    def get_balance(self, asset):
        return self.client.get_asset_balance(asset=asset)

    def get_latest_price(self, symbol):
        return self.client.get_symbol_ticker(symbol=symbol)

    def update_symbol_df(self):
        try:
            bars = self.client.get_historical_klines(self.symbol, '1m', str(datetime.now() - timedelta(days=1)), limit=1000)
        except Exception as e:
            print("Erro completo:", e)

        for line in bars:
            del line[6:]

        self.symbol_df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.symbol_df['date'] = pd.to_datetime(self.symbol_df['timestamp'], unit='ms', utc=True)
        self.symbol_df.set_index('date', inplace=True)

    def get_symbol_df(self):
        return self.symbol_df

    def get_symbol_to_plot(self):
        symbol_df_copy = self.symbol_df.copy(deep=True)

        symbol_df_copy['sma_short'] = pd.to_numeric(symbol_df_copy['sma_short'], errors='coerce')
        symbol_df_copy['sma_long'] = pd.to_numeric(symbol_df_copy['sma_long'], errors='coerce')
        symbol_df_copy['close'] = pd.to_numeric(symbol_df_copy['close'], errors='coerce')

        symbol_df_copy = symbol_df_copy.dropna(subset=['sma_short', 'sma_long', 'close'])

        return symbol_df_copy

    def get_sma(self):
        self.update_symbol_df()

        short_window = 10
        long_window = 30

        self.symbol_df['sma_short'] = self.symbol_df['close'].rolling(window=short_window).mean()
        self.symbol_df['sma_long'] = self.symbol_df['close'].rolling(window=long_window).mean()

        # Inicializa a coluna 'signal' com 0
        self.symbol_df['signal'] = 0

        # Usando iloc para evitar problemas com o índice DatetimeIndex
        self.symbol_df.iloc[short_window:, self.symbol_df.columns.get_loc('signal')] = np.where(
            self.symbol_df.iloc[short_window:]['sma_short'] > self.symbol_df.iloc[short_window:]['sma_long'], 1, 0)

        # Calcula a diferença entre os sinais para identificar as mudanças
        self.symbol_df['position'] = self.symbol_df['signal'].diff()

    def place_buy_order(self, quantity, symbol):
        try:
            order = self.client.order_market_buy(
                symbol=symbol,
                quantity=quantity)
            print(f"Bought {self.symbol}")
            return order
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def place_sell_order(self, quantity, symbol):
        try:
            order = self.client.order_market_sell(
                symbol=symbol,
                quantity=quantity)
            print(f"Sold {self.symbol}")
            return order
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def get_last_row(self):
        return self.symbol_df.iloc[-1]

    def calculate_profit_or_loss(self, order_buy, order_sell):

        # Informações do saldo atual
        balance = float(self.client.get_asset_balance(asset='USDT')['free'])

        # Comprar - Informações da ordem de compra
        buy_fills = order_buy['fills']
        buy_qty = sum(float(fill['qty']) for fill in buy_fills)  # Soma todas as quantidades compradas
        buy_costs = sum(float(fill['qty']) * float(fill['price']) for fill in buy_fills)  # Soma os custos totais de cada operação
        buy_commission = sum(float(fill['commission']) for fill in buy_fills)  # Soma todas as comissões em BTC ou outro ativo

        # Vender - Informações da ordem de venda
        sell_fills = order_sell['fills']
        sell_qty = sum(float(fill['qty']) for fill in sell_fills)  # Soma todas as quantidades vendidas
        sell_revenue = sum(float(fill['qty']) * float(fill['price']) for fill in sell_fills)  # Soma os ganhos totais de cada operação
        sell_commission = sum(float(fill['commission']) for fill in sell_fills)  # Soma todas as comissões em USDT ou outro ativo

        # Lucro bruto (sem taxas)
        profit = sell_revenue - buy_costs

        # Subtração das comissões
        # Compra: A comissão é em BTC (precisamos converter para USDT)
        buy_commission_usdt = buy_commission * float(buy_fills[0]['price'])
        # Venda: A comissão já está em USDT
        sell_commission_usdt = sell_commission

        # Lucro líquido (após taxas)
        profit_with_fees = profit - (buy_commission_usdt + sell_commission_usdt)

        # Atualização do lucro total
        self.total_profit += profit_with_fees

        # Informações para o log
        print(f"Data e hora: {datetime.now()}")
        print(f"Lucro bruto: {profit:.2f} USDT")
        print(f"Lucro líquido após taxas: {profit_with_fees:.2f} USDT")
        print(f"Lucro líquido TOTAL: {self.total_profit:.2f} USDT")
        print(f"Balanço atual da Conta: {balance:.2f} USDT")

        # Gravação em arquivo
        with open('./lucros.txt', 'a') as file:  # 'a' para adicionar ao final do arquivo
            file.write(f"******************************* INICIO *******************************\n")
            file.write(f"Data e hora: {datetime.now()}\n")
            file.write(f"Lucro bruto: {profit:.2f} USDT\n")
            file.write(f"Lucro líquido após taxas: {profit_with_fees:.2f} USDT\n")
            file.write(f"Lucro líquido TOTAL: {self.total_profit:.2f} USDT\n")
            file.write(f"Balanço atual da conta: {balance:.2f} USDT\n")
            file.write(f"******************************* FIM *******************************\n\n\n")

    def execute_trading(self):
        self.get_sma()

        symbol_info = self.client.get_symbol_info(self.symbol)

        lot_size = next(filter for filter in symbol_info['filters'] if filter['filterType'] == 'LOT_SIZE')
        step_size = float(lot_size['stepSize'])

        balance = self.client.get_asset_balance(asset=self.asset)
        asset_balance = float(balance['free'])
        symbol_price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
        quantity = round_step_size((asset_balance / symbol_price) * 0.02, step_size)

        if self.symbol_df['position'].iloc[-1] == 1 and not self.position_to_sell:
            self.order_buy.append(self.place_buy_order(quantity, self.symbol))
            self.position_to_sell = not self.position_to_sell
            print(f"[BUY] {datetime.now()} ->", self.order_buy[-1])

        elif self.symbol_df['position'].iloc[-1] == -1 and self.position_to_sell:
            self.order_sell.append(self.place_sell_order(quantity, self.symbol))
            self.position_to_sell = not self.position_to_sell
            print(f"[SELL] {datetime.now()} ->", self.order_sell[-1])

            if len(self.order_buy) == len(self.order_sell):
                print(f"\n\n******************************* INICIO *******************************\n")
                self.calculate_profit_or_loss(self.order_buy[-1], self.order_sell[-1])
                print("\n******************************* FIM *******************************\n\n\n")

        else:
            print('No trade signal at this time.')



