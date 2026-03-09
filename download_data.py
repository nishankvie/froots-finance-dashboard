import yfinance as yf
data_list=["AGGG.L","VWCE.DE","EIMI.L","IUSV.DE","WSML.L"]
for tickers in data_list:
    data= yf.download(tickers,period="max",auto_adjust=True)
    data.to_csv(f'data/{tickers}.csv')
 


