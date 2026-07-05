from indicators import add_indicators


def score_timeframe(df):
    if df.empty or len(df) < 50:
        return {
            "direction": "Insufficient Data",
            "score": 0,
            "confidence": "Low",
            "reasons": ["Need at least 50 candles"],
        }

    df = add_indicators(df)
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    bullish_score = 0
    bearish_score = 0
    bullish_reasons = []
    bearish_reasons = []
    neutral_reasons = []

    bullish_score, bearish_score = _score_comparison(
        latest,
        "close",
        "ema_13",
        10,
        "Close above EMA13",
        "Close below EMA13",
        bullish_score,
        bearish_score,
        bullish_reasons,
        bearish_reasons,
        neutral_reasons,
    )
    bullish_score, bearish_score = _score_comparison(
        latest,
        "ema_13",
        "ema_21",
        15,
        "EMA13 above EMA21",
        "EMA13 below EMA21",
        bullish_score,
        bearish_score,
        bullish_reasons,
        bearish_reasons,
        neutral_reasons,
    )
    bullish_score, bearish_score = _score_comparison(
        latest,
        "ema_21",
        "ema_50",
        15,
        "EMA21 above EMA50",
        "EMA21 below EMA50",
        bullish_score,
        bearish_score,
        bullish_reasons,
        bearish_reasons,
        neutral_reasons,
    )
    bullish_score, bearish_score = _score_comparison(
        latest,
        "close",
        "sma_35",
        10,
        "Close above SMA35",
        "Close below SMA35",
        bullish_score,
        bearish_score,
        bullish_reasons,
        bearish_reasons,
        neutral_reasons,
    )

    if _has_value(latest, "ema_13") and _has_value(df.iloc[-3], "ema_13"):
        if latest["ema_13"] > df.iloc[-3]["ema_13"]:
            bullish_score += 10
            bullish_reasons.append("EMA13 rising over last 3 candles")
        elif latest["ema_13"] < df.iloc[-3]["ema_13"]:
            bearish_score += 10
            bearish_reasons.append("EMA13 falling over last 3 candles")
        else:
            neutral_reasons.append("EMA13 flat over last 3 candles")
    else:
        neutral_reasons.append("EMA13 trend unavailable")

    if _has_value(latest, "rsi_14"):
        if latest["rsi_14"] > 55:
            bullish_score += 10
            bullish_reasons.append("RSI14 above 55")
        elif latest["rsi_14"] < 45:
            bearish_score += 10
            bearish_reasons.append("RSI14 below 45")
        else:
            neutral_reasons.append("RSI14 neutral")
    else:
        neutral_reasons.append("RSI14 unavailable")

    if _has_value(latest, "macd_hist"):
        if latest["macd_hist"] > 0:
            bullish_score += 10
            bullish_reasons.append("MACD histogram positive")
        elif latest["macd_hist"] < 0:
            bearish_score += 10
            bearish_reasons.append("MACD histogram negative")
        else:
            neutral_reasons.append("MACD histogram neutral")
    else:
        neutral_reasons.append("MACD histogram unavailable")

    if _has_value(latest, "close") and _has_value(previous, "close"):
        if latest["close"] > previous["close"]:
            bullish_score += 10
            bullish_reasons.append("Close above previous close")
        elif latest["close"] < previous["close"]:
            bearish_score += 10
            bearish_reasons.append("Close below previous close")
        else:
            neutral_reasons.append("Close unchanged from previous close")
    else:
        neutral_reasons.append("Previous close unavailable")

    if _has_value(latest, "atr_14"):
        bullish_score += 10
        bearish_score += 10
        bullish_reasons.append("ATR14 available")
        bearish_reasons.append("ATR14 available")
    else:
        neutral_reasons.append("ATR14 unavailable")

    direction, score, reasons = _resolve_direction(
        bullish_score,
        bearish_score,
        bullish_reasons,
        bearish_reasons,
        neutral_reasons,
    )

    return {
        "direction": direction,
        "score": int(score),
        "confidence": _confidence(score),
        "reasons": reasons,
    }


def score_all_timeframes(timeframes):
    return {
        timeframe: score_timeframe(df)
        for timeframe, df in timeframes.items()
    }


def analyze_timeframe(df):
    if df.empty or len(df) < 50:
        return None

    scored = score_timeframe(df)
    if scored["direction"] == "Insufficient Data":
        return None

    df = add_indicators(df)
    latest = df.iloc[-1]

    return {
        "time": str(latest["time"]),
        "close": float(latest["close"]),
        "ema_13": _float_or_none(latest["ema_13"]),
        "ema_21": _float_or_none(latest["ema_21"]),
        "sma_35": _float_or_none(latest["sma_35"]),
        "ema_50": _float_or_none(latest["ema_50"]),
        "atr_14": _float_or_none(latest["atr_14"]),
        "rsi_14": _float_or_none(latest["rsi_14"]),
        "macd": _float_or_none(latest["macd"]),
        "macd_signal": _float_or_none(latest["macd_signal"]),
        "macd_hist": _float_or_none(latest["macd_hist"]),
        "signal": scored["direction"],
        "direction": scored["direction"],
        "score": scored["score"],
        "confidence": scored["confidence"],
        "reasons": scored["reasons"],
    }


def summarize(results):
    bullish_count = sum(1 for r in results.values() if r["direction"] == "Bullish")
    bearish_count = sum(1 for r in results.values() if r["direction"] == "Bearish")

    if bullish_count == len(results):
        return "ALL_BULLISH"

    if bearish_count == len(results):
        return "ALL_BEARISH"

    return f"{bullish_count}/{len(results)} Bullish, {bearish_count}/{len(results)} Bearish"


def _score_comparison(
    row,
    left,
    right,
    points,
    bullish_reason,
    bearish_reason,
    bullish_score,
    bearish_score,
    bullish_reasons,
    bearish_reasons,
    neutral_reasons,
):
    if not _has_value(row, left) or not _has_value(row, right):
        neutral_reasons.append(f"{left} vs {right} unavailable")
        return bullish_score, bearish_score

    if row[left] > row[right]:
        bullish_score += points
        bullish_reasons.append(bullish_reason)
    elif row[left] < row[right]:
        bearish_score += points
        bearish_reasons.append(bearish_reason)
    else:
        neutral_reasons.append(f"{left} equals {right}")

    return bullish_score, bearish_score


def _resolve_direction(
    bullish_score,
    bearish_score,
    bullish_reasons,
    bearish_reasons,
    neutral_reasons,
):
    if bullish_score - bearish_score >= 20:
        return "Bullish", bullish_score, bullish_reasons + neutral_reasons

    if bearish_score - bullish_score >= 20:
        return "Bearish", bearish_score, bearish_reasons + neutral_reasons

    reasons = ["Bullish and bearish scores are close"]
    reasons.extend(bullish_reasons)
    reasons.extend(bearish_reasons)
    reasons.extend(neutral_reasons)

    return "Neutral", max(bullish_score, bearish_score), reasons


def _confidence(score):
    if score >= 75:
        return "High"

    if score >= 50:
        return "Medium"

    return "Low"


def _has_value(row, column):
    if column not in row:
        return False

    value = row[column]
    return value == value


def _float_or_none(value):
    if value != value:
        return None

    return float(value)
