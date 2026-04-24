# Contributing

Thanks for contributing to Job Hunter.

## Before you open a PR

1. Keep the browser automation stack on `DrissionPage`.
2. Do not switch the runtime to Playwright or Selenium browser launch mode.
3. Prefer adding new platforms as independent adapters instead of coupling logic into `skill_entry.py`.
4. Keep default behavior safe: `rehearsal` should remain the recommended default.

## Local setup

```bash
python -m pip install -e .
python doctor.py --json
python -m unittest tests.test_core
```

## Adapter guidelines

- Implement new platforms in a dedicated `<platform>_apply.py`.
- Expose `apply_jobs(task, config, browser, skill_dir)`.
- Reuse `shared.py` for config, browser takeover, logging, and scoring.
- Avoid hard-coding machine-specific absolute paths.
- Do not auto-fill platform forms unless the behavior is explicit and documented.

## Selector changes

- Prefer resilient selectors based on text and stable class fragments.
- Keep fallbacks when the site has multiple layout variants.
- If a selector fix is derived from a live page, document the scenario in the PR.

## Tests

- Add or update unit tests for any non-trivial shared logic change.
- Keep tests deterministic and independent from live websites.
- Do not require a logged-in browser session in CI.

