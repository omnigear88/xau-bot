import os
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

import requests
from dotenv import load_dotenv


BASE_URL = "https://api.massive.com"
DEFAULT_SYMBOL = "C:XAUUSD"


def get_massive_api_key():
    load_dotenv()
    api_key = os.getenv("MASSIVE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "MASSIVE_API_KEY is not set. Add it to your .env file before "
            "running Massive bootstrap or live mode."
        )

    return api_key


def fetch_forex_aggregates(symbol, multiplier, timespan, from_date, to_date):
    api_key = get_massive_api_key()
    encoded_symbol = quote(symbol, safe=":")
    url = (
        f"{BASE_URL}/v2/aggs/ticker/{encoded_symbol}/range/"
        f"{multiplier}/{timespan}/{from_date}/{to_date}"
    )

    response = requests.get(
        url,
        params={
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
            "apiKey": api_key,
        },
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    if payload.get("status") == "ERROR":
        raise RuntimeError(payload.get("error") or "Massive API returned an error.")

    results = payload.get("results") or []

    candles = []
    for row in results:
        candles.append({
            "time": datetime.fromtimestamp(row["t"] / 1000, UTC),
            "open": float(row["o"]),
            "high": float(row["h"]),
            "low": float(row["l"]),
            "close": float(row["c"]),
        })

    return candles


def bootstrap_1m_history(symbol=DEFAULT_SYMBOL, days=5):
    today = datetime.now(UTC).date()
    from_date = today - timedelta(days=days)

    return fetch_forex_aggregates(
        symbol=symbol,
        multiplier=1,
        timespan="minute",
        from_date=from_date.isoformat(),
        to_date=today.isoformat(),
    )
