from notification_engine import should_notify


def make_state(
    overall_direction="Bullish",
    direction_15m="Bullish",
    score_15m=80,
    confidence_15m="High",
    direction_4h="Bullish",
    last_alert_time="2026-07-05T00:00:00+00:00",
):
    return {
        "overall_direction": overall_direction,
        "timeframes": {
            "15m": {
                "direction": direction_15m,
                "score": score_15m,
                "confidence": confidence_15m,
            },
            "1H": {
                "direction": "Bullish",
                "score": 82,
                "confidence": "High",
            },
            "4H": {
                "direction": direction_4h,
                "score": 75,
                "confidence": "High",
            },
            "1D": {
                "direction": "Neutral",
                "score": 45,
                "confidence": "Low",
            },
        },
        "last_alert_time": last_alert_time,
    }


def run_case(name, previous_state, current_state, expected):
    actual = should_notify(previous_state, current_state)
    status = "PASS" if actual == expected else "FAIL"
    print(f"{status}: {name} expected={expected} actual={actual}")
    if actual != expected:
        raise AssertionError(name)


def main():
    base = make_state()

    run_case("first state should notify", None, base, True)
    run_case("same state should not notify", base, make_state(), False)
    run_case(
        "score change >= 20 should notify",
        base,
        make_state(score_15m=100),
        True,
    )
    run_case(
        "4H direction change should notify",
        base,
        make_state(direction_4h="Bearish"),
        True,
    )
    run_case(
        "confidence change to High should notify",
        make_state(score_15m=80, confidence_15m="Medium"),
        make_state(score_15m=80, confidence_15m="High"),
        True,
    )
    run_case(
        "only timestamp change should not notify",
        base,
        make_state(last_alert_time="2026-07-05T01:00:00+00:00"),
        False,
    )


if __name__ == "__main__":
    main()
