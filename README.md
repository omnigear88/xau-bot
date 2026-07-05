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
last close, latest EMA13, EMA21, ATR14, RSI14, and MACD histogram.

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
