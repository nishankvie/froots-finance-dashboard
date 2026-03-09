import pandas as pd
import streamlit as st
import plotly.express as px
st.title('Recovery Visualisation')
#create a dropdown
events = {
    'COVID Crash 2020':('2020-01-01', '2021-06-30'),
    '2022 Rate Spike':('2021-12-01', '2023-06-30'),
    '2023 Banking Crisis':('2023-01-01', '2023-12-31'),
    'Custom Date Range':None,  # special value for custom input
}
selected_event=st.selectbox('Select market events', events.keys())
if selected_event == 'Custom Date Range':
    col1,col2=st.columns(2)
    with col1:
        start_date= st.date_input('Start Date')
    with col2:
        end_date= st.date_input('End Date')
    start_str=str(start_date)
    end_str=str(end_date)
else:
    start_str, end_str= events[selected_event]

#load all ETF DATA now
tickers=["AGGG.L","VWCE.DE","EIMI.L","IUSV.DE","WSML.L"]
price_data={} # tickers-> price data
for ticker in tickers:
    df=pd.read_csv(f'data/{ticker}.csv',header=[0,1],index_col=0)
    df.index = pd.to_datetime(df.index)
    df.columns = df.columns.get_level_values(0)
    price_data[ticker]= df['Close']
#filter price data
filtered={}
for ticker, prices in price_data.items():
    filtered_prices= prices.loc[start_str:end_str]
    if not filtered_prices.empty:
        filtered[ticker]=filtered_prices
if len(filtered)==0:
    st.warning('No ETF data available for this time period.')
    st.stop()
normalised={}
for ticker, prices in filtered.items():
    first_price= prices.iloc[0]
    normalised[ticker]= (prices/first_price)*100
normalised_df=pd.concat(normalised, axis=1).sort_index()

#chart
fig=px.line(normalised_df, 
    title= f'Portfolio Recovery of {selected_event}',
    labels={'value': 'Normalised Price (start = 100)', 'index': 'Date' })
fig.add_hline(
    y=100,
    line_dash='dash',
    line_color='gray',
    annotation_text='Pre-crash level')
st.plotly_chart(fig, use_container_width= True)
#recovery time
st.subheader('Recovery Time')
cols= st.columns(len(normalised_df.columns))
for col, ticker in zip(cols, normalised_df.columns):
    series= normalised_df[ticker]
    crash_low_date=series.idxmin()
    recovery_series= series[series.index> crash_low_date]
    recovered= recovery_series[recovery_series>=100]
    if recovered.empty:
        recovery_text="NOT YET RECOVERED"
    else:
        recovery_date=recovered.index[0]
        months= ((recovery_date.year- pd.Timestamp(start_str).year)*12)+ (recovery_date.month- pd.Timestamp(start_str).month)
        recovery_text= f'{months} month'
    with col:
        st.metric(label=ticker,value=recovery_text)
