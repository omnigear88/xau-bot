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


def signal_changed(current_overall):
    state = load_state()

    previous = state.get("overall")

    if previous != current_overall:
        state["overall"] = current_overall
        save_state(state)
        return True

    return False