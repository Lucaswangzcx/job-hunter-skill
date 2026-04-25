# CLAUDE.md

This repository is an open-source Chinese job application automation skill.

## Primary goal

Help users automate job matching and submission on:

- Boss直聘
- 实习僧

## Hard constraints

- Use `DrissionPage` only for browser automation.
- Do not introduce Playwright or Selenium as browser launchers.
- Use CDP takeover with local ports:
  - Boss: `9222`
  - 实习僧: `9223`
- Require manual browser login before automation.
- Keep the repository free of personal or machine-specific local data.

## Read first

1. `README.md`
2. `docs/REPO_MAP.md`
3. `config.example.json`
4. `resume.example.md`
5. `doctor.py`
6. `skill_entry.py`
7. `shared.py`
8. Platform adapter:
   - `boss_apply.py`
   - `sxs_apply.py`

## Runtime model

- `skill_entry.py` is the single-platform dispatcher.
- Each platform is independent.
- Do not couple Boss and 实习僧 into a combined run path.
- Safe rehearsal mode must remain the default recommendation.

## Files to avoid committing

- `config.json`
- `resume.md`
- `job-hunter.log`
- `*-log.json`
- `.job_hunter/`
- `__pycache__/`
- `*.pyc`

## If you change behavior

- Update `README.md` at the same time.
- Update the matching docs in `docs/`.
- Keep examples in Chinese.
- Keep the agent workflow explicit and reproducible.

## Before finishing a task

- Run `python doctor.py --json`
- Run `python -m unittest tests.test_core`
- Make sure the workspace does not contain local runtime artifacts

