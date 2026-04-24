# Job Hunter Skill

一个基于 `DrissionPage + CDP 端口接管` 的自动化求职投递工具，当前聚焦 `Boss直聘` 与 `实习僧`。

An AI-assisted job application automation tool built on `DrissionPage + CDP takeover`, currently focused on `Boss直聘` and `Shixiseng`.

AI-assisted job application automation for `Boss直聘` and `实习僧`, built on `DrissionPage + CDP takeover`.

This repository is currently an `alpha` release. The core flow has been run against live sites, but selectors and page behavior can still change over time.

## Highlights

- `DrissionPage only`: no Playwright or Selenium browser launch flow
- `Single-platform execution`: run `Boss` or `SXS` independently
- `Safe by default`: explicit `rehearsal` and `apply` modes
- `Extensible adapter design`: easy to add new job platforms later
- `Analysis-friendly logs`: structured `runs`, `records`, and `analytics`

## Why this project

- Uses `DrissionPage` only, with local browser takeover via CDP.
- Keeps platform adapters decoupled from the entry script.
- Supports explicit `rehearsal` and `apply` modes.
- Scores JDs with rule-based logic plus an OpenAI-compatible LLM hook.
- Writes structured JSON logs for later analysis.

## Supported platforms

- `Boss直聘`
- `实习僧`

## What this repo does not do

- It does not launch Playwright or Selenium browsers.
- It does not support `51job` in the current release.
- It does not guarantee long-term selector stability for live websites.

## Project layout

```text
job-hunter-skill/
├── skill_entry.py
├── shared.py
├── boss_apply.py
├── sxs_apply.py
├── doctor.py
├── config.example.json
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── tests/
```

## Quickstart

### 1. Clone and install

```bash
git clone <your-repo-url>
cd job-hunter-skill
python -m pip install -e .
```

If you prefer plain requirements:

```bash
python -m pip install -r requirements.txt
```

### 2. Prepare your local runtime directory

By default, the project uses your current working directory as the runtime directory. That means these files will live in the folder where you run the command:

- `config.json`
- `resume.md`
- `job-hunter.log`
- `boss-<city>-log.json`
- `sxs-<city>-log.json`
- `.job_hunter/browser/...`

Copy the example config:

```bash
cp config.example.json config.json
```

On PowerShell:

```powershell
Copy-Item config.example.json config.json
```

Put your resume in:

```text
./resume.md
```

You can start from the provided template:

```powershell
Copy-Item resume.example.md resume.md
```

You can also use another runtime directory:

```bash
job-hunter --skill-dir /path/to/workspace
```

Or set an environment variable:

```bash
JOB_HUNTER_HOME=/path/to/workspace
```

### 3. Run the environment doctor

```bash
job-hunter-doctor --json
```

Or:

```bash
python doctor.py --json
```

The doctor checks:

- Python version
- presence of core code files
- `config.json`
- `resume_path`
- `DrissionPage`
- LLM settings
- whether platform browser debug ports are listening

## Browser launch model

This project relies on `manual browser login + CDP port takeover`.

### Boss直聘

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir=".job_hunter/browser/boss"
```

### 实习僧

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9223 --user-data-dir=".job_hunter/browser/sxs"
```

Log in manually, keep the browser open, then run the skill.

## Usage

### Interactive entry

```bash
python skill_entry.py
```

### Installed CLI

```bash
job-hunter --platform boss --mode rehearsal --job "Java开发实习生" --city 北京 --count 1
```

### Boss rehearsal

```bash
job-hunter --platform boss --mode rehearsal --job "Java开发实习生" --city 北京 --count 1
```

### Boss real apply

```bash
job-hunter --platform boss --mode apply --job "Java开发实习生" --city 北京 --count 1 --min-score 80
```

### Shixiseng rehearsal

```bash
job-hunter --platform sxs --mode rehearsal --job "Java开发实习生" --city 北京 --count 1
```

### Shixiseng real apply

```bash
job-hunter --platform sxs --mode apply --job "Java开发实习生" --city 北京 --count 1 --min-score 80
```

If you already finished browser login, add:

```bash
--yes
```

### Platform-only scripts

```bash
job-hunter-boss --job "Java开发实习生" --city 北京 --count 1 --mode rehearsal
job-hunter-sxs --job "Java开发实习生" --city 北京 --count 1 --mode rehearsal
```

## Config

Use `config.example.json` as the starting point.

Important fields:

- `resume_path`: local resume path
- `greeting`: Boss greeting text
- `skills`: extracted or manually maintained skill keywords
- `target_roles`: role keywords that receive role bonus
- `exclude_keywords`: hard stop keywords
- `min_score`: threshold for real apply
- `default_mode`: recommended default is `rehearsal`
- `platform_ports`: CDP ports per platform
- `user_data_dirs`: browser user-data-dir per platform
- `llm`: OpenAI-compatible endpoint settings

For LLM settings, you can use either `config.json` or environment variables:

- `JOB_HUNTER_LLM_BASE_URL`
- `JOB_HUNTER_LLM_API_KEY`
- `JOB_HUNTER_LLM_MODEL`
- `JOB_HUNTER_LLM_TIMEOUT`
- `JOB_HUNTER_LLM_TEMPERATURE`

## Run modes

### `rehearsal`

- No real application click is executed.
- Useful for selector checks, JD extraction, scoring, and login validation.
- Recommended default for first-time setup.

### `apply`

- Real apply actions are executed after the score reaches the threshold.
- Use only after you verify the platform flow in rehearsal mode.

## Logging

Each platform writes an analysis-friendly JSON log.

Examples:

- `boss-北京-log.json`
- `sxs-北京-log.json`

Schema summary:

```json
{
  "schema_version": 2,
  "meta": {},
  "runs": [],
  "records": {
    "applied": [],
    "skipped": [],
    "failed": []
  },
  "analytics": {}
}
```

Highlights:

- `runs`: batch-level execution history with `run_id`
- `records`: job-level details for applied, skipped, and failed items
- `analytics`: counts, score summary, top-scoring jobs, and company totals

## Architecture

- `skill_entry.py`: single-platform dispatcher
- `shared.py`: config, LLM, logging, scoring, browser takeover helpers
- `boss_apply.py`: Boss adapter
- `sxs_apply.py`: Shixiseng adapter
- `doctor.py`: environment self-check

To add another platform:

1. Create `<platform>_apply.py`
2. Implement `apply_jobs(task, config, browser, skill_dir)`
3. Register it in `SCRIPT_REGISTRY` in `skill_entry.py`
4. Add label, alias, default port, and browser dir mapping in `shared.py`

## Development

Run local checks:

```bash
python doctor.py --json
python -m unittest tests.test_core
python -m py_compile skill_entry.py shared.py boss_apply.py sxs_apply.py doctor.py tests/test_core.py
```

CI is configured in `.github/workflows/ci.yml`.

## Safety and responsibility

Use this project at your own risk.

- You are responsible for complying with the terms of the target platforms.
- Manual login is intentionally required.
- Always validate flows in `rehearsal` mode before using `apply`.
- Do not commit your `config.json`, `resume.md`, browser profiles, or local logs.

## Roadmap

- More resilient selector fallbacks
- Optional structured export for analytics
- Additional platform adapters
- Better test coverage around shared scoring and runtime behavior
