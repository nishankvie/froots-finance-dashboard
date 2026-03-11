import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title='Froots Intelligence Platform',
    layout='wide',
    page_icon='assets/froots_logo.png',
    initial_sidebar_state='expanded'
)

st.logo("assets/froots_logo.png", size="large")

components.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-3NB5QZVMMX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-3NB5QZVMMX');
</script>
""", height=0)

st.switch_page('pages/1_customer_intelligence.py')