from datetime import UTC, datetime

import massive_api


def make_candle(day, close):
    return {
        "time": datetime(2026, 1, day, tzinfo=UTC),
        "open": close,
        "high": close,
        "low": close,
        "close": close,
    }


def main():
    calls = []
    chunks = [
        [make_candle(1, 1.0), make_candle(2, 2.0)],
        [make_candle(2, 22.0), make_candle(3, 3.0)],
        [make_candle(4, 4.0)],
    ]

    original_fetch = massive_api._fetch_bootstrap_chunk
    original_datetime = massive_api.datetime

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 1, 5, tzinfo=tz)

    def fake_fetch(**kwargs):
        calls.append(kwargs)
        return chunks[len(calls) - 1]

    try:
        massive_api.datetime = FixedDatetime
        massive_api._fetch_bootstrap_chunk = fake_fetch
        candles = massive_api.bootstrap_1m_history(days=4, chunk_days=2)
    finally:
        massive_api.datetime = original_datetime
        massive_api._fetch_bootstrap_chunk = original_fetch

    assert len(calls) == 3, f"expected 3 chunks, got {len(calls)}"
    assert [c["time"].day for c in candles] == [1, 2, 3, 4]
    assert candles[1]["close"] == 22.0

    print("PASS: bootstrap chunks full range, dedupes by time, and sorts candles")


if __name__ == "__main__":
    main()
