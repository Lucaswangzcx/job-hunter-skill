# 求职投递自动化 Skill

这是一个给中国大学生和求职者使用的 Agent Skill，用于在人工登录浏览器后，辅助完成岗位匹配、投递前安全演练和正式投递。

真正给 agent 读取和执行的入口是 [SKILL.md](./SKILL.md)。GitHub 首页只保留最短说明，避免文档堆叠。

## 目录结构

```text
.
├── SKILL.md                 # Agent 使用说明，中文源头文档
├── agents/openai.yaml       # Codex/Agent UI 元数据
├── job_hunter_skill/        # 自动化投递核心代码
├── examples/                # 配置和简历模板，不含真实隐私
├── tests/                   # 核心逻辑测试
├── .github/workflows/ci.yml # 最小 CI
├── pyproject.toml           # Python 包和 CLI 入口
└── README.md                # GitHub 简介
```

## 支持范围

- Boss直聘
- 实习僧
- 安全演练模式：`rehearsal`
- 正式投递模式：`apply`

自动化方式是 `DrissionPage + CDP 端口接管`。用户必须自己启动浏览器并手动登录，skill 不接管账号密码。
执行前会检查目标 CDP 端口是否已监听；端口未打开时直接报错，不自动新开浏览器。

## 安装

```bash
python -m pip install -e .
```

安装成 Codex skill：

```powershell
robocopy . "$env:USERPROFILE\.codex\skills\job-hunter-skill" /E /XD .git .job_hunter __pycache__ /XF config.json resume.md job-hunter.log *-log.json
```

重启 Codex 后即可用 `$job-hunter-skill`。

## 首次使用

```powershell
Copy-Item examples/resume.example.md resume.md
```

先把 `resume.md` 改成自己的简历，并放在运行目录。第一次运行 `job-hunter` 时，如果没有 `config.json`，skill 会进入引导流程：

- 提示用户确认 `resume.md` 的位置。
- 让用户填写打招呼话术、目标岗位、排除关键词、端口、运行模式、阈值和评分标准。
- 不让用户手写 `skills`，而是根据简历自动抽取 8-15 个关键点。
- 生成本地私有 `config.json`。

`config.json`、`resume.md` 和日志都不会提交到 GitHub。

## 搜索和评分

- 命令行 `--job` 是本次平台搜索词。
- 未传 `--job` 时，默认使用 `config.json` 里 `target_roles` 的第一个岗位。
- 本次搜索词会临时加入评分用 `target_roles`，避免搜索岗位和岗位加分标准不一致。
- 关键词匹配会容忍常见空格差异，例如 `Java开发实习生` 可以命中 `Java 开发实习生`。
- 评分权重集中放在 `config.json` 的 `scoring` 段，用户可以按自身情况调整岗位命中、技能命中和 LLM/启发式补分。

## 检查

```bash
python -m job_hunter_skill.doctor --json
python -m unittest tests.test_core
python -m py_compile job_hunter_skill/skill_entry.py job_hunter_skill/shared.py job_hunter_skill/boss_apply.py job_hunter_skill/sxs_apply.py job_hunter_skill/doctor.py tests/test_core.py
```

## 隐私边界

不要提交这些本地运行文件：

- `config.json`
- `resume.md`
- `resume.txt`
- `job-hunter.log`
- `*-log.json`
- `.job_hunter/`
