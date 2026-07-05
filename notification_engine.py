IMPORTANT_TIMEFRAMES = {"4H", "1D"}
SCORE_CHANGE_THRESHOLD = 20


def should_notify(previous_state, current_state):
    if not previous_state:
        return True

    if previous_state.get("overall_direction") != current_state.get("overall_direction"):
        return True

    previous_timeframes = previous_state.get("timeframes", {})
    current_timeframes = current_state.get("timeframes", {})

    for timeframe, current in current_timeframes.items():
        previous = previous_timeframes.get(timeframe)
        if previous is None:
            return True

        previous_direction = previous.get("direction")
        current_direction = current.get("direction")
        if previous_direction != current_direction:
            return True

        if timeframe in IMPORTANT_TIMEFRAMES and previous_direction != current_direction:
            return True

        previous_score = previous.get("score")
        current_score = current.get("score")
        if _score_changed(previous_score, current_score):
            return True

        if _became_high_confidence(previous.get("confidence"), current.get("confidence")):
            return True

    return False


def _score_changed(previous_score, current_score):
    if previous_score is None or current_score is None:
        return previous_score != current_score

    return abs(current_score - previous_score) >= SCORE_CHANGE_THRESHOLD


def _became_high_confidence(previous_confidence, current_confidence):
    return previous_confidence in {"Low", "Medium"} and current_confidence == "High"
