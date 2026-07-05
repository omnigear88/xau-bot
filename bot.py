import argparse
import time
from datetime import UTC, datetime, timedelta


DB_SYMBOL = "XAUUSD"
MASSIVE_SYMBOL = "C:XAUUSD"
POLL_SECONDS = 60


def run_live():
    from massive_api import fetch_forex_aggregates
    from database import init_db, save_candle

    init_db()
    last_saved_time = get_last_saved_1m_time()
    last_evaluated_boundary = None

    print("Starting Massive REST polling for XAUUSD 1-minute candles.")

    while True:
        try:
            candles = fetch_latest_1m_candles(fetch_forex_aggregates)
            completed_candles = filter_completed_candles(candles)
            new_candles = [
                candle for candle in completed_candles
                if last_saved_time is None or candle["time"] > last_saved_time
            ]

            if not new_candles:
                print("No new completed 1m candles.")
            else:
                for candle in new_candles:
                    save_candle(DB_SYMBOL, "1m", candle)
                    last_saved_time = candle["time"]
                    print(
                        "Saved Massive 1m candle: "
                        f"{candle['time']} close={round(candle['close'], 2)}"
                    )

                    if is_completed_15m_boundary(candle):
                        boundary = candle["time"]
                        if boundary != last_evaluated_boundary:
                            print("15m boundary reached. Evaluating...")
                            evaluate_strategy()
                            last_evaluated_boundary = boundary

        except KeyboardInterrupt:
            print("Stopping Massive polling.")
            return
        except Exception as exc:
            print(f"Massive live polling error: {exc}")

        time.sleep(POLL_SECONDS)


def run_bootstrap(days):
    from database import init_db, save_candle
    from massive_api import bootstrap_1m_history

    init_db()
    print(f"Fetching {days} days of Massive 1-minute XAUUSD candles...")
    candles = bootstrap_1m_history(symbol=MASSIVE_SYMBOL, days=days)

    if not candles:
        print(
            "Massive returned no candles. Check MASSIVE_API_KEY, ticker "
            "format, date range, and account access."
        )
        return

    for candle in candles:
        save_candle(DB_SYMBOL, "1m", candle)

    print(f"Saved {len(candles)} Massive 1m candles to SQLite.")
    print(f"First: {candles[0]['time']}")
    print(f"Last: {candles[-1]['time']}")


def run_offline():
    from database import init_db, load_history
    from resampler import get_all_timeframes
    from strategy import score_timeframe

    init_db()
    one_minute = load_history(DB_SYMBOL, "1m", limit=1)
    if one_minute.empty:
        print(
            "SQLite database is empty: no stored 1m candles were found. "
            "Run `python bot.py bootstrap` first."
        )
        return

    candles_by_timeframe = get_all_timeframes()

    if all(df.empty for df in candles_by_timeframe.values()):
        print(
            "SQLite has 1m candles, but there is not enough history to build "
            "higher timeframes yet."
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

        score = score_timeframe(df)
        last = df.iloc[-1]

        print(f"First: {df.iloc[0]['time']}")
        print(f"Last: {last['time']}")
        print(f"Last close: {last['close']}")
        print(f"Direction: {score['direction']}")
        print(f"Score: {score['score']}")
        print(f"Confidence: {score['confidence']}")
        print("Reasons:")
        for reason in score["reasons"]:
            print(f"- {reason}")


def fetch_latest_1m_candles(fetch_forex_aggregates):
    now = datetime.now(UTC)
    from_date = (now - timedelta(days=2)).date().isoformat()
    to_date = now.date().isoformat()

    return fetch_forex_aggregates(
        symbol=MASSIVE_SYMBOL,
        multiplier=1,
        timespan="minute",
        from_date=from_date,
        to_date=to_date,
    )


def filter_completed_candles(candles):
    current_minute = datetime.now(UTC).replace(second=0, microsecond=0)
    return [candle for candle in candles if candle["time"] < current_minute]


def get_last_saved_1m_time():
    from database import load_history

    df = load_history(DB_SYMBOL, "1m", limit=1)
    if df.empty:
        return None

    return df.iloc[-1]["time"].to_pydatetime()


def is_completed_15m_boundary(candle):
    return candle["time"].minute % 15 == 14


def evaluate_strategy():
    from resampler import get_all_timeframes
    from state import signal_changed
    from strategy import analyze_timeframe, summarize
    from telegram_bot import send_telegram

    candles_by_timeframe = get_all_timeframes()
    results = {}

    for timeframe, df in candles_by_timeframe.items():
        if len(df) < 60:
            print(f"{timeframe}: not enough candles after resample ({len(df)}/60)")
            return

        result = analyze_timeframe(df)
        if result is None:
            print(f"{timeframe}: indicators not ready")
            return

        results[timeframe] = result

    overall = summarize(results)
    print("Overall:", overall)

    if signal_changed(overall):
        print("Signal changed. Sending Telegram.")
        send_telegram(format_strategy_message(results, overall))
    else:
        print("No signal change.")


def format_strategy_message(results, overall):
    if overall == "ALL_BULLISH":
        title = "XAUUSD ALL BULLISH"
    elif overall == "ALL_BEARISH":
        title = "XAUUSD ALL BEARISH"
    else:
        title = "XAUUSD Mixed"

    lines = [title, "", f"Overall: {overall}", ""]

    for timeframe, result in results.items():
        lines.append(
            f"{timeframe}: {result['direction']} "
            f"({result['score']}, {result['confidence']})"
        )
        lines.append(f"Close: {round(result['close'], 2)}")
        lines.append(f"Time: {result['time']}")
        lines.append("Reasons:")
        for reason in result["reasons"]:
            lines.append(f"- {reason}")
        lines.append("")

    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="XAUUSD streaming bot")
    parser.add_argument(
        "mode",
        nargs="?",
        default="live",
        choices=["live", "offline", "bootstrap"],
        help="Run Massive polling, inspect SQLite data, or bootstrap history.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="Days of 1-minute Massive history to fetch in bootstrap mode.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.mode == "offline":
        run_offline()
        return

    if args.mode == "bootstrap":
        run_bootstrap(args.days)
        return

    run_live()


if __name__ == "__main__":
    main()
