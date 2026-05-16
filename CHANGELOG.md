# Changelog

All notable changes to `tgram-analytics` (the Python SDK) are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-05-16

### Added
- **Array-valued event properties.** `EventProperties` now accepts lists of scalars in addition to single scalars, enabling multi-select onboarding answers, A/B variant memberships, and any set-style attribute that previously needed lossy workarounds.

  ```python
  tga.track(
      "onboarding_completed",
      session_id="user-session-123",
      properties={
          "role": "creator",
          "interest_set": ["vertical_to_horizontal", "unsure"],
      },
  )
  ```

  Lists whose key ends in `_set` are sorted alphabetically by the server at write time so `GROUP BY properties->'interest_set'` collapses equivalent combinations into a single bucket. Other list properties keep insertion order.

- **Runtime validation** on `track()`, `pageview()`, and `identify()` properties. Nested dicts, nested lists, `NaN`, `Infinity`, and other non-scalar values now raise `TypeError` synchronously with a message that names the bad key — surfacing developer mistakes in dev rather than as silent server-side 422s.

- New exported types `EventPropertyScalar` and `EventPropertyValue` for callers who want to spell out their property shape explicitly.

### Changed
- `EventProperties` widened from `dict[str, Union[str, int, float, bool, None]]` to `dict[str, EventPropertyValue]` where `EventPropertyValue = Union[Scalar, list[Scalar]]`. **Non-breaking:** all existing scalar-only code continues to typecheck and round-trip unchanged.

## [0.1.2]

Initial public release.
