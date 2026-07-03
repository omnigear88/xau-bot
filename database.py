import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/market_data.db")


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candles (
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                time TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                PRIMARY KEY (symbol, timeframe, time)
            )
        """)


def save_candle(symbol, timeframe, candle):
    with connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO candles
            (symbol, timeframe, time, open, high, low, close)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            timeframe,
            candle["time"].isoformat(),
            candle["open"],
            candle["high"],
            candle["low"],
            candle["close"],
        ))


def load_history(symbol, timeframe, limit=300):
    with connect() as conn:
        df = pd.read_sql_query("""
            SELECT time, open, high, low, close
            FROM candles
            WHERE symbol = ? AND timeframe = ?
            ORDER BY time DESC
            LIMIT ?
        """, conn, params=(symbol, timeframe, limit))

    if df.empty:
        return df

    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time").reset_index(drop=True)
    return df