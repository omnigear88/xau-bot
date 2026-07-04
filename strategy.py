from indicators import add_indicators


def analyze_timeframe(df):
    if len(df) < 60:
        return None

    df = add_indicators(df)

    last = df.iloc[-1]

    if last[["ema13", "ema21", "sma35", "ema50"]].isna().any():
        return None

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
        "ema13": float(last["ema13"]),
        "ema21": float(last["ema21"]),
        "sma35": float(last["sma35"]),
        "ema50": float(last["ema50"]),
        "signal": signal,
    }


def summarize(results):
    bullish_count = sum(1 for r in results.values() if r["signal"] == "Bullish")
    bearish_count = sum(1 for r in results.values() if r["signal"] == "Bearish")

    if bullish_count == len(results):
        overall = "ALL_BULLISH"
    elif bearish_count == len(results):
        overall = "ALL_BEARISH"
    else:
        overall = f"{bullish_count}/{len(results)} Bullish, {bearish_count}/{len(results)} Bearish"

    return overall
