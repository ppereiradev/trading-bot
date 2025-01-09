import os
import pandas as pd
import numpy as np
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from utils.trading_bot import TradingBot


api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")
asset = os.getenv("BINANCE_ASSET")
symbol = os.getenv("BINANCE_SYMBOL")
api_url = 'https://testnet.binance.vision/api' # set as None in production


trading_bot = TradingBot(api_key, secret_key, api_url, asset, symbol)


app = Dash(__name__)

app.layout = html.Div([
    html.H1(f"Gráfico de {asset} com Médias Móveis", style={"textAlign": "center"}),
    dcc.Graph(id='asset-graph'),
    dcc.Interval(
        id='interval-component',
        interval=150 * 1000, # time to update chart (150 seconds)
        n_intervals=0
    )
])

# Callback to update chart
@app.callback(
    Output('asset-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n_intervals):

    trading_bot.execute_trading()
    print(trading_bot.get_last_row(), "\n")
    symbol_df = trading_bot.get_symbol_to_plot()


    fig = px.line(
        symbol_df,
        x=symbol_df.index,
        y=['sma_short', 'sma_long', 'close'],
        labels={
            'sma_short': 'SMA Curto',
            'sma_long': 'SMA Longo',
            'close': 'Preço de Fechamento'
        },
        title=f'Preço de Fechamento e Médias Móveis de {asset}'
    )
    return fig


if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=8050, debug=True)
