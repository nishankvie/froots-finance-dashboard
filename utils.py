import pandas as pd
import streamlit as st
from datetime import date, datetime


# ── Data loaders ─────────────────────────────────────────────────────────────

@st.cache_data
def load_clients():
    df = pd.read_csv('data/clients.csv')
    df['last_login_date'] = pd.to_datetime(df['last_login_date'])
    return df


@st.cache_data
def load_portfolios():
    return pd.read_csv('data/client_portfolios.csv')


@st.cache_data
def load_quant_events():
    df = pd.read_csv('data/quant_events.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['etf_ticker'] = df['etf_ticker'].fillna('')
    df['client_specific_name'] = df['client_specific_name'].fillna('')
    return df


@st.cache_data
def load_notes():
    df = pd.read_csv('data/client_notes.csv')
    df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data
def load_contacts():
    df = pd.read_csv('data/client_contacts.csv')
    df['contact_date'] = pd.to_datetime(df['contact_date'])
    return df


@st.cache_data
def load_aum_history():
    df = pd.read_csv('data/aum_history.csv')
    df['date'] = pd.to_datetime(df['date'])
    return df


# ── Score computation ─────────────────────────────────────────────────────────

def compute_health_score(client_row) -> int:
    """
    Computes a 0–100 health score from four signals (25 pts each):
    - Login frequency this week
    - Deposit activity (monthly_deposit > 0)
    - Portfolio size (up to €50,000)
    - Recent login (within 30 days)
    """
    days_since_login = (pd.Timestamp(date.today()) - client_row['last_login_date']).days

    login_score    = min(client_row['login_count_this_week'], 5) / 5 * 25
    deposit_score  = 25.0 if client_row['monthly_deposit'] > 0 else 0.0
    portfolio_score = min(client_row['portfolio_value_eur'] / 50_000, 1.0) * 25
    recency_score  = 25.0 if days_since_login <= 30 else 0.0

    return int(login_score + deposit_score + portfolio_score + recency_score)


def compute_churn_risk(client_row) -> str:
    """
    Returns 'High', 'Medium', or 'Low' churn risk.
    High: ALL THREE signals triggered
    Medium: ANY ONE signal triggered
    Low: none triggered
    """
    s1 = client_row['missed_deposits_last_3_months'] >= 2
    s2 = client_row['login_count_this_week'] <= 1
    s3 = client_row['portfolio_performance_pct'] < -3.0

    if s1 and s2 and s3:
        return 'High'
    elif s1 or s2 or s3:
        return 'Medium'
    return 'Low'


def health_color(score: int) -> str:
    if score >= 70:
        return 'green'
    elif score >= 40:
        return 'orange'
    return 'red'


def churn_color(risk: str) -> str:
    return {'High': 'red', 'Medium': 'orange', 'Low': 'green'}.get(risk, 'gray')


# ── Sidebar renderer ──────────────────────────────────────────────────────────

def render_sidebar():
    import streamlit.components.v1 as components

    components.html("""
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-3NB5QZVMMX"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-3NB5QZVMMX');
    </script>
    """, height=0)






    """
    Renders the persistent froots sidebar on every page.
    Includes: branding, KPI metrics, global search, and active client indicator.
    Call this at the top of every page after loading clients + aum data.
    """
    clients  = load_clients()
    aum_df   = load_aum_history()

    total_aum     = clients['portfolio_value_eur'].sum()
    annual_fee    = total_aum * 0.01
    total_clients = len(clients)
    st.logo("assets/froots_logo.png", size="large")
    with st.sidebar:

        # ── Global Search ──────────────────────────────────────────────────
        st.markdown('**🔍 Global Search**')
        query = st.text_input(
            'Search clients or ETF tickers',
            key='sidebar_search',
            placeholder='Name or ticker…',
            label_visibility='collapsed'
        )

        if query and query.strip():
            q = query.strip()

            # Client name match
            name_matches = clients[
                clients['name'].str.contains(q, case=False, na=False)
            ]

            # ETF ticker match (exact or partial)
            etf_tickers = ['VWCE.DE', 'EIMI.L', 'AGGG.L', 'IUSV.DE', 'WSML.L']
            is_etf = any(q.upper() in t.upper() for t in etf_tickers)

            if not name_matches.empty:
                if len(name_matches) == 1:
                    match = name_matches.iloc[0]
                    st.success(f'Found: {match["name"]}')
                    if st.button('Go to Profile', key='sidebar_go'):
                        st.session_state['selected_client_id'] = int(match['client_id'])
                        st.switch_page('pages/2_client_portfolio.py')
                else:
                    st.info(f'{len(name_matches)} clients match "{q}"')
                    sel = st.selectbox(
                        'Select client',
                        name_matches['name'].tolist(),
                        key='sidebar_select'
                    )
                    if st.button('Go to Profile', key='sidebar_go_multi'):
                        cid = int(
                            name_matches[name_matches['name'] == sel]['client_id'].iloc[0]
                        )
                        st.session_state['selected_client_id'] = cid
                        st.switch_page('pages/2_client_portfolio.py')
            elif is_etf:
                matched_ticker = next(
                    (t for t in etf_tickers if q.upper() in t.upper()), q.upper()
                )
                st.info(f'ETF search: {matched_ticker}')
                if st.button('View in Quant Feed', key='sidebar_etf'):
                    st.session_state['search_etf'] = matched_ticker
                    st.switch_page('pages/5_quant_feed.py')
            else:
                st.info(f'Keyword search: "{q}"')
                if st.button('Search Quant Feed', key='sidebar_kw'):
                    st.session_state['search_keyword'] = q
                    st.switch_page('pages/5_quant_feed.py')

        st.divider()

        st.metric('Total Clients', total_clients)
        st.metric('Total AUM', f'€{total_aum:,.0f}')
        st.metric('Annual Fee Revenue', f'€{annual_fee:,.0f}')

        st.divider()


        # ── Active client indicator ────────────────────────────────────────
        if 'selected_client_id' in st.session_state:
            cid = st.session_state['selected_client_id']
            match = clients[clients['client_id'] == cid]
            if not match.empty:
                client_name = match.iloc[0]['name']
                st.markdown(f'**Viewing:** {client_name}')
                if st.button('↩ Back to Profile', key='sidebar_back'):
                    st.switch_page('pages/2_client_portfolio.py')
