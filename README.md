# XAU Bot

A Python-based XAUUSD market data and alert system.

## Purpose

This project collects live XAUUSD data from IG, stores completed 1-minute candles in SQLite, builds higher timeframes locally, and sends Telegram alerts based on trading logic.

## Current Architecture

IG Streaming API
→ 1-minute candles
→ SQLite database
→ Resampler
→ Indicators
→ Strategy
→ Telegram

## Main Files

- `bot.py` — application entry point
- `market_data.py` — IG streaming and candle collection
- `database.py` — SQLite storage and retrieval
- `resampler.py` — builds 15m, 1H, 4H, 1D candles from 1m data
- `indicators.py` — technical indicators
- `strategy.py` — trading logic
- `telegram_bot.py` — Telegram messages
- `state.py` — prevents duplicate alerts

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
