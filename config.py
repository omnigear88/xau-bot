from dotenv import load_dotenv
import os

load_dotenv()

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
IG_API_KEY = os.getenv("IG_API_KEY")
IG_ENV = os.getenv("IG_ENV", "demo").lower()
IG_GOLD_EPIC = os.getenv("IG_GOLD_EPIC")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_XAU_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_XAU_CHAT_ID")

BASE_URL = (
    "https://demo-api.ig.com/gateway/deal"
    if IG_ENV == "demo"
    else "https://api.ig.com/gateway/deal"
)

TIMEFRAMES = {
    "15m": "MINUTE_15",
    "1H": "HOUR",
    "4H": "HOUR_4",
    "1D": "DAY",
}

STATE_FILE = "data/state.json"