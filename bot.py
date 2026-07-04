import argparse


def run_live():
    from market_data import main as run_market_data

    run_market_data()


def run_offline():
    from resampler import get_all_timeframes

    candles_by_timeframe = get_all_timeframes()

    if all(df.empty for df in candles_by_timeframe.values()):
        print(
            "SQLite database is empty: no stored 1m candles were found. "
            "Run the live bot long enough to save completed 1m candles first."
        )
        return

    for timeframe, df in candles_by_timeframe.items():
        print(f"\n{timeframe}")
        print(f"Rows: {len(df)}")

        if df.empty:
            print("First: n/a")
            print("Last: n/a")
            print("Last close: n/a")
            continue

        print(f"First: {df.iloc[0]['time']}")
        print(f"Last: {df.iloc[-1]['time']}")
        print(f"Last close: {df.iloc[-1]['close']}")


def parse_args():
    parser = argparse.ArgumentParser(description="XAUUSD streaming bot")
    parser.add_argument(
        "mode",
        nargs="?",
        default="live",
        choices=["live", "offline"],
        help="Run live IG streaming or inspect stored SQLite candle data.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.mode == "offline":
        run_offline()
        return

    run_live()

if __name__ == "__main__":
    main()
