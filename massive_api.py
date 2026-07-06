import os
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

import requests
from dotenv import load_dotenv


BASE_URL = "https://api.massive.com"
DEFAULT_SYMBOL = "C:XAUUSD"
BOOTSTRAP_CHUNK_DAYS = 25


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


def bootstrap_1m_history(symbol=DEFAULT_SYMBOL, days=5, chunk_days=BOOTSTRAP_CHUNK_DAYS):
    end_date = datetime.now(UTC).date()
    start_date = end_date - timedelta(days=days)
    current_start = start_date
    candles_by_time = {}

    while current_start <= end_date:
        current_end = min(
            current_start + timedelta(days=chunk_days - 1),
            end_date,
        )

        print(
            f"Fetching Massive chunk {current_start.isoformat()} "
            f"to {current_end.isoformat()}...",
            flush=True,
        )

        chunk = _fetch_bootstrap_chunk(
            symbol=symbol,
            multiplier=1,
            timespan="minute",
            from_date=current_start.isoformat(),
            to_date=current_end.isoformat(),
        )

        for candle in chunk:
            candles_by_time[candle["time"]] = candle

        print(
            f"Chunk candles fetched: {len(chunk)} | "
            f"Total candles collected: {len(candles_by_time)}",
            flush=True,
        )

        current_start = current_end + timedelta(days=1)

    return [
        candles_by_time[time]
        for time in sorted(candles_by_time)
    ]


def _fetch_bootstrap_chunk(symbol, multiplier, timespan, from_date, to_date):
    return fetch_forex_aggregates(
        symbol=symbol,
        multiplier=multiplier,
        timespan=timespan,
        from_date=from_date,
        to_date=to_date,
    )
