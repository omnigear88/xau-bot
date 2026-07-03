from config import IG_GOLD_EPIC
from ig_api import login, get_prices
from database import init_db, save_candle

SYMBOL = "XAUUSD"

TIMEFRAMES = {
    "15m": "MINUTE_15",
    "1H": "HOUR",
    "4H": "HOUR_4",
    "1D": "DAY",
}


def main():
    init_db()
    cst, token = login()

    for tf, resolution in TIMEFRAMES.items():
        print(f"Bootstrapping {tf}...")

        df = get_prices(
            cst=cst,
            token=token,
            epic=IG_GOLD_EPIC,
            resolution=resolution,
            max_bars=120,
        )

        for _, row in df.iterrows():
            candle = {
                "time": row["time"].to_pydatetime(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }

            save_candle(SYMBOL, tf, candle)

        print(f"Saved {len(df)} candles for {tf}")


if __name__ == "__main__":
    main()