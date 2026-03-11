import streamlit as st

st.set_page_config(
    page_title='Froots Intelligence Platform',
    layout='wide',
    page_icon='assets/froots_logo.png',
    initial_sidebar_state='expanded'
)

st.logo("assets/froots_logo.png", size="large")

st.switch_page('pages/1_customer_intelligence.py')