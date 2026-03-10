import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import utils

st.set_page_config(
    page_title='Client Portfolio — froots',
    layout='wide',
    page_icon='assets/froots_logo.png',
    initial_sidebar_state='expanded'
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
utils.render_sidebar()

# ── Guard ─────────────────────────────────────────────────────────────────────
if 'selected_client_id' not in st.session_state:
    st.info('👈 Select a client from the Customer Intelligence dashboard to view their profile.')
    if st.button('Go to Dashboard'):
        st.switch_page('pages/1_customer_intelligence.py')
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
clients    = utils.load_clients()
portfolios = utils.load_portfolios()
events     = utils.load_quant_events()
notes_all  = utils.load_notes()
contacts_all = utils.load_contacts()

cid    = st.session_state['selected_client_id']
client = clients[clients['client_id'] == cid]

if client.empty:
    st.error('Client not found. Return to the dashboard.')
    st.stop()

client = client.iloc[0]
today  = pd.Timestamp(date.today())

health_score = utils.compute_health_score(client)
churn_risk   = utils.compute_churn_risk(client)
days_since_login = (today - client['last_login_date']).days
annual_fee   = client['portfolio_value_eur'] * 0.01

health_badge = {
    'green':  '🟢 Healthy',
    'orange': '🟡 Moderate',
    'red':    '🔴 At Risk',
}[utils.health_color(health_score)]

churn_badge = {
    'red':    '🔴 High Risk',
    'orange': '🟡 Medium Risk',
    'green':  '🟢 Low Risk',
}[utils.churn_color(churn_risk)]

client_portfolio = portfolios[portfolios['client_id'] == cid]

# Last contact
client_contacts = contacts_all[contacts_all['client_id'] == cid].sort_values('contact_date', ascending=False)
if not client_contacts.empty:
    days_since_contact = (today - client_contacts.iloc[0]['contact_date']).days
else:
    days_since_contact = 999

# ── Page title ────────────────────────────────────────────────────────────────
st.title(f'Client Portfolio: {client["name"]}')
st.divider()

# ── Section 1: Client Profile Header ─────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown(f'### {client["name"]}')
    st.markdown(f'**Age:** {int(client["age"])}')
    st.markdown(f'**Risk Profile:** {client["risk_profile"].capitalize()}')
    st.markdown(f'**Investment Goal:** {client["investment_goal"]}')
    st.markdown(f'**Member for:** {int(client["months_since_joining"])} months')

with col_right:
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric('Portfolio Value', f'€{client["portfolio_value_eur"]:,.0f}')
    with m2:
        st.metric('Monthly Deposit', f'€{client["monthly_deposit"]:,.0f}')
    with m3:
        perf = client['portfolio_performance_pct']
        st.metric('YTD Performance', f'{perf:+.1f}%', delta=f'{perf:+.1f}%')

    b1, b2 = st.columns(2)
    with b1:
        st.markdown(f'**Health:** {health_badge}')
    with b2:
        st.markdown(f'**Churn Risk:** {churn_badge}')

st.info(f'💶 Annual fee contribution to froots: **€{annual_fee:,.0f}**')

# Suggested action
churn_signals = client['missed_deposits_last_3_months'] >= 2
if churn_risk == 'High':
    st.error('📞 **Suggested Action:** Recommend immediate phone call — high churn risk detected.')
elif health_score < 40:
    st.warning('📧 **Suggested Action:** Send reassurance email — health score is below threshold.')
elif days_since_contact >= 60:
    st.warning(f'📅 **Suggested Action:** Schedule monthly check-in — last contacted {days_since_contact} days ago.')
else:
    st.success('✅ **Suggested Action:** No action needed — client is engaged and on track.')

st.divider()

# ── Section 2: Portfolio Allocation Charts ────────────────────────────────────
st.subheader('Portfolio Allocation')

if client_portfolio.empty:
    st.warning('No portfolio data found for this client.')
else:
    col_pie, col_bar = st.columns(2)

    with col_pie:
        fig_pie = px.pie(
            client_portfolio,
            names='etf',
            values='weight_pct',
            title='Current Allocation',
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        melted = pd.melt(
            client_portfolio,
            id_vars=['etf'],
            value_vars=['target_pct', 'weight_pct'],
            var_name='type',
            value_name='value'
        )
        melted['type'] = melted['type'].map({'target_pct': 'Target', 'weight_pct': 'Current'})
        fig_bar = px.bar(
            melted,
            x='etf',
            y='value',
            color='type',
            barmode='group',
            title='Target vs Current',
            labels={'value': 'Allocation (%)', 'etf': 'ETF'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ── Section 3: Health Score and Churn Risk ────────────────────────────────────
st.subheader('Health Score & Churn Risk')

login_score    = min(client['login_count_this_week'], 5) / 5 * 25
deposit_score  = 25.0 if client['monthly_deposit'] > 0 else 0.0
portfolio_score = min(client['portfolio_value_eur'] / 50_000, 1.0) * 25
recency_score  = 25.0 if days_since_login <= 30 else 0.0

col_gauge, col_churn = st.columns(2)

with col_gauge:
    hcolor = utils.health_color(health_score)
    fig_gauge = go.Figure(go.Indicator(
        mode='gauge+number',
        value=health_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f'Health Score — {health_badge}'},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': hcolor},
            'steps': [
                {'range': [0, 40],   'color': '#ffe0e0'},
                {'range': [40, 70],  'color': '#fff3cd'},
                {'range': [70, 100], 'color': '#d4edda'},
            ],
            'threshold': {
                'line': {'color': 'black', 'width': 3},
                'thickness': 0.8,
                'value': health_score
            }
        }
    ))
    fig_gauge.update_layout(height=280, margin=dict(t=40, b=10))
    st.plotly_chart(fig_gauge, use_container_width=True)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric('Login Activity', f'{int(login_score)}/25')
    with s2:
        st.metric('Deposit Active', f'{int(deposit_score)}/25')
    with s3:
        st.metric('Portfolio Size', f'{int(portfolio_score)}/25')
    with s4:
        st.metric('Recent Login', f'{int(recency_score)}/25')

with col_churn:
    ccolor = utils.churn_color(churn_risk)
    badge_style = {
        'red':    ('#f8d7da', '#721c24'),
        'orange': ('#fff3cd', '#856404'),
        'green':  ('#d4edda', '#155724'),
    }[ccolor]

    st.markdown(
        f'<div style="background:{badge_style[0]};color:{badge_style[1]};'
        f'padding:20px;border-radius:8px;text-align:center;font-size:1.4rem;font-weight:bold;">'
        f'Churn Risk: {churn_risk}</div>',
        unsafe_allow_html=True
    )
    st.write('')
    st.markdown('**Risk Signals:**')

    sig1 = client['missed_deposits_last_3_months'] >= 2
    sig2 = client['login_count_this_week'] <= 1
    sig3 = client['portfolio_performance_pct'] < -3.0

    st.markdown(
        f'{"❌" if sig1 else "✅"} Missed deposits: '
        f'{int(client["missed_deposits_last_3_months"])} in last 3 months '
        f'(threshold: ≥ 2)'
    )
    st.markdown(
        f'{"❌" if sig2 else "✅"} Login activity: '
        f'{int(client["login_count_this_week"])} logins this week '
        f'(threshold: ≤ 1)'
    )
    st.markdown(
        f'{"❌" if sig3 else "✅"} Performance: '
        f'{client["portfolio_performance_pct"]:+.1f}% YTD '
        f'(threshold: < -3%)'
    )

st.divider()

# ── Section 4: Panic Detection ────────────────────────────────────────────────
st.subheader('Panic Detection')

high_login_flag   = client['login_count_this_week'] >= 5
negative_perf_flag = client['portfolio_performance_pct'] < -5.0

if high_login_flag and negative_perf_flag:
    st.error(
        f'🔴 **Critical — Potential Panic Behaviour Detected**\n\n'
        f'- Login count this week: **{int(client["login_count_this_week"])}** (threshold: ≥ 5)\n'
        f'- YTD performance: **{client["portfolio_performance_pct"]:+.1f}%** (threshold: < -5%)\n\n'
        'Recommend: proactive outreach from support team immediately.'
    )
elif high_login_flag:
    st.warning(
        f'🟡 **Warning — High Login Activity**\n\n'
        f'- Login count this week: **{int(client["login_count_this_week"])}** (threshold: ≥ 5)\n'
        f'- Performance is within normal range ({client["portfolio_performance_pct"]:+.1f}%).\n\n'
        'Monitor: client may have questions about recent market movements.'
    )
elif negative_perf_flag:
    st.warning(
        f'🟡 **Warning — Negative Performance Signal**\n\n'
        f'- YTD performance: **{client["portfolio_performance_pct"]:+.1f}%** (threshold: < -5%)\n'
        f'- Login frequency is normal ({int(client["login_count_this_week"])} this week).\n\n'
        'Monitor: no immediate panic signs but performance may prompt client contact.'
    )
else:
    st.success(
        f'🟢 **All Clear — No Panic Signals**  '
        f'Logins this week: {int(client["login_count_this_week"])} | '
        f'YTD: {client["portfolio_performance_pct"]:+.1f}%'
    )

st.divider()

# ── Section 5: Portfolio Drift + Advisor Notes ────────────────────────────────
st.subheader('Portfolio Drift & Advisor Notes')

with st.expander('📊 Portfolio Drift Details', expanded=True):
    if client_portfolio.empty:
        st.info('No portfolio data available.')
    else:
        for _, row in client_portfolio.iterrows():
            drift = round(row['weight_pct'] - row['target_pct'], 1)
            if drift > 1.0:
                st.markdown(
                    f'🔺 **{row["etf"]}** is **{drift}% above target** '
                    f'({row["weight_pct"]}% current vs {row["target_pct"]}% target) '
                    f'— may be rebalanced down soon.'
                )
            elif drift < -1.0:
                st.markdown(
                    f'🔻 **{row["etf"]}** is **{abs(drift)}% below target** '
                    f'({row["weight_pct"]}% current vs {row["target_pct"]}% target) '
                    f'— may receive additional allocation.'
                )
            else:
                st.markdown(f'✅ **{row["etf"]}** is on target ({row["target_pct"]}%).')

st.markdown('**Advisor Notes**')
client_notes = notes_all[notes_all['client_id'] == cid].sort_values('date', ascending=False)

if not client_notes.empty:
    display_notes = client_notes[['date', 'note_text', 'added_by']].copy()
    display_notes['date'] = display_notes['date'].dt.strftime('%d %b %Y')
    display_notes.columns = ['Date', 'Note', 'Added By']
    st.dataframe(display_notes, use_container_width=True, hide_index=True)
else:
    st.caption('No notes yet.')

with st.form('add_note_form', clear_on_submit=True):
    st.markdown('**Add New Note**')
    note_author = st.text_input('Your name', placeholder='e.g. Lisa Wagner')
    note_text   = st.text_area('Note', placeholder='Type advisor note here…')
    submitted   = st.form_submit_button('Save Note')
    if submitted:
        if not note_text.strip():
            st.warning('Note text cannot be empty.')
        else:
            notes_df = utils.load_notes()
            next_id  = int(notes_df['note_id'].max()) + 1 if not notes_df.empty else 1
            new_row  = pd.DataFrame([{
                'note_id':  next_id,
                'client_id': cid,
                'date':     date.today().isoformat(),
                'note_text': note_text.strip(),
                'added_by': note_author.strip() if note_author.strip() else 'Unknown'
            }])
            updated = pd.concat([notes_df, new_row], ignore_index=True)
            updated.to_csv('data/client_notes.csv', index=False)
            st.cache_data.clear()
            st.success('Note saved.')
            st.rerun()

st.divider()

# ── Section 6: ETF Alerts for This Client ────────────────────────────────────
st.subheader('Recent ETF Alerts')

if client_portfolio.empty:
    st.info('No portfolio data to match alerts against.')
else:
    client_etfs = client_portfolio['etf'].tolist()
    cutoff      = pd.Timestamp(today) - pd.Timedelta(days=7)
    recent_events = events[
        (events['etf_ticker'].isin(client_etfs)) &
        (events['timestamp'] >= cutoff)
    ].sort_values('timestamp', ascending=False)

    if recent_events.empty:
        st.success('✅ No recent ETF alerts for this client\'s holdings in the past 7 days.')
    else:
        for _, ev in recent_events.iterrows():
            ts_str = ev['timestamp'].strftime('%d %b %Y %H:%M')
            content = (
                f'**{ev["event_type"]}** · {ts_str} · ETF: `{ev["etf_ticker"]}`\n\n'
                f'{ev["reason"]}'
            )
            if ev['severity'] == 'critical':
                st.error(content)
            elif ev['severity'] == 'warning':
                st.warning(content)
            else:
                st.info(content)

st.divider()

# ── Section 7: Best Time to Reach Out ────────────────────────────────────────
st.subheader('Best Time to Reach Out')

weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
login_day     = client['last_login_date'].weekday()
day_type      = 'weekday' if login_day < 5 else 'weekend'
day_name      = weekday_names[login_day]

if not client_contacts.empty:
    last_contact_str = f'Last contacted **{days_since_contact} days ago** ({client_contacts.iloc[0]["contact_type"]}).'
else:
    last_contact_str = 'No contact history found.'

urgent = days_since_contact > 60 and churn_risk == 'High'

if churn_risk == 'High' or days_since_contact > 30:
    recommendation = '📞 **Recommended:** Schedule a call this week — elevated risk or extended time since last contact.'
else:
    recommendation = '📧 **Recommended:** Send monthly portfolio update — client is engaged and up to date.'

message = (
    f'🗓️ Client typically active on **{day_type}s** (last seen on a {day_name}).  \n'
    f'{last_contact_str}  \n'
    f'{recommendation}'
)

if urgent:
    st.error(message)
else:
    st.info(message)

st.divider()

# ── Section 8: Communication History ─────────────────────────────────────────
st.subheader('Communication History')

if not client_contacts.empty:
    disp_contacts = client_contacts[[
        'contact_date', 'contact_type', 'agent_name', 'description', 'outcome'
    ]].copy()
    disp_contacts['contact_date'] = disp_contacts['contact_date'].dt.strftime('%d %b %Y')
    disp_contacts.columns = ['Date', 'Type', 'Agent', 'Description', 'Outcome']
    st.dataframe(disp_contacts, use_container_width=True, hide_index=True)
else:
    st.caption('No contact history yet.')

with st.form('add_contact_form', clear_on_submit=True):
    st.markdown('**Log New Contact**')
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        contact_date = st.date_input('Date', value=date.today())
    with fc2:
        contact_type = st.selectbox('Type', ['Phone Call', 'Email', 'Meeting', 'Chat'])
    with fc3:
        agent_name = st.text_input('Agent name', placeholder='Your name')

    description = st.text_area('Description', placeholder='Brief summary of the conversation…')
    outcome     = st.text_input('Outcome', placeholder='e.g. Resolved — no changes')
    submitted   = st.form_submit_button('Log Contact')

    if submitted:
        if not description.strip():
            st.warning('Description cannot be empty.')
        else:
            contacts_df = utils.load_contacts()
            next_id     = int(contacts_df['contact_id'].max()) + 1 if not contacts_df.empty else 1
            new_row     = pd.DataFrame([{
                'contact_id':   next_id,
                'client_id':    cid,
                'contact_date': contact_date.isoformat(),
                'contact_type': contact_type,
                'agent_name':   agent_name.strip() if agent_name.strip() else 'Unknown',
                'description':  description.strip(),
                'outcome':      outcome.strip()
            }])
            updated = pd.concat([contacts_df, new_row], ignore_index=True)
            updated.to_csv('data/client_contacts.csv', index=False)
            st.cache_data.clear()
            st.success('Contact logged.')
            st.rerun()
