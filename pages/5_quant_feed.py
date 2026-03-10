import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
from datetime import datetime, date
import utils

st.set_page_config(
    page_title='Quant & Support Feed — froots',
    layout='wide',
    page_icon='assets/froots_logo.png',
    initial_sidebar_state='expanded'
)

utils.render_sidebar()

st.title('Quant & Support Feed')
st.caption(f'Last updated: {datetime.now().strftime("%d %b %Y, %H:%M")}')
st.divider()

# ── Data ──────────────────────────────────────────────────────────────────────
events     = utils.load_quant_events()
portfolios = utils.load_portfolios()
clients    = utils.load_clients()

# Pre-populate search from session state (set by sidebar global search)
default_keyword = st.session_state.pop('search_keyword', '')
default_etf     = st.session_state.pop('search_etf', '')

# ── Section 1: Filters ────────────────────────────────────────────────────────
st.subheader('Filters')

all_types      = sorted(events['event_type'].unique().tolist())
all_severities = ['All', 'info', 'warning', 'critical']

fcol1, fcol2, fcol3 = st.columns(3)
with fcol1:
    selected_types = st.multiselect(
        'Event type', options=all_types, default=all_types
    )
with fcol2:
    selected_severity = st.selectbox('Severity', all_severities)
with fcol3:
    keyword = st.text_input(
        'Keyword search (reason text)',
        value=default_keyword or default_etf,
        placeholder='e.g. VWCE, rebalance…'
    )

# Apply filters
filtered = events.copy()
if selected_types:
    filtered = filtered[filtered['event_type'].isin(selected_types)]
if selected_severity != 'All':
    filtered = filtered[filtered['severity'] == selected_severity]
if keyword.strip():
    kw = keyword.strip()
    filtered = filtered[
        filtered['reason'].str.contains(kw, case=False, na=False) |
        filtered['etf_ticker'].str.contains(kw, case=False, na=False) |
        filtered['event_type'].str.contains(kw, case=False, na=False)
    ]
filtered = filtered.sort_values('timestamp', ascending=False).reset_index(drop=True)

st.divider()

# ── Section 2: Create New Alert ───────────────────────────────────────────────
with st.expander('➕ Post New Alert', expanded=False):
    with st.form('new_alert_form', clear_on_submit=True):
        na1, na2 = st.columns(2)
        with na1:
            new_etf    = st.text_input('ETF ticker (optional)', placeholder='e.g. VWCE.DE')
            new_client = st.text_input('Client name (optional — for client-specific alert)')
            new_type   = st.selectbox(
                'Event type',
                ['Risk Alert', 'Rebalance Alert', 'Information Update', 'Team Task', 'Client Alert']
            )
        with na2:
            new_severity = st.selectbox('Severity', ['info', 'warning', 'critical'])
            new_reason   = st.text_area('Reason / description', height=120, placeholder='Plain English explanation…')

        submitted = st.form_submit_button('Post Alert', type='primary')
        if submitted:
            if not new_reason.strip():
                st.warning('Reason cannot be empty.')
            else:
                ev_df   = utils.load_quant_events()
                next_id = int(ev_df['event_id'].max()) + 1 if not ev_df.empty else 1

                # Auto-detect affected clients
                affected_count = 0
                affected_names = []
                etf_clean = new_etf.strip().upper()
                if etf_clean:
                    matches = portfolios[portfolios['etf'].str.upper() == etf_clean]
                    affected_ids = matches['client_id'].unique()
                    affected_count = len(affected_ids)
                    affected_names = clients[
                        clients['client_id'].isin(affected_ids)
                    ]['name'].tolist()

                new_row = pd.DataFrame([{
                    'event_id':             next_id,
                    'timestamp':            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'event_type':           new_type,
                    'reason':               new_reason.strip(),
                    'affected_clients':     affected_count,
                    'severity':             new_severity,
                    'etf_ticker':           new_etf.strip(),
                    'client_specific_name': new_client.strip()
                }])
                updated = pd.concat([ev_df, new_row], ignore_index=True)
                updated.to_csv('data/quant_events.csv', index=False)
                st.cache_data.clear()

                if affected_count > 0:
                    names_preview = ', '.join(affected_names[:5])
                    suffix = f' and {affected_count - 5} more' if affected_count > 5 else ''
                    st.success(
                        f'Alert posted. {affected_count} client(s) affected: {names_preview}{suffix}.'
                    )
                else:
                    st.success('Alert posted.')
                st.rerun()

st.divider()

# ── Section 3: Event Timeline ─────────────────────────────────────────────────
st.subheader(f'Event Timeline — {len(filtered)} event(s)')

SEVERITY_ICONS = {'info': '🔵', 'warning': '🟡', 'critical': '🔴'}

if filtered.empty:
    st.info('No events match the current filters.')
else:
    for _, row in filtered.iterrows():
        severity = row['severity']
        icon     = SEVERITY_ICONS.get(severity, '⚪')
        ts_str   = row['timestamp'].strftime('%d %b %Y  %H:%M')

        header_parts = [f'**{row["event_type"]}**', ts_str]
        if row['etf_ticker']:
            header_parts.append(f'ETF: `{row["etf_ticker"]}`')
        if row['client_specific_name']:
            header_parts.append(f'Client: {row["client_specific_name"]}')

        content = ' · '.join(header_parts) + f'\n\n{row["reason"]}'
        if row['affected_clients'] > 0:
            content += f'\n\n*Affected clients: {int(row["affected_clients"])}*'

        time_col, card_col = st.columns([1, 5])
        with time_col:
            st.markdown(f'{icon} `{ts_str}`')

        with card_col:
            if severity == 'critical':
                st.error(content)
            elif severity == 'warning':
                st.warning(content)
            else:
                st.info(content)

            # Expand to view affected clients
            if row['etf_ticker']:
                etf_clean = row['etf_ticker'].strip().upper()
                matches   = portfolios[portfolios['etf'].str.upper() == etf_clean]
                if not matches.empty:
                    affected_ids   = matches['client_id'].unique()
                    affected_names = clients[
                        clients['client_id'].isin(affected_ids)
                    ][['name', 'risk_profile', 'portfolio_value_eur']].copy()
                    affected_names.columns = ['Client', 'Risk Profile', 'Portfolio (€)']
                    affected_names['Portfolio (€)'] = affected_names['Portfolio (€)'].map('{:,.0f}'.format)

                    with st.expander(f'View {len(affected_names)} affected client(s)'):
                        st.dataframe(affected_names, use_container_width=True, hide_index=True)

            # Copy email text
            with st.expander('📋 Copy email text'):
                st.code(row['reason'], language=None)

        st.divider()
