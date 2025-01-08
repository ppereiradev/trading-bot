import plotly.express as px

class BTCPlotter:

    def plot(self, btc_df):
        fig = px.line(btc_df,
                      x=btc_df.index,
                      y=['sma_short', 'sma_long', 'close'],
                      labels={'sma_short': 'SMA Curto', 'sma_long': 'SMA Longo', 'close': 'Preço de Fechamento'},
                      title='Preço de Fechamento e Médias Móveis de BTC')

        fig.write_html('grafico_btc.html')
