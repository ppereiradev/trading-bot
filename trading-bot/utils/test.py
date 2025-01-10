import os

from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from binance.client import Client
from binance.helpers import round_step_size


api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")
asset = os.getenv("BINANCE_ASSET")
symbol = os.getenv("BINANCE_SYMBOL")
api_url = 'https://testnet.binance.vision/api' # set as None in production


client = Client(api_key, secret_key)
client.API_URL = api_url
position_to_sell = False
total_profit = 0
order_buy = []
order_sell = []

symbol_info = client.get_symbol_info(symbol)

lot_size = next(filter for filter in symbol_info['filters'] if filter['filterType'] == 'LOT_SIZE')
step_size = float(lot_size['stepSize'])

balance = client.get_asset_balance(asset=asset)
asset_balance = float(balance['free'])
symbol_price = float(client.get_symbol_ticker(symbol=symbol)['price'])
quantity = round_step_size((asset_balance / symbol_price) * 0.02, step_size)


def place_buy_order(quantity, symbol):
    try:
        order = client.order_market_buy(
            symbol=symbol,
            quantity=quantity)
        print(f"Bought {symbol}")
        return order
    except Exception as e:
        print(f'An error occurred: {e}')
        return None

def place_sell_order(quantity, symbol):
    try:
        order = client.order_market_sell(
            symbol=symbol,
            quantity=quantity)
        print(f"Sold {symbol}")
        return order
    except Exception as e:
        print(f'An error occurred: {e}')
        return None

def calculate_profit(order_buy, order_sell):
    global total_profit

    # Informações do saldo atual
    balance = float(client.get_asset_balance(asset='USDT')['free'])

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
    total_profit += profit_with_fees

    # Informações para o log
    print(f"Data e hora: {datetime.now()}")
    print(f"Lucro bruto: {profit:.2f} USDT")
    print(f"Lucro líquido após taxas: {profit_with_fees:.2f} USDT")
    print(f"Lucro líquido TOTAL: {total_profit:.2f} USDT")
    print(f"Balanço atual da Conta: {balance:.2f} USDT")

    # Gravação em arquivo
    with open('./lucros.txt', 'a') as file:  # 'a' para adicionar ao final do arquivo
        file.write(f"******************************* INICIO *******************************\n")
        file.write(f"Data e hora: {datetime.now()}\n")
        file.write(f"Lucro bruto: {profit:.2f} USDT\n")
        file.write(f"Lucro líquido após taxas: {profit_with_fees:.2f} USDT\n")
        file.write(f"Lucro líquido TOTAL: {total_profit:.2f} USDT\n")
        file.write(f"Balanço atual da conta: {balance:.2f} USDT\n")
        file.write(f"******************************* FIM *******************************\n\n\n")



if __name__ == "__main__":

    order_buy.append(place_buy_order(quantity, symbol))
    position_to_sell = not position_to_sell
    print(f"[BUY] {datetime.now()} ->", order_buy[-1])

    order_sell.append(place_sell_order(quantity, symbol))
    position_to_sell = not position_to_sell
    print(f"[SELL] {datetime.now()} ->", order_sell[-1])

    print(f"\n\n******************************* INICIO *******************************\n")
    calculate_profit(order_buy[-1], order_sell[-1])
    print("\n******************************* FIM *******************************\n\n\n")
