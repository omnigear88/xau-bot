import time
from datetime import datetime, UTC
from trading_ig import IGService, IGStreamService
from lightstreamer.client import Subscription, SubscriptionListener

from config import IG_USERNAME, IG_PASSWORD, IG_API_KEY, IG_ENV, IG_GOLD_EPIC
from resampler import get_all_timeframes
from strategy import analyze_timeframe, summarize
from telegram_bot import send_telegram
from state import signal_changed
from database import init_db, save_candle


ACC_TYPE = "DEMO" if IG_ENV == "demo" else "LIVE"

SYMBOL = "XAUUSD"

current_1m_candle = None


def mid(bid, offer):
    if bid is not None and offer is not None:
        return (float(bid) + float(offer)) / 2
    if bid is not None:
        return float(bid)
    if offer is not None:
        return float(offer)
    return None


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
    candles_by_timeframe = get_all_timeframes()
    results = {}

    for timeframe, df in candles_by_timeframe.items():
        if len(df) < 60:
            print(
                f"{timeframe}: not enough candles after resample "
                f"({len(df)}/60)",
                flush=True,
            )
            return

        result = analyze_timeframe(df)
        if result is None:
            print(f"{timeframe}: indicators not ready", flush=True)
            return

        results[timeframe] = result

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

    save_candle(SYMBOL, "1m", current_1m_candle)

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
    init_db()

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
