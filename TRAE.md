# TRAE.md

This repository contains a job-hunting automation skill for Chinese users.

## Project summary

- Platform support:
  - Boss直聘
  - 实习僧
- Browser automation:
  - `DrissionPage`
  - CDP port takeover
- Modes:
  - rehearsal
  - apply

## Agent instructions

- Treat each platform as an independent integration.
- Keep the entry point simple for路人用户.
- Prefer readable docs over hidden conventions.
- If you change a platform flow, update the quickstart in `README.md`.
- If you change a repository path or file meaning, update `docs/REPO_MAP.md`.

## Do not

- Do not use Playwright or Selenium for browser launching.
- Do not commit local browser data.
- Do not commit `config.json` or `resume.md`.
- Do not add machine-specific paths to the tracked source.

## Good places to start

- `README.md`
- `CLAUDE.md`
- `CODEBUDDY.md`
- `skill_entry.py`
- `shared.py`
- `doctor.py`

