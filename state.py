import json
import os
from config import STATE_FILE


def load_state():
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

    if not os.path.exists(STATE_FILE):
        return {}

    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_previous_analysis_state():
    state = load_state()
    return state.get("analysis")


def save_analysis_state(current_state):
    state = load_state()
    state["analysis"] = _compact_analysis_state(current_state)
    save_state(state)


def signal_changed(current_overall):
    state = load_state()

    previous = state.get("overall")

    if previous != current_overall:
        state["overall"] = current_overall
        save_state(state)
        return True

    return False


def _compact_analysis_state(current_state):
    return {
        "overall_direction": current_state.get("overall_direction"),
        "timeframes": {
            timeframe: {
                "direction": result.get("direction"),
                "score": result.get("score"),
                "confidence": result.get("confidence"),
            }
            for timeframe, result in current_state.get("timeframes", {}).items()
        },
        "last_alert_time": current_state.get("last_alert_time"),
    }
