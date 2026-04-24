# Release Checklist

Use this before publishing a new GitHub release.

## Repository hygiene

- [ ] Confirm `config.json`, `resume.md`, `job-hunter.log`, `*-log.json`, and `.job_hunter/` are not committed
- [ ] Confirm no private API keys or local absolute personal paths remain in docs or examples
- [ ] Confirm `README.md`, `CHANGELOG.md`, and `LICENSE` are present
- [ ] Confirm version in `pyproject.toml` matches the intended release tag

## Validation

- [ ] `python doctor.py --json`
- [ ] `python -m unittest tests.test_core`
- [ ] `python -m py_compile skill_entry.py shared.py boss_apply.py sxs_apply.py doctor.py tests/test_core.py`
- [ ] Optional: `python -m pip install -e .`

## Manual smoke checks

- [ ] Boss rehearsal run verified
- [ ] SXS rehearsal run verified
- [ ] If doing a live-release confidence check, test only on throwaway or explicitly approved targets

## GitHub setup

- [ ] Initialize the repo if needed: `git init`
- [ ] Add remote origin
- [ ] Push default branch
- [ ] Enable Issues and Discussions if desired
- [ ] Review `.github/ISSUE_TEMPLATE/*` and replace placeholder discussion URL

## Tag and release

- [ ] Commit all release files
- [ ] Create a tag such as `v0.1.0`
- [ ] Draft GitHub release notes from `CHANGELOG.md`

