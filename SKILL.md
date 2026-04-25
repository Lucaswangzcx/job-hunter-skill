---
name: job-hunter-skill
description: Job search automation for Chinese recruiting platforms using DrissionPage CDP browser takeover. Use when an agent needs to help a user set up, configure, rehearse, run, debug, or extend automated job matching and applications for Boss直聘 or 实习僧, including resume/config preparation, safe rehearsal runs, formal apply runs, platform adapter maintenance, and repository checks.
---

# Job Hunter Skill

Use this skill to help users run or maintain the Job Hunter automation project. The project supports Boss直聘 and 实习僧 with `DrissionPage` plus CDP takeover of a browser the user started and logged into manually.

## Core Rules

- Keep `rehearsal` as the default recommendation. Run `apply` only when the user explicitly asks for real submissions.
- Require manual browser login before automation. Do not automate credential entry.
- Use `DrissionPage` and CDP takeover only. Do not add Playwright or Selenium browser launchers.
- Treat Boss直聘 and 实习僧 as independent platform adapters with separate ports and browser profiles.
- Never commit or expose local/private runtime files: `config.json`, `resume.md`, `job-hunter.log`, `*-log.json`, `.job_hunter/`, `__pycache__/`, or `*.pyc`.
- Keep user-facing examples and docs in Chinese.

## Read First

Load only what is needed for the task:

- General use: `README.md`, `docs/START_HERE.md`, `config.example.json`, `resume.example.md`
- Repository orientation: `docs/REPO_MAP.md`
- CLI and dispatch flow: `skill_entry.py`, then `shared.py`
- Environment checks: `doctor.py`
- Platform behavior: `boss_apply.py` or `sxs_apply.py`
- Existing agent notes: `CLAUDE.md`, `CODEBUDDY.md`, `TRAE.md`

## Runtime Model

- `skill_entry.py` is the main single-platform dispatcher.
- Installed CLI commands are defined in `pyproject.toml`:
  - `job-hunter`
  - `job-hunter-doctor`
  - `job-hunter-boss`
  - `job-hunter-sxs`
- Runtime data is resolved from `--skill-dir`, `JOB_HUNTER_HOME`, or the current working directory.
- Default CDP ports are Boss直聘 `9222` and 实习僧 `9223`.

## Common Workflows

### Set up or inspect a user run

1. Confirm dependencies are installed: `python -m pip install -e .`
2. Ask the user to copy `config.example.json` to `config.json` and `resume.example.md` to `resume.md` in their chosen runtime directory if they do not already have private files.
3. Run `python doctor.py --json` or `job-hunter-doctor --json`.
4. If browser checks fail, show the relevant Edge command from `README.md` and ask the user to log in manually.

### Rehearse before applying

Prefer this command shape:

```bash
job-hunter --platform boss --mode rehearsal --job "Java开发实习生" --city 北京 --count 1 --skill-dir /path/to/runtime
```

Use `--platform sxs` for 实习僧. Use `--yes` only after the user confirms the correct browser is open and logged in.

### Run real applications

Use formal apply mode only after explicit user confirmation:

```bash
job-hunter --platform boss --mode apply --job "Java开发实习生" --city 北京 --count 1 --min-score 80 --skill-dir /path/to/runtime
```

Before running, restate that this can submit real applications.

### Modify or extend the project

1. Keep changes small and local to the relevant module.
2. For new platforms, add `<platform>_apply.py`, implement `apply_jobs(task, config, browser, skill_dir)`, register it in `skill_entry.py`, update defaults/aliases in `shared.py`, then update `README.md` and `docs/REPO_MAP.md`.
3. If behavior changes, update user docs in the same change.
4. Run repository checks before finishing.

## Validation

Use the checks that match the task:

```bash
python doctor.py --json
python -m unittest tests.test_core
python -m py_compile skill_entry.py shared.py boss_apply.py sxs_apply.py doctor.py tests/test_core.py
```

If a check cannot run because dependencies, credentials, a logged-in browser, or network access are missing, report that clearly and keep the user on `rehearsal` until the environment is ready.
