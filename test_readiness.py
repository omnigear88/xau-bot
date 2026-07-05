import pandas as pd

from indicators import add_indicators
from readiness import check_platform_ready, check_timeframe_ready


def make_candles(rows):
    return pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=rows, freq="15min", tz="UTC"),
        "open": [float(i) for i in range(rows)],
        "high": [float(i) + 1 for i in range(rows)],
        "low": [float(i) - 1 for i in range(rows)],
        "close": [float(i) + 0.5 for i in range(rows)],
    })


def run_case(name, actual, expected):
    status = "PASS" if actual == expected else "FAIL"
    print(f"{status}: {name} expected={expected} actual={actual}")
    if actual != expected:
        raise AssertionError(name)


def main():
    empty = pd.DataFrame()
    run_case("empty timeframe data -> not ready", check_timeframe_ready("15m", empty)["ready"], False)

    insufficient = add_indicators(make_candles(20))
    run_case(
        "insufficient rows -> not ready",
        check_timeframe_ready("15m", insufficient)["ready"],
        False,
    )

    sufficient = add_indicators(make_candles(60))
    run_case(
        "sufficient rows with indicators -> ready",
        check_timeframe_ready("15m", sufficient)["ready"],
        True,
    )

    missing_atr = sufficient.drop(columns=["atr_14"])
    run_case(
        "missing ATR -> not ready",
        check_timeframe_ready("15m", missing_atr)["ready"],
        False,
    )

    platform = check_platform_ready({
        "15m": sufficient,
        "1H": sufficient,
        "4H": sufficient,
        "1D": sufficient,
    })
    run_case("all required timeframes ready", platform["ready"], True)


if __name__ == "__main__":
    main()
