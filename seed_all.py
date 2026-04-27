import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# Upload clients FIRST
clients = pd.read_csv("data/clients.csv")
clients['last_login_date'] = pd.to_datetime(clients['last_login_date'])
clients.to_sql("clients", engine, if_exists="append", index=False)

# Contacts
contacts = pd.read_csv("data/client_contacts.csv")
contacts['contact_date'] = pd.to_datetime(contacts['contact_date'])
contacts.to_sql("client_contacts", engine, if_exists="append", index=False)

# Notes
notes = pd.read_csv("data/client_notes.csv")
notes['date'] = pd.to_datetime(notes['date'])
notes.to_sql("client_notes", engine, if_exists="append", index=False)

# Portfolios
portfolios = pd.read_csv("data/client_portfolios.csv")
portfolios.to_sql("client_portfolios", engine, if_exists="append", index=False)

# Quant events
events = pd.read_csv("data/quant_events.csv")
events['timestamp'] = pd.to_datetime(events['timestamp'])
events.to_sql("quant_events", engine, if_exists="append", index=False)

# AUM
aum = pd.read_csv("data/aum_history.csv")
aum['date'] = pd.to_datetime(aum['date'])
aum.to_sql("aum_history", engine, if_exists="append", index=False)

print("✅ Data uploaded")