import pandas as pd
import streamlit as st
import plotly.express as px
st.title('Portfolio Overview')
portfolio= pd.read_csv('data/portfolio.csv') 
#drift calculate
portfolio['Drift']=portfolio['current_pct']-portfolio['target_pct']
#get dataframe
st.dataframe(portfolio)

melted=pd.melt(portfolio,id_vars=['etf'],value_vars=['target_pct', 'current_pct'],var_name='type',value_name='value')
fig=px.bar(melted,title='graph of values',x='etf',y='value',color='type',barmode='group')
st.plotly_chart(fig, use_container_width=True)
list_etf= portfolio['etf']
cols=st.columns(portfolio.shape[0])

for col, (index,row) in zip(cols,portfolio.iterrows()):
    with col:
        st.metric(label=row['etf'],value=f"{row['current_pct']}%", delta=row['Drift'],delta_color='normal' if row['Drift']>0 else 'inverse' )
