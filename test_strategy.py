from indicators import add_indicators
from resampler import get_all_timeframes
from strategy import score_all_timeframes


def main():
    timeframes = get_all_timeframes()
    timeframes = {
        timeframe: add_indicators(df) if not df.empty else df
        for timeframe, df in timeframes.items()
    }
    scores = score_all_timeframes(timeframes)

    for timeframe, result in scores.items():
        print(f"\n{timeframe}")
        print(f"Direction: {result['direction']}")
        print(f"Score: {result['score']}")
        print(f"Confidence: {result['confidence']}")
        print(f"ATR14: {_format_optional_number(result['atr_14'])}")
        print(f"Volatility: {result['volatility_note']}")
        print("Reasons:")
        for reason in result["reasons"]:
            print(f"- {reason}")


def _format_optional_number(value):
    if value is None:
        return "n/a"

    return f"{value:.4f}"


if __name__ == "__main__":
    main()
