from datetime import datetime, timedelta, timezone
import requests
import pandas as pd
from config import IG_USERNAME, IG_PASSWORD, IG_API_KEY, BASE_URL


def login():
    url = f"{BASE_URL}/session"

    headers = {
        "X-IG-API-KEY": IG_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2",
    }

    payload = {
        "identifier": IG_USERNAME,
        "password": IG_PASSWORD,
    }

    r = requests.post(url, headers=headers, json=payload, timeout=20)

    if r.status_code != 200:
        print(r.text)
        raise SystemExit("IG login failed")

    return r.headers["CST"], r.headers["X-SECURITY-TOKEN"]


def make_headers(cst, token, version="1"):
    return {
        "X-IG-API-KEY": IG_API_KEY,
        "CST": cst,
        "X-SECURITY-TOKEN": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": version,
    }

def get_price_value(price_obj):
    bid = price_obj.get("bid")
    ask = price_obj.get("ask")

    if bid is not None and ask is not None:
        return (bid + ask) / 2

    if bid is not None:
        return bid

    if ask is not None:
        return ask

    return None

def get_prices(cst, token, epic, resolution, max_bars=500):
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)

    if resolution == "MINUTE_15":
        start = now - timedelta(days=2)
    elif resolution == "HOUR":
        start = now - timedelta(days=7)
    elif resolution == "HOUR_4":
        start = now - timedelta(days=30)
    elif resolution == "DAY":
        start = now - timedelta(days=180)
    else:
        start = now - timedelta(days=30)

    url = f"{BASE_URL}/prices/{epic}"

    params = {
        "resolution": resolution,
        "from": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "to": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "pageSize": max_bars,
        "pageNumber": 1,
    }

    r = requests.get(
        url,
        headers=make_headers(cst, token, version="3"),
        params=params,
        timeout=20,
    )

    print("URL:", r.url)
    print("Status:", r.status_code)

    if r.status_code != 200:
        print(r.text)
        raise SystemExit(f"Price request failed for {resolution}")

    prices = r.json().get("prices", [])

    rows = []
    for p in prices:
        rows.append({
            "time": p.get("snapshotTimeUTC"),
            "open": get_price_value(p["openPrice"]),
            "high": get_price_value(p["highPrice"]),
            "low": get_price_value(p["lowPrice"]),
            "close": get_price_value(p["closePrice"]),
        })

    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"])
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df.sort_values("time").reset_index(drop=True)

    print(f"{resolution}: first={df.iloc[0]['time']} last={df.iloc[-1]['time']} rows={len(df)}")

    return df