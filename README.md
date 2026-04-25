# Job Hunter Skill

Agent-ready automation skill for matching and applying to jobs on Chinese recruiting platforms.

The skill is defined by [SKILL.md](./SKILL.md). Use that file as the source of truth for agent behavior, safety rules, setup, rehearsal runs, real apply runs, and maintenance workflow.

## What It Does

- Supports Boss直聘 and 实习僧.
- Uses `DrissionPage` with CDP takeover of a browser the user starts and logs into manually.
- Keeps `rehearsal` mode as the safe default.
- Provides CLI entrypoints for agent-assisted setup, self-checks, rehearsals, and apply runs.

## Install

```bash
python -m pip install -e .
```

To install as a Codex skill, copy this repository to the local skills directory and restart Codex:

```powershell
robocopy . "$env:USERPROFILE\.codex\skills\job-hunter-skill" /E /XD .git .job_hunter __pycache__ /XF config.json resume.md job-hunter.log *-log.json
```

Then invoke it as `$job-hunter-skill`.

## Validate

```bash
python doctor.py --json
python -m unittest tests.test_core
python -m py_compile skill_entry.py shared.py boss_apply.py sxs_apply.py doctor.py tests/test_core.py
```

## Runtime Privacy

Do not commit local runtime files:

- `config.json`
- `resume.md`
- `job-hunter.log`
- `*-log.json`
- `.job_hunter/`
