from indicators import add_indicators


def analyze_timeframe(df):
    if len(df) < 60:
        return None

    df = add_indicators(df)

    last = df.iloc[-1]

    if last[["ema_13", "ema_21", "sma_35", "ema_50"]].isna().any():
        return None

    bullish = (
        last["close"] > last["ema_13"]
        and last["ema_13"] > last["ema_21"]
        and last["ema_21"] > last["sma_35"]
        and last["sma_35"] > last["ema_50"]
    )

    bearish = (
        last["close"] < last["ema_13"]
        and last["ema_13"] < last["ema_21"]
        and last["ema_21"] < last["sma_35"]
        and last["sma_35"] < last["ema_50"]
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
        "ema_13": float(last["ema_13"]),
        "ema_21": float(last["ema_21"]),
        "sma_35": float(last["sma_35"]),
        "ema_50": float(last["ema_50"]),
        "atr_14": float(last["atr_14"]),
        "rsi_14": float(last["rsi_14"]),
        "macd": float(last["macd"]),
        "macd_signal": float(last["macd_signal"]),
        "macd_hist": float(last["macd_hist"]),
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
