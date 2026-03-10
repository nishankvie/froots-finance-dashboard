import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import date
import utils

st.set_page_config(
    page_title='Customer Intelligence — froots',
    layout='wide',
    page_icon='assets/froots_logo.png',
    initial_sidebar_state='expanded'
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
utils.render_sidebar()

# ── Data ──────────────────────────────────────────────────────────────────────
clients    = utils.load_clients()
aum_history = utils.load_aum_history()
today      = pd.Timestamp(date.today())

# Compute derived columns for the full client table
clients['health_score'] = clients.apply(utils.compute_health_score, axis=1)
clients['churn_risk']   = clients.apply(utils.compute_churn_risk, axis=1)
clients['days_since_login'] = (today - clients['last_login_date']).dt.days
clients['annual_fee_eur']   = clients['portfolio_value_eur'] * 0.01

# ── Page title ────────────────────────────────────────────────────────────────
st.title('Customer Intelligence Dashboard')
st.caption('Overview of all clients, AUM performance, and risk signals.')
st.divider()

# ── Section 1: Metric cards ───────────────────────────────────────────────────
total_clients    = len(clients)
clients_at_risk  = int((clients['health_score'] < 40).sum())
high_login       = int((clients['login_count_this_week'] >= 5).sum())
inactive         = int((clients['days_since_login'] > 30).sum())
total_aum        = clients['portfolio_value_eur'].sum()
annual_fee_rev   = total_aum * 0.01

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.metric('Total Clients', total_clients)
with c2:
    st.metric('Clients At Risk', clients_at_risk, help='Health score below 40')
with c3:
    st.metric('High Login Activity', high_login, help='≥ 5 logins this week')
with c4:
    st.metric('Inactive (30+ days)', inactive, help='Last login older than 30 days')
with c5:
    st.metric('Total AUM', f'€{total_aum:,.0f}')
with c6:
    st.metric('Annual Fee Revenue', f'€{annual_fee_rev:,.0f}', help='AUM × 1%')

st.divider()

# ── Section 2: AUM Growth Chart ───────────────────────────────────────────────
st.subheader('Assets Under Management — 24 Month Growth')
fig_aum = px.line(
    aum_history,
    x='date',
    y='total_aum_eur',
    labels={'total_aum_eur': 'AUM (EUR)', 'date': 'Month'},
    markers=True
)
fig_aum.update_traces(line_color='#2ecc71', line_width=2.5)
fig_aum.update_layout(
    yaxis_tickformat='€,.0f',
    hovermode='x unified',
    margin=dict(t=20, b=20)
)
st.plotly_chart(fig_aum, use_container_width=True)

st.divider()

# ── Section 3: Client Risk Table ──────────────────────────────────────────────
st.subheader('Client Risk Overview')

# Build display dataframe
display_df = clients[[
    'name', 'health_score', 'churn_risk', 'risk_profile',
    'portfolio_value_eur', 'annual_fee_eur', 'monthly_deposit', 'last_login_date'
]].copy()

display_df.columns = [
    'Name', 'Health Score', 'Churn Risk', 'Risk Profile',
    'Portfolio Value (€)', 'Annual Fee (€)', 'Monthly Deposit (€)', 'Last Login'
]
display_df['Last Login'] = display_df['Last Login'].dt.strftime('%d %b %Y')
display_df['Portfolio Value (€)'] = display_df['Portfolio Value (€)'].map('{:,.0f}'.format)
display_df['Annual Fee (€)']      = display_df['Annual Fee (€)'].map('{:,.0f}'.format)
display_df['Monthly Deposit (€)'] = display_df['Monthly Deposit (€)'].map('{:,.0f}'.format)


def _color_health(val):
    if val >= 70:
        return 'background-color: #d4edda; color: #155724'
    elif val >= 40:
        return 'background-color: #fff3cd; color: #856404'
    return 'background-color: #f8d7da; color: #721c24'


def _color_churn(val):
    colors = {
        'High':   'background-color: #f8d7da; color: #721c24',
        'Medium': 'background-color: #fff3cd; color: #856404',
        'Low':    'background-color: #d4edda; color: #155724',
    }
    return colors.get(val, '')


styled = (
    display_df.style
    .applymap(_color_health, subset=['Health Score'])
    .applymap(_color_churn,  subset=['Churn Risk'])
)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()

# ── Section 4: Client Navigation ──────────────────────────────────────────────
st.subheader('Open Client Profile')

sorted_names = sorted(clients['name'].tolist())
selected_name = st.selectbox('Select a client', sorted_names, key='page1_select')

if st.button('Open Client Profile →', type='primary'):
    cid = int(clients[clients['name'] == selected_name]['client_id'].iloc[0])
    st.session_state['selected_client_id'] = cid
    st.switch_page('pages/2_client_portfolio.py')
