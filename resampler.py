import pandas as pd
from database import load_history

SYMBOL = "XAUUSD"

TIMEFRAME_RULES = {
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1H": "1h",
    "4H": "4h",
    "1D": "1d",
}


def get_candles(timeframe, limit=300):
    if timeframe not in TIMEFRAME_RULES:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    # Need more 1m candles than final requested candles
    multiplier = {
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1H": 60,
        "4H": 240,
        "1D": 1440,
    }[timeframe]

    one_minute_limit = limit * multiplier + 200

    df = load_history(SYMBOL, "1m", limit=one_minute_limit)

    if df.empty:
        return df

    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.drop_duplicates(subset=["time"], keep="last")
    df = df.sort_values("time")
    df = df.set_index("time")

    rule = TIMEFRAME_RULES[timeframe]

    resampled = (
        df.resample(rule)
        .agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
        })
        .dropna()
        .reset_index()
    )

    return resampled.tail(limit).reset_index(drop=True)


def get_all_timeframes(limit=300):
    return {
        "15m": get_candles("15m", limit),
        "1H": get_candles("1H", limit),
        "4H": get_candles("4H", limit),
        "1D": get_candles("1D", limit),
    }


if __name__ == "__main__":
    for tf, df in get_all_timeframes(limit=100).items():
        print(f"\n{tf}")
        print("Rows:", len(df))
        if not df.empty:
            print("First:", df.iloc[0]["time"])
            print("Last:", df.iloc[-1]["time"])
            print(df.tail(3))