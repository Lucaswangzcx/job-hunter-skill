## Summary

- What does this PR change?
- Why is the change needed?

## Checklist

- [ ] I kept the browser stack on `DrissionPage`
- [ ] I did not add Playwright or Selenium browser launch logic
- [ ] I tested the affected shared logic locally
- [ ] I updated docs if user-facing behavior changed
- [ ] I removed or masked private paths, tokens, and logs

## Validation

```bash
python doctor.py --json
python -m unittest tests.test_core
python -m py_compile skill_entry.py shared.py boss_apply.py sxs_apply.py doctor.py tests/test_core.py
```

## Notes

- Any selector assumptions:
- Any live-site caveats:

