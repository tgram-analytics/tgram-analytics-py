# tgram-analytics Python SDK

Lightweight Python SDK for [tgram-analytics](https://github.com/tgram-analytics). Track events and pageviews from your Python backend.

## Install

```bash
pip install tgram-analytics
```

Get a free `proj_` API key from [@MyTelegramAnalyticsBot](https://t.me/MyTelegramAnalyticsBot) on Telegram (1 project free), or [self-host the server](https://github.com/tgram-analytics/server) and create keys via your own bot.

## Quick start (sync)

```python
from tgram_analytics import TGA

with TGA("proj_xxx", "https://analytics.example.com") as tga:
    tga.track("signup", session_id="user-session-123", properties={"plan": "pro"})
    tga.pageview(session_id="user-session-123", url="/dashboard")
```

## Quick start (async)

```python
from tgram_analytics import AsyncTGA

async with AsyncTGA("proj_xxx", "https://analytics.example.com") as tga:
    tga.track("signup", session_id="user-session-123")
    await tga.flush()
```

## Batching

Buffer events and send them in batches to reduce HTTP requests:

```python
from tgram_analytics import TGA, BatchOptions

tga = TGA("proj_xxx", "https://analytics.example.com", batch=BatchOptions(max_size=20, max_wait=3.0))
# Events are buffered and auto-flushed when max_size is reached or max_wait seconds elapse
tga.track("click", "session-1")
tga.flush()  # manual flush
tga.close()  # flushes + closes HTTP client
```

## Identifying users

Attach persistent properties to a session. All subsequent `track()` and `pageview()` calls for that session will include them:

```python
tga.identify("session-123", {"plan": "pro", "locale": "en-US"})
tga.track("purchase", "session-123", {"amount": 49})
# sent properties: {"plan": "pro", "locale": "en-US", "amount": 49}
```

Per-event properties override identified properties when keys conflict.

Call `tga.forget("session-123")` to clear stored properties for a session.

## API reference

### `TGA(api_key, server_url, *, batch=False, timeout=10.0)`

Sync client. `api_key` must start with `"proj_"`.

- `batch` — `False` (default), `True` (default thresholds), or `BatchOptions(max_size=10, max_wait=5.0)`
- `timeout` — HTTP request timeout in seconds

### `AsyncTGA(api_key, server_url, *, batch=False, timeout=10.0)`

Async client with the same constructor signature.

### `.track(event_name, session_id, properties=None)`

Track a custom event. Fire-and-forget — errors are logged, never raised.

### `.pageview(session_id, url, referrer=None, properties=None)`

Track a pageview event.

### `.identify(session_id, properties)`

Store properties that are merged into all subsequent events for this session.

### `.forget(session_id)`

Remove stored `identify()` properties for a session.

### `.flush()`

Send all buffered events immediately. No-op if batching is disabled.

### `.close()` / `await .close()`

Flush pending events and close the HTTP client.

Both clients support context managers (`with` / `async with`) for automatic cleanup.

## Error handling

Analytics should never break your application. All HTTP and network errors are caught and logged via Python's `logging` module under the `tgram_analytics` logger:

```python
import logging
logging.getLogger("tgram_analytics").setLevel(logging.DEBUG)
```

Only the constructor raises exceptions (on invalid `api_key` or missing `server_url`).

## License

MIT

## Links

- Website: <https://tgram-analytics.com>
- Server (API): <https://github.com/tgram-analytics/server>
- JS SDK: <https://github.com/tgram-analytics/tgram-analytics-js>
- Python SDK: <https://github.com/tgram-analytics/tgram-analytics-py>
- Flutter SDK: <https://github.com/tgram-analytics/tgram-analytics-flutter>
