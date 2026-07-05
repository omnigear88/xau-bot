REQUIRED_COLUMNS = {"time", "open", "high", "low", "close"}


class IndicatorEngine:
    def __init__(self):
        self.indicators = []

    def add_indicator(self, name, **params):
        self.indicators.append((name.lower(), params))
        return self

    def calculate(self, df):
        if df.empty:
            return df

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            missing_columns = ", ".join(sorted(missing))
            raise ValueError(f"DataFrame is missing required columns: {missing_columns}")

        result = df.copy()

        for name, params in self.indicators:
            if name == "ema":
                self._calculate_ema(result, params)
            elif name == "sma":
                self._calculate_sma(result, params)
            elif name == "atr":
                self._calculate_atr(result, params)
            elif name == "rsi":
                self._calculate_rsi(result, params)
            elif name == "macd":
                self._calculate_macd(result, params)
            else:
                raise ValueError(f"Unsupported indicator: {name}")

        return result

    def _calculate_ema(self, df, params):
        period = _get_period(params)
        df[f"ema_{period}"] = df["close"].ewm(span=period, adjust=False).mean()

    def _calculate_sma(self, df, params):
        period = _get_period(params)
        df[f"sma_{period}"] = df["close"].rolling(window=period).mean()

    def _calculate_atr(self, df, params):
        period = _get_period(params)
        previous_close = df["close"].shift(1)
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - previous_close).abs()
        low_close = (df["low"] - previous_close).abs()
        true_range = high_low.combine(high_close, max).combine(low_close, max)

        df[f"atr_{period}"] = true_range.rolling(window=period).mean()

    def _calculate_rsi(self, df, params):
        period = _get_period(params)
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        average_gain = gain.rolling(window=period).mean()
        average_loss = loss.rolling(window=period).mean()
        relative_strength = average_gain / average_loss

        df[f"rsi_{period}"] = 100 - (100 / (1 + relative_strength))

    def _calculate_macd(self, df, params):
        fast = int(params.get("fast", 12))
        slow = int(params.get("slow", 26))
        signal = int(params.get("signal", 9))

        fast_ema = df["close"].ewm(span=fast, adjust=False).mean()
        slow_ema = df["close"].ewm(span=slow, adjust=False).mean()

        df["macd"] = fast_ema - slow_ema
        df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]


def _get_period(params):
    if "period" not in params:
        raise ValueError("Indicator period is required.")

    return int(params["period"])


def default_engine():
    return (
        IndicatorEngine()
        .add_indicator("ema", period=13)
        .add_indicator("ema", period=21)
        .add_indicator("ema", period=50)
        .add_indicator("sma", period=35)
        .add_indicator("atr", period=14)
        .add_indicator("rsi", period=14)
        .add_indicator("macd", fast=12, slow=26, signal=9)
    )


def add_indicators(df):
    return default_engine().calculate(df)
