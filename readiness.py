REQUIRED_TIMEFRAMES = ("15m", "1H", "4H", "1D")
MIN_CANDLES = {
    "15m": 50,
    "1H": 50,
    "4H": 50,
    "1D": 50,
}
REQUIRED_INDICATORS = (
    "ema_13",
    "ema_21",
    "ema_50",
    "sma_35",
    "rsi_14",
    "macd_hist",
)


def check_timeframe_ready(tf, df):
    if df is None or df.empty:
        return {"ready": False, "reason": "No candles available"}

    required_rows = MIN_CANDLES.get(tf, 50)
    if len(df) < required_rows:
        return {
            "ready": False,
            "reason": f"Need at least {required_rows} candles, found {len(df)}",
        }

    latest = df.iloc[-1]

    for indicator in REQUIRED_INDICATORS:
        if not _has_value(latest, indicator):
            return {"ready": False, "reason": f"{indicator} unavailable"}

    if not _has_value(latest, "atr_14"):
        return {"ready": False, "reason": "atr_14 unavailable"}

    return {"ready": True, "reason": "Ready"}


def check_platform_ready(timeframes):
    timeframe_status = {
        timeframe: check_timeframe_ready(timeframe, timeframes.get(timeframe))
        for timeframe in REQUIRED_TIMEFRAMES
    }

    return {
        "ready": all(status["ready"] for status in timeframe_status.values()),
        "timeframes": timeframe_status,
    }


def _has_value(row, column):
    if column not in row:
        return False

    value = row[column]
    return value == value
