# XAU Bot Roadmap

## Current Version: v0.2
- IG 1-minute streaming works
- SQLite persistence added
- Telegram integration works
- systemd service runs bot 24/7
- Git initialized

## Next Milestone: v0.3 Resampler
Goal: Build higher timeframes from stored 1-minute candles.

Tasks:
- Create resampler.py
- Load 1m candles from SQLite
- Resample into 15m, 1H, 4H, 1D
- Return clean pandas DataFrames
- Test candle counts and timestamps

## Future Ideas
- ATR
- ADX
- RSI
- MACD
- Trend score
- Market structure
- BOS / CHoCH
- Liquidity sweep
- Session context
- Backtesting
- Signal journal
