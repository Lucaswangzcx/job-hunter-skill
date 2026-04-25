---
name: job-hunter-skill
description: 面向中国大学生和求职者的求职投递自动化 skill。用于让 agent 帮用户准备简历和配置、检查环境、启动安全演练、在用户明确确认后执行正式投递，并维护 Boss直聘、实习僧等中国招聘平台的 DrissionPage/CDP 自动化适配器。触发场景包括自动投递、岗位匹配、Boss直聘、实习僧、安全演练、正式投递、求职配置、自检、浏览器接管、平台适配器维护。
---

# 求职投递自动化 Skill

用这个 skill 帮中国大学生和求职者在 Boss直聘、实习僧上做岗位匹配、投递前演练和正式投递。自动化方式是 `DrissionPage` 接管用户已经手动登录好的浏览器 CDP 端口。

## 核心原则

- 默认只做 `rehearsal` 安全演练，不真实投递。
- 只有用户明确要求正式投递时，才运行 `apply`。
- 正式投递前，必须再次说明“这会产生真实投递行为”。
- 必须让用户自己启动浏览器并手动登录，不自动输入账号、密码或验证码。
- 只使用 `DrissionPage + CDP 接管`，不要引入 Playwright 或 Selenium 启动浏览器。
- Boss直聘和实习僧保持独立适配器、独立端口、独立浏览器用户目录。
- 不读取、不输出、不提交用户隐私文件：`config.json`、`resume.md`、`resume.txt`、`job-hunter.log`、`*-log.json`、`.job_hunter/`。
- 面向用户的说明和示例优先使用中文。

## 目录导航

- `job_hunter_skill/skill_entry.py`：总入口，负责配置检查、任务收集和平台调度。
- `job_hunter_skill/shared.py`：公共能力，包括配置、日志、评分、LLM、浏览器接管。
- `job_hunter_skill/boss_apply.py`：Boss直聘适配器。
- `job_hunter_skill/sxs_apply.py`：实习僧适配器。
- `job_hunter_skill/doctor.py`：环境自检。
- `examples/config.example.json`：配置模板。
- `examples/resume.example.md`：简历模板。
- `tests/test_core.py`：核心逻辑测试。

## 运行模型

- CLI 入口：
  - `job-hunter`
  - `job-hunter-doctor`
  - `job-hunter-boss`
  - `job-hunter-sxs`
- 运行目录由 `--skill-dir`、`JOB_HUNTER_HOME` 或当前目录决定。
- 运行目录里放用户自己的 `config.json`、`resume.md` 和日志。
- 默认端口：
  - Boss直聘：`9222`
  - 实习僧：`9223`

## 首次使用

1. 安装依赖：

```bash
python -m pip install -e .
```

2. 准备用户私有运行文件：

```powershell
Copy-Item examples/config.example.json config.json
Copy-Item examples/resume.example.md resume.md
```

3. 让用户编辑 `resume.md` 和 `config.json`。

4. 运行自检：

```bash
python -m job_hunter_skill.doctor --json
```

## 浏览器登录

Boss直聘：

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir=".job_hunter/browser/boss"
```

实习僧：

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9223 --user-data-dir=".job_hunter/browser/sxs"
```

打开后让用户手动登录，并保持浏览器窗口打开。

## 安全演练

优先运行安全演练：

```bash
job-hunter --platform boss --mode rehearsal --job "Java开发实习生" --city 北京 --count 1 --skill-dir /path/to/runtime
```

实习僧使用：

```bash
job-hunter --platform sxs --mode rehearsal --job "Java开发实习生" --city 北京 --count 1 --skill-dir /path/to/runtime
```

只有当用户确认浏览器已登录，才可以加 `--yes`。

## 正式投递

正式投递必须由用户明确要求：

```bash
job-hunter --platform boss --mode apply --job "Java开发实习生" --city 北京 --count 1 --min-score 80 --skill-dir /path/to/runtime
```

如果用户只是说“帮我看看”“跑一下”“测试一下”，默认仍然使用 `rehearsal`。

## 修改或扩展

1. 小步修改，只碰相关模块。
2. 新增平台时，新增 `job_hunter_skill/<platform>_apply.py`，实现 `apply_jobs(task, config, browser, skill_dir)`。
3. 在 `job_hunter_skill/skill_entry.py` 注册平台。
4. 在 `job_hunter_skill/shared.py` 补平台别名、默认端口和浏览器目录。
5. 行为变化时，同步更新 `SKILL.md` 和 `README.md`。

## 验证

```bash
python -m job_hunter_skill.doctor --json
python -m unittest tests.test_core
python -m py_compile job_hunter_skill/skill_entry.py job_hunter_skill/shared.py job_hunter_skill/boss_apply.py job_hunter_skill/sxs_apply.py job_hunter_skill/doctor.py tests/test_core.py
```

如果因为未安装依赖、未登录浏览器、缺少私有配置或端口未监听导致检查失败，要清楚说明原因，并继续建议用户先跑 `rehearsal`。
