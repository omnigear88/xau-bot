from resampler import get_all_timeframes
from strategy import score_all_timeframes


def main():
    timeframes = get_all_timeframes()
    scores = score_all_timeframes(timeframes)

    for timeframe, result in scores.items():
        print(f"\n{timeframe}")
        print(f"Direction: {result['direction']}")
        print(f"Score: {result['score']}")
        print(f"Confidence: {result['confidence']}")
        print("Reasons:")
        for reason in result["reasons"]:
            print(f"- {reason}")


if __name__ == "__main__":
    main()
