# Froots Intelligence Platform

An internal dashboard prototype built for the customer excellence team of a Vienna-based robo-advisor. The tool transforms raw client and portfolio data into actionable signals — so support teams know who needs attention, why, and what to do next.

**Live demo:** https://froots.streamlit.app

---

## Why Froots

Most finance projects built by students focus on trading tools or portfolio optimisation. I wanted to do something different.

I came to Vienna already deeply interested in fintech and investment companies. While exploring the ecosystem, Bitpanda and Froots stood out immediately. What drew me most strongly to Froots was the mission: making serious wealth management accessible to everyday Austrians, not just the wealthy. 

To better understand the problem they are solving, I analysed ECB Household Finance and Consumption Survey data (Wave 2021) and found that only **3.6% of Austrian 16–34 year olds own publicly traded shares** — the lowest in a European comparison and well below the euro area average of 10.1%.

That number made the mission concrete for me. It also made me think about what happens after Froots solves the acquisition problem — after a young Austrian decides to start investing. The harder challenge begins: keeping them engaged, informed, and calm through market volatility. That is where the customer excellence team comes in.

This prototype is my attempt to build something useful for that team.

---

## The Problem I Tried to Solve

When an investment algorithm makes a decision — rebalancing a portfolio, adjusting ETF weights, reacting to a volatility spike — the reasoning behind that decision is not always easily accessible to the customer excellence team. Yet they are the ones who speak directly with clients and must explain what happened and why.

I imagined this as an operational gap: a communication bridge missing between the quant team and the support team. This dashboard is a prototype of that bridge.

---

## What It Does
The two modules at the centre of this idea are the Customer Intelligence Dashboard and the Quant-to-Support Feed — these address the communication gap I described above. 

The Risk Metrics and Crash Recovery pages provide additional context when the customer excellence team speaks with clients during periods of market volatility.

**Customer Intelligence Dashboard**

- Live overview of total clients, AUM, clients at risk, and annual fee contribution
- 24-month AUM growth chart
- Full client risk table with health scores and churn risk indicators
- One-click navigation into any client profile

**Client Portfolio Overview**
- Complete client profile: risk profile, investment goal, portfolio value, YTD performance
- Health score (0–100) built from login activity, deposit consistency, portfolio size, and recency
- Churn risk: High / Medium / Low with the three signals that drive it
- Panic detection: flags clients logging in unusually often during market drops
- Portfolio allocation vs target with plain-English drift explanation per ETF
- Automatic ETF alerts: when the quant team posts an alert on VWCE.DE, every client holding that ETF sees it on their profile automatically
- Suggested action per client: "Recommend immediate phone call" / "Send reassurance email" / "No action needed"
- Full communication history with ability to log new contacts directly in the tool

**Risk Metrics Dashboard**
- ETF volatility, maximum drawdown, Sharpe ratio, correlation matrix
- Identifies clients most exposed to the highest-volatility ETF

**Crash Recovery Visualisation**
- Recovery curves for historical market events (COVID 2020 etc.)
- Identifies which current clients were invested during each crash period

**Quant-to-Support Feed**
- Quant and finance teams post alerts directly into the platform
- Alerts automatically identify affected clients by matching ETF holdings
- Support agents see relevant alerts on each client's profile in real time
- Plain-English explanations ready to copy into client emails

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| Streamlit | Multi-page web app framework |
| Pandas | Data processing and CSV management |
| Plotly | Interactive charts (gauge, pie, line, bar, heatmap) |
| CSV files | All data stored in editable flat files — replaceable with a database |

---

## Data

All client data is simulated. The dataset contains 50 Austrian clients with realistic names, varied risk profiles, and portfolio values between €5,000 and €150,000. ETF price data is sourced from Yahoo Finance for: VWCE.DE, EIMI.L, AGGG.L, IUSV.DE, WSML.L.

All data lives in CSV files in the `data/` directory. No values are hardcoded in Python. In production, CSV files would be replaced by live data connections.

---

## Project Structure

```
froots-finance-dashboard/
├── app.py                          # Entry point, redirects to dashboard
├── utils.py                        # Shared loaders, health score, churn risk, sidebar
├── data/
│   ├── clients.csv                 # 50 client profiles
│   ├── client_portfolios.csv       # 250 rows — 50 clients × 5 ETFs
│   ├── quant_events.csv            # Algorithm and risk alerts
│   ├── client_notes.csv            # Advisor notes per client
│   ├── client_contacts.csv         # Communication history
│   ├── aum_history.csv             # 24-month AUM growth
│   └── [ETF price CSVs]            # Yahoo Finance data
└── pages/
    ├── 1_customer_intelligence.py  # Main dashboard
    ├── 2_client_portfolio.py       # Client deep dive
    ├── 3_risk_metrics.py           # ETF analytics
    ├── 4_crash_recovery.py         # Market event recovery
    └── 5_quant_feed.py             # Alert feed and posting
```

---

## Running Locally

```bash
git clone https://github.com/nishankvie/froots-finance-dashboard
cd froots-finance-dashboard
pip install -r requirements.txt
streamlit run app.py
```

---

## Future Roadmap

This prototype is an initial concept and would need further development to become a fully functional internal tool. The natural next step would be working closely with the team to understand actual workflows, challenges, and priorities across the customer excellence, quant, and finance teams.

Potential directions for development:

- **Internal data integration** — connect the platform to the company's actual data sources so portfolio data, client activity, and ETF updates synchronise automatically instead of relying on CSV files
- **Automated weekly digest** — generate a Monday morning summary for the customer excellence team showing flagged clients, recent algorithm events, and suggested outreach priorities for the week
- **Client segmentation** — automatically group clients by behaviour patterns such as panic-prone during volatility, consistent depositors, or disengaged — helping the team prioritise who to contact and how
- **Expanded risk signals** — more granular churn indicators based on deposit trends, goal proximity, and portfolio underperformance relative to the client's specific risk profile

The goal would be to gradually evolve the prototype into a practical internal tool tailored to the company's real operational needs — ensuring it supports communication between teams and improves efficiency in handling client portfolios and updates. The features that matter most can only be identified by consulting the people who do this work every day.

---

## About

Built by Nishank — Mathematics and Data Science student at the University of Vienna (previously studied Computer Science at IIIT Delhi). I work primarily with Python and Pandas for data analysis, and SQL for data exploration and reporting.

This project was built independently as a way to demonstrate genuine interest in Froots's mission and to think seriously about the operational challenges a fintech startup at this stage might face.

Instead of sending a generic application, I wanted to demonstrate motivation in a more meaningful way. At a technical meetup in Vienna, someone said that what really stands out is when a candidate takes the time to build something — showing they have tried to understand the product and the company rather than just saying they are motivated. That stayed with me, so I started researching Froots, thinking about operational challenges a fintech startup might face, and exploring where a tool could be useful. This prototype is the result of that process. I would be happy to discuss these ideas further in person.