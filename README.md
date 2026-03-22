# Tidewatch

Tidewatch is a FastAPI-based stock data and portfolio management project. It currently includes portfolio management, watchlist monitoring, Xueqiu portfolios, stock list queries, and K-line export features, with PostgreSQL as the main datastore.

## Main Features

- Portfolio management
- Watchlist monitoring
- Xueqiu portfolio view
- Stock list query and maintenance
- Tools such as cost calculation and K-line export
- Scheduled K-line and stock list updates

## Pages

- `/`
- `/admin`
- `/monitor`
- `/tools`
- `/xueqiu`

## APIs

- `/api/portfolio`
- `/api/monitor`
- `/api/admin`
- `/api/tools`
- `/api/xueqiu`
- `/api/stock-list`

## Run

```bash
pip install -r requirements.txt
python app.py
```
