import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
    }

    r = requests.post(url, json=payload, timeout=20)

    if r.status_code != 200:
        print("Telegram failed:", r.status_code, r.text)
    else:
        print("Telegram sent.")


def format_message(results, overall):
    lines = []

    if overall == "ALL_BULLISH":
        title = "🟢 XAUUSD ALL BULLISH"
    elif overall == "ALL_BEARISH":
        title = "🔴 XAUUSD ALL BEARISH"
    else:
        title = "⚪ XAUUSD Mixed"

    lines.append(title)
    lines.append("")
    lines.append(f"Overall: {overall}")
    lines.append("")

    for tf, r in results.items():
        if r["signal"] == "Bullish":
            icon = "✅"
        elif r["signal"] == "Bearish":
            icon = "❌"
        else:
            icon = "⚪"

        lines.append(f"{tf}: {icon} {r['signal']}")
        lines.append(f"Close: {round(r['close'], 2)}")
        lines.append(f"Time: {r['time']}")
        lines.append("")

    return "\n".join(lines)