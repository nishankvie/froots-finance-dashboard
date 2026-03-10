import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import date
import utils

st.set_page_config(
    page_title='Crash Recovery — froots',
    layout='wide',
    page_icon='assets/froots_logo.png',
    initial_sidebar_state='expanded'
)

utils.render_sidebar()

st.title('Crash Recovery Visualisation')
st.caption('Normalised ETF performance during historical market stress events.')
st.divider()

# ── Event selector (ported verbatim from tab4_recovery.py) ───────────────────
events = {
    'COVID Crash 2020':    ('2020-01-01', '2021-06-30'),
    '2022 Rate Spike':     ('2021-12-01', '2023-06-30'),
    '2023 Banking Crisis': ('2023-01-01', '2023-12-31'),
    'Custom Date Range':   None,
}

selected_event = st.selectbox('Select market event', events.keys())

if selected_event == 'Custom Date Range':
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input('Start Date')
    with col2:
        end_date = st.date_input('End Date')
    start_str = str(start_date)
    end_str   = str(end_date)
else:
    start_str, end_str = events[selected_event]

# ── Load ETF data ─────────────────────────────────────────────────────────────
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

# Filter by date range
filtered = {}
for ticker, prices in price_data.items():
    fp = prices.loc[start_str:end_str]
    if not fp.empty:
        filtered[ticker] = fp

if not filtered:
    st.warning('No ETF data available for this time period.')
    st.stop()

# Normalise (start = 100)
normalised = {}
for ticker, prices in filtered.items():
    normalised[ticker] = (prices / prices.iloc[0]) * 100

normalised_df = pd.concat(normalised, axis=1).sort_index()

# ── Recovery chart ────────────────────────────────────────────────────────────
fig = px.line(
    normalised_df,
    title=f'Portfolio Recovery — {selected_event}',
    labels={'value': 'Normalised Price (start = 100)', 'index': 'Date'}
)
fig.add_hline(
    y=100,
    line_dash='dash',
    line_color='gray',
    annotation_text='Pre-crash level'
)
st.plotly_chart(fig, use_container_width=True)

# ── Recovery time metrics ─────────────────────────────────────────────────────
st.subheader('Recovery Time')
cols = st.columns(len(normalised_df.columns))
for col, ticker in zip(cols, normalised_df.columns):
    series = normalised_df[ticker]
    crash_low_date  = series.idxmin()
    recovery_series = series[series.index > crash_low_date]
    recovered       = recovery_series[recovery_series >= 100]

    if recovered.empty:
        recovery_text = 'NOT YET RECOVERED'
    else:
        recovery_date = recovered.index[0]
        months = (
            (recovery_date.year  - pd.Timestamp(start_str).year)  * 12 +
            (recovery_date.month - pd.Timestamp(start_str).month)
        )
        recovery_text = f'{months} months'

    with col:
        st.metric(label=ticker, value=recovery_text)

st.divider()

# ── Clients Who Experienced This Event ───────────────────────────────────────
st.subheader('Clients Who Experienced This Event')

today = pd.Timestamp(date.today())
event_start = pd.Timestamp(start_str)
months_at_event_start = max(
    int((today - event_start).days // 30), 0
)

clients = utils.load_clients()
clients['health_score'] = clients.apply(utils.compute_health_score, axis=1)

invested_then = clients[
    clients['months_since_joining'] >= months_at_event_start
].copy()

st.markdown(
    f'Clients who were invested during **{selected_event}** '
    f'(joined ≥ {months_at_event_start} months ago): **{len(invested_then)}**'
)

if invested_then.empty:
    st.info('No clients were invested during this event window.')
else:
    display = invested_then[[
        'name', 'portfolio_value_eur', 'months_since_joining', 'health_score', 'risk_profile'
    ]].copy()
    display.columns = [
        'Client Name', 'Portfolio Value (€)', 'Months Joined', 'Health Score', 'Risk Profile'
    ]
    display['Portfolio Value (€)'] = display['Portfolio Value (€)'].map('{:,.0f}'.format)
    display = display.sort_values('Months Joined', ascending=False)
    st.dataframe(display, use_container_width=True, hide_index=True)
