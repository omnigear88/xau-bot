# XAU Bot

A Python-based XAUUSD market data and alert system.

## Purpose

This project collects XAUUSD 1-minute candles from the Massive Forex REST API,
stores them in SQLite, builds higher timeframes locally, and sends Telegram
alerts based on trading logic.

## Current Architecture

Massive Forex REST API
-> 1-minute candles
-> SQLite database
-> Resampler
-> Indicators
-> Strategy
-> Telegram

## Main Files

- `bot.py` - application entry point and mode orchestration
- `massive_api.py` - Massive REST API access and candle parsing
- `database.py` - SQLite storage and retrieval
- `resampler.py` - builds 15m, 1H, 4H, 1D candles from 1m data
- `indicators.py` - technical indicators
- `strategy.py` - trading logic
- `telegram_bot.py` - Telegram messages
- `state.py` - prevents duplicate alerts
- `market_data.py` - legacy IG streaming code, not used by `bot.py`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with:

```bash
MASSIVE_API_KEY=your_massive_api_key
TELEGRAM_XAU_TOKEN=your_telegram_bot_token
TELEGRAM_XAU_CHAT_ID=your_telegram_chat_id
```

## Commands

Bootstrap recent 1-minute XAUUSD candles from Massive into SQLite:

```bash
python bot.py bootstrap
```

Run live Massive REST polling. This fetches recent completed 1-minute candles
every 60 seconds, saves new candles to SQLite, and evaluates the strategy after
completed 15-minute boundaries:

```bash
python bot.py live
```

Inspect local SQLite data without connecting to Massive or IG:

```bash
python bot.py offline
```

Offline mode prints each timeframe's row count, first and last candle times,
last close, direction, score, confidence, and score reasons.

If no mode is provided, the bot defaults to live mode:

```bash
python bot.py
```

## Data Source

The default Massive Forex ticker for XAUUSD is:

```text
C:XAUUSD
```

Candles are saved locally as:

```text
symbol = XAUUSD
timeframe = 1m
```

## v0.5 Indicator Engine

`indicators.py` contains a reusable `IndicatorEngine` for adding indicators to
OHLC DataFrames.

Supported indicators:

- EMA with configurable period, for example `ema_13`
- SMA with configurable period, for example `sma_35`
- ATR with configurable period, for example `atr_14`
- RSI with configurable period, for example `rsi_14`
- MACD with configurable fast, slow, and signal periods: `macd`,
  `macd_signal`, `macd_hist`

The compatibility helper `add_indicators(df)` still works and applies the
default engine:

- EMA 13
- EMA 21
- EMA 50
- SMA 35
- ATR 14
- RSI 14
- MACD 12/26/9

To test the indicator engine against local 15m candles:

```bash
python test_indicators.py
```

## v0.6 Trend Score Engine

`strategy.py` converts indicator-enriched OHLC DataFrames into a normalized
0-100 trend score for each timeframe.

The main scoring functions are:

- `score_timeframe(df)` - scores one OHLC DataFrame
- `score_all_timeframes(timeframes)` - scores a dictionary of timeframe
  DataFrames

Each score result contains:

- `direction` - `Bullish`, `Bearish`, `Neutral`, or `Insufficient Data`
- `score` - integer from 0 to 100, calculated as `round(raw_score / 80 * 100)`
- `confidence` - `Low`, `Medium`, or `High`
- `atr_14` - latest ATR value, or `None` when unavailable
- `volatility_note` - `ATR available` or `ATR unavailable`
- `reasons` - human-readable scoring reasons

The score compares bullish and bearish evidence from EMA alignment, SMA
position, EMA13 slope, RSI14, MACD histogram, and previous close. ATR is
reported as volatility information only; it does not add bullish or bearish
points.

Bullish raw max score is 80:

- close > ema_13: +10
- ema_13 > ema_21: +15
- ema_21 > ema_50: +15
- close > sma_35: +10
- ema_13 rising over last 3 candles: +10
- rsi_14 > 55: +10
- macd_hist > 0: +10
- close > previous close: +10

Bearish raw max score is 80 using the mirrored conditions. The returned score
normalizes that raw score to 0-100.

To test the trend score engine against all local timeframes:

```bash
python test_strategy.py
```

`test_strategy.py` loads resampled candles, adds indicators with
`add_indicators(df)`, then scores each timeframe.

## v0.7 Notification Engine

`notification_engine.py` separates analysis frequency from notification
frequency. The bot can analyze every completed 15m boundary, but Telegram is
sent only when the compact analysis state changes enough to matter.

Notify when:

- There is no previous analysis state
- Overall direction changes
- Any timeframe direction changes
- Any timeframe score changes by 20 or more points
- Confidence changes from `Low` or `Medium` to `High`
- The `4H` or `1D` direction changes

Do not notify when only timestamps change, or when score/confidence changes are
small and direction is unchanged.

The compact saved analysis state contains:

- `overall_direction`
- Per-timeframe `direction`, `score`, and `confidence`
- `last_alert_time`

Offline mode prints whether the current analysis would notify compared with the
saved state:

```bash
python bot.py offline
```

To test notification rules:

```bash
python test_notification_engine.py
```

## v0.8 Platform Readiness Layer

`readiness.py` prevents misleading trading alerts before every required
timeframe is usable.

Required timeframes:

- `15m`
- `1H`
- `4H`
- `1D`

Each timeframe must have at least 50 candles, non-empty latest values for
`ema_13`, `ema_21`, `ema_50`, `sma_35`, `rsi_14`, and `macd_hist`, plus an
available `atr_14`.

Live mode still analyzes and saves state on completed 15m boundaries, but it
does not send trading alerts until the platform readiness check passes. When
the platform changes from not-ready to ready, the bot sends one
`XAU Platform Ready` message.

Offline mode prints readiness status and per-timeframe reasons:

```bash
python bot.py offline
```

To test readiness rules:

```bash
python test_readiness.py
```
