import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import utils

st.set_page_config(
    page_title='Risk Metrics — froots',
    layout='wide',
    page_icon='assets/froots_logo.png',
    initial_sidebar_state='expanded'
)

utils.render_sidebar()

st.title('Risk Metrics Dashboard')
st.caption('ETF-level risk analytics: volatility, drawdown, Sharpe ratio, correlations.')
st.divider()

# ── ETF price loading (ported verbatim from tab3_risk.py) ─────────────────────
tickers = ['AGGG.L', 'VWCE.DE', 'EIMI.L', 'IUSV.DE', 'WSML.L']

@st.cache_data
def load_price_data():
    price_data = {}
    for ticker in tickers:
        df = pd.read_csv(f'data/{ticker}.csv', header=[0, 1], index_col=0)
        df.index = pd.to_datetime(df.index)
        df.columns = df.columns.get_level_values(0)
        price_data[ticker] = df['Close']
    return price_data

price_data = load_price_data()

# Daily returns
daily_return_dic = {}
for ticker in tickers:
    daily_return = price_data[ticker].pct_change()
    daily_return_dic[ticker] = daily_return
returns_df = pd.concat(daily_return_dic, axis=1)

# ── Daily Returns Table ───────────────────────────────────────────────────────
st.subheader('Daily ETF Returns')
st.dataframe(returns_df.tail(30).style.format('{:.4f}'), use_container_width=True)

st.divider()

# ── Rolling Volatility ────────────────────────────────────────────────────────
st.subheader('30-Day Rolling Volatility (Annualised)')
rol_std = returns_df.rolling(window=30).std()
volatility_df = rol_std * np.sqrt(252)

fig_vol = px.line(
    volatility_df.dropna(),
    title='Annualised Volatility (30-day window)',
    labels={'value': 'Annualised Volatility', 'index': 'Date'}
)
st.plotly_chart(fig_vol, use_container_width=True)

st.divider()

# ── Maximum Drawdown ──────────────────────────────────────────────────────────
st.subheader('Maximum Drawdown')
price_index  = (1 + returns_df).cumprod()
running_max  = price_index.cummax()
drawdown_df  = (price_index - running_max) / running_max
max_drawdown = drawdown_df.min()

cols = st.columns(len(tickers))
for col, ticker in zip(cols, tickers):
    with col:
        st.metric(label=ticker, value=f'{max_drawdown[ticker]:.2%}')

st.divider()

# ── Sharpe Ratio ──────────────────────────────────────────────────────────────
st.subheader('Sharpe Ratio (annualised, risk-free rate = 0)')
sharpe = (returns_df.mean() * 252) / (returns_df.std() * np.sqrt(252))

cols = st.columns(len(tickers))
for col, ticker in zip(cols, tickers):
    with col:
        color = 'normal' if sharpe[ticker] > 0 else 'inverse'
        st.metric(label=ticker, value=f'{sharpe[ticker]:.2f}')

st.divider()

# ── Correlation Heatmap ───────────────────────────────────────────────────────
st.subheader('Correlation Matrix')
corr = returns_df.corr()
fig_heatmap = go.Figure(data=go.Heatmap(
    z=corr.values,
    x=corr.columns.tolist(),
    y=corr.index.tolist(),
    colorscale='RdYlGn',
    zmin=-1,
    zmax=1,
    text=corr.round(2).values,
    texttemplate='%{text}',
))
fig_heatmap.update_layout(title='ETF Return Correlations', height=450)
st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# ── Clients Most Exposed ──────────────────────────────────────────────────────
st.subheader('Clients Most Exposed')

# Identify highest-volatility ETF (most recent annualised vol value)
latest_vol = volatility_df.dropna().iloc[-1]
highest_vol_ticker = latest_vol.idxmax()
highest_vol_value  = latest_vol.max()

st.markdown(
    f'Highest current volatility ETF: **{highest_vol_ticker}** '
    f'({highest_vol_value:.1%} annualised) — showing clients with weight > 30% in this ETF.'
)

portfolios = utils.load_portfolios()
clients    = utils.load_clients()
clients['churn_risk'] = clients.apply(utils.compute_churn_risk, axis=1)

exposed = portfolios[
    (portfolios['etf'] == highest_vol_ticker) &
    (portfolios['weight_pct'] > 30)
].merge(
    clients[['client_id', 'name', 'portfolio_value_eur', 'churn_risk']],
    on='client_id'
)[['name', 'portfolio_value_eur', 'weight_pct', 'churn_risk']].copy()

exposed.columns = ['Client Name', 'Portfolio Value (€)', f'{highest_vol_ticker} Weight (%)', 'Churn Risk']
exposed['Portfolio Value (€)'] = exposed['Portfolio Value (€)'].map('{:,.0f}'.format)
exposed = exposed.sort_values(f'{highest_vol_ticker} Weight (%)', ascending=False)

if exposed.empty:
    st.info(f'No clients hold more than 30% in {highest_vol_ticker}.')
else:
    st.dataframe(exposed, use_container_width=True, hide_index=True)
