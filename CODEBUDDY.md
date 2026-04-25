# CODEBUDDY.md

You are working in the `job-hunter-skill` repository.

## What this repo is

A Chinese-facing open-source skill for automated job application matching and submission.

## What to do

- Keep Boss直聘 and 实习僧 as separate adapters.
- Keep the browser stack on `DrissionPage` + CDP takeover.
- Prefer small, easy-to-review changes.
- Preserve the Chinese README and user-facing docs.
- Keep the repository easy for newcomers to scan.

## What to read first

- `README.md`
- `docs/REPO_MAP.md`
- `skill_entry.py`
- `shared.py`
- `boss_apply.py`
- `sxs_apply.py`
- `doctor.py`

## Important rules

- Do not add Playwright or Selenium browser launchers.
- Do not hardcode local machine paths into committed source files.
- Do not commit private runtime files.
- Keep examples and docs in Chinese.
- If you add a new platform, document it in `README.md` and `docs/REPO_MAP.md`.

## Suggested workflow

1. Inspect the minimum set of files.
2. Make the change in code.
3. Update `README.md` and `docs/` if the user-facing workflow changed.
4. Run the repository checks.
5. Verify the workspace is clean before finishing.

