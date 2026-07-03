import time
import pandas as pd
from datetime import datetime, UTC
from trading_ig import IGService, IGStreamService
from lightstreamer.client import Subscription, SubscriptionListener

from config import IG_USERNAME, IG_PASSWORD, IG_API_KEY, IG_ENV, IG_GOLD_EPIC
from indicators import add_indicators
from telegram_bot import send_telegram
from state import signal_changed
from database import init_db, save_candle, load_history


ACC_TYPE = "DEMO" if IG_ENV == "demo" else "LIVE"

SYMBOL = "XAUUSD"

one_minute_rows = []
current_1m_candle = None


def mid(bid, offer):
    if bid is not None and offer is not None:
        return (float(bid) + float(offer)) / 2
    if bid is not None:
        return float(bid)
    if offer is not None:
        return float(offer)
    return None


def analyze_df(df):
    df = df.copy()

    if len(df) < 60:
        return None

    df = add_indicators(df)
    last = df.iloc[-1]

    bullish = (
        last["close"] > last["ema13"]
        and last["ema13"] > last["ema21"]
        and last["ema21"] > last["sma35"]
        and last["sma35"] > last["ema50"]
    )

    bearish = (
        last["close"] < last["ema13"]
        and last["ema13"] < last["ema21"]
        and last["ema21"] < last["sma35"]
        and last["sma35"] < last["ema50"]
    )

    if bullish:
        signal = "Bullish"
    elif bearish:
        signal = "Bearish"
    else:
        signal = "Neutral"

    return {
        "time": str(last["time"]),
        "close": float(last["close"]),
        "signal": signal,
    }


def resample_from_1m():
    if len(one_minute_rows) < 300:
        print(f"Collecting 1m candles... {len(one_minute_rows)}/300")
        return None

    df = pd.DataFrame(one_minute_rows)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.drop_duplicates(subset=["time"], keep="last")
    df = df.sort_values("time")
    df = df.set_index("time")

    rules = {
        "15m": "15min",
        "1H": "1h",
        "4H": "4h",
        "1D": "1d",
    }

    results = {}

    for label, rule in rules.items():
        tf = (
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

        result = analyze_df(tf)

        if result is None:
            print(f"{label}: not enough candles after resample")
            return None

        results[label] = result

    return results


def summarize(results):
    bullish = sum(1 for r in results.values() if r["signal"] == "Bullish")
    bearish = sum(1 for r in results.values() if r["signal"] == "Bearish")

    if bullish == 4:
        return "ALL_BULLISH"

    if bearish == 4:
        return "ALL_BEARISH"

    return f"{bullish}/4 Bullish, {bearish}/4 Bearish"


def format_message(results, overall):
    if overall == "ALL_BULLISH":
        title = "🟢 XAUUSD ALL BULLISH"
    elif overall == "ALL_BEARISH":
        title = "🔴 XAUUSD ALL BEARISH"
    else:
        title = "⚪ XAUUSD Mixed"

    lines = [title, "", f"Overall: {overall}", ""]

    for tf, r in results.items():
        icon = "⚪"
        if r["signal"] == "Bullish":
            icon = "✅"
        elif r["signal"] == "Bearish":
            icon = "❌"

        lines.append(f"{tf}: {icon} {r['signal']}")
        lines.append(f"Close: {round(r['close'], 2)}")
        lines.append(f"Time: {r['time']}")
        lines.append("")

    return "\n".join(lines)


def evaluate_all():
    results = resample_from_1m()

    if not results:
        return

    overall = summarize(results)
    print("Overall:", overall)

    if signal_changed(overall):
        print("Signal changed. Sending Telegram.")
        send_telegram(format_message(results, overall))
    else:
        print("No signal change.")


def finalize_previous_candle():
    global current_1m_candle

    if current_1m_candle is None:
        return

    one_minute_rows.append(current_1m_candle)
    save_candle(SYMBOL, "1m", current_1m_candle)

    if len(one_minute_rows) > 5000:
        del one_minute_rows[:-5000]

    dt = current_1m_candle["time"]
    close = current_1m_candle["close"]

    print(f"Saved completed 1m candle: {dt} close={round(close, 2)}", flush=True)

    if dt.minute % 15 == 14:
        print("15m boundary reached. Evaluating...")
        evaluate_all()


class ChartListener(SubscriptionListener):
    def onItemUpdate(self, update):
        global current_1m_candle

        values = update.getChangedFields()

        utm = values.get("UTM")
        if not utm:
            return

        o = mid(values.get("BID_OPEN"), values.get("OFR_OPEN"))
        h = mid(values.get("BID_HIGH"), values.get("OFR_HIGH"))
        l = mid(values.get("BID_LOW"), values.get("OFR_LOW"))
        c = mid(values.get("BID_CLOSE"), values.get("OFR_CLOSE"))

        if None in [o, h, l, c]:
            return

        dt = datetime.fromtimestamp(int(utm) / 1000, UTC)

        incoming_candle = {
            "time": dt,
            "open": o,
            "high": h,
            "low": l,
            "close": c,
        }

        if current_1m_candle is None:
            current_1m_candle = incoming_candle
            print(f"Started 1m candle: {dt} close={round(c, 2)}", flush=True)
            return

        if incoming_candle["time"] == current_1m_candle["time"]:
            current_1m_candle = incoming_candle
            return

        finalize_previous_candle()
        current_1m_candle = incoming_candle
        print(f"Started 1m candle: {dt} close={round(c, 2)}", flush=True)


def main():
    global one_minute_rows

    init_db()

    df = load_history(SYMBOL, "1m", limit=5000)
    if not df.empty:
        one_minute_rows = df.to_dict("records")
        print(f"Loaded {len(one_minute_rows)} saved 1m candles.")

    ig_service = IGService(
        username=IG_USERNAME,
        password=IG_PASSWORD,
        api_key=IG_API_KEY,
        acc_type=ACC_TYPE,
    )

    ig_service.create_session()
    print("IG REST session created.")

    stream_service = IGStreamService(ig_service)
    stream_service.create_session()
    print("IG streaming session created.")

    item = f"CHART:{IG_GOLD_EPIC}:1MINUTE"

    sub = Subscription(
        mode="MERGE",
        items=[item],
        fields=[
            "UTM",
            "OFR_OPEN",
            "OFR_HIGH",
            "OFR_LOW",
            "OFR_CLOSE",
            "BID_OPEN",
            "BID_HIGH",
            "BID_LOW",
            "BID_CLOSE",
        ],
    )

    sub.addListener(ChartListener())
    stream_service.subscribe(sub)

    print("Subscribed to:", item)
    print("Streaming 1-minute IG chart candles...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        finalize_previous_candle()
        stream_service.unsubscribe(sub)
        stream_service.disconnect()


if __name__ == "__main__":
    main()