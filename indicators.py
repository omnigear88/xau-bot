def add_indicators(df):
    df = df.copy()

    df["ema13"] = df["close"].ewm(span=13, adjust=False).mean()
    df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
    df["sma35"] = df["close"].rolling(window=35).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

    return df