from indicators import add_indicators
from resampler import get_candles


INDICATOR_COLUMNS = [
    "time",
    "close",
    "ema_13",
    "ema_21",
    "ema_50",
    "sma_35",
    "atr_14",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_hist",
]


def main():
    df = get_candles("15m", limit=300)

    if df.empty:
        print("No 15m candles available. Run `python bot.py bootstrap` first.")
        return

    df = add_indicators(df)
    print(df[INDICATOR_COLUMNS].tail(5))


if __name__ == "__main__":
    main()
