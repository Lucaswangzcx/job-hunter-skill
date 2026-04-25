# Job Hunter Skill

一个面向真实求职场景的自动化投递工具，基于 `DrissionPage + CDP 端口接管` 实现，当前支持：

- `Boss直聘`
- `实习僧`

这是一个适合中国大学生和求职者直接上手的开源 `alpha` 项目。目标不是“炫技”，而是把真实可跑、可演练、可扩展、可协作的骨架先打稳。

## 3 分钟上手版

如果你只想最快跑起来，按这 4 步走：

1. 先看 [docs/START_HERE.md](./docs/START_HERE.md)
2. 复制 [config.example.json](./config.example.json) 和 [resume.example.md](./resume.example.md)
3. 打开浏览器手动登录 `Boss直聘` 或 `实习僧`
4. 运行 [skill_entry.py](./skill_entry.py)

## 按使用路径看

### 路线 A：我是路人，第一次来用

先看这些：

1. [docs/START_HERE.md](./docs/START_HERE.md) - 3 分钟上手版
2. [config.example.json](./config.example.json) - 配置长什么样
3. [resume.example.md](./resume.example.md) - 简历模板长什么样
4. [docs/REPO_MAP.md](./docs/REPO_MAP.md) - 仓库文件怎么分工

然后按这个顺序上手：

1. 安装依赖
2. 复制示例配置
3. 填自己的 `resume.md`
4. 先跑 `doctor.py`
5. 再跑 `skill_entry.py`

### 路线 B：我是要真的跑起来的人

先看这些执行入口：

- [skill_entry.py](./skill_entry.py) - 总入口
- [shared.py](./shared.py) - 公共能力
- [boss_apply.py](./boss_apply.py) - Boss 适配器
- [sxs_apply.py](./sxs_apply.py) - 实习僧适配器
- [doctor.py](./doctor.py) - 环境自检

再看这些运行文件：

- `config.json`
- `resume.md`
- `job-hunter.log`
- `boss-<城市>-log.json`
- `sxs-<城市>-log.json`

### 路线 C：我是 agent，要接手这个仓库

先看这些说明文件：

- [CLAUDE.md](./CLAUDE.md)
- [CODEBUDDY.md](./CODEBUDDY.md)
- [TRAE.md](./TRAE.md)

再看执行链：

- [skill_entry.py](./skill_entry.py)
- [shared.py](./shared.py)
- [boss_apply.py](./boss_apply.py)
- [sxs_apply.py](./sxs_apply.py)

### 路线 D：我是开发者，要改代码

先看这些：

- [docs/REPO_MAP.md](./docs/REPO_MAP.md)
- [tests/test_core.py](./tests/test_core.py)
- [scripts/](./scripts/)

然后再做修改：

1. 先改代码
2. 再改 README
3. 再改 docs
4. 最后跑测试和自检

### 路线 E：我是要发布仓库的人

先看这些：

- [docs/GITHUB_RELEASE_v0.1.0.md](./docs/GITHUB_RELEASE_v0.1.0.md)
- [docs/GITHUB_REPO_COPY.md](./docs/GITHUB_REPO_COPY.md)
- [docs/RELEASE_CHECKLIST.md](./docs/RELEASE_CHECKLIST.md)

然后确认：

- 没有提交 `config.json`
- 没有提交 `resume.md`
- 没有提交本地浏览器目录
- 没有提交日志和缓存文件

## 这个项目做什么

- 只使用 `DrissionPage`，不使用 Playwright 或 Selenium 主动启动浏览器
- 让用户先手动登录，再由脚本接管本地浏览器会话
- 按简历和 JD 做匹配评分
- 支持 `安全演练` 和 `正式投递` 两种模式
- 记录结构化日志，方便后续分析和复盘

## 当前支持的平台

- `Boss直聘`
- `实习僧`

## 当前不做什么

- 不支持 `51job`
- 不主动启动 Playwright / Selenium 浏览器
- 不承诺所有站点 selector 永久稳定

## 项目结构

如果你想先看文件分工，直接去 [docs/REPO_MAP.md](./docs/REPO_MAP.md)。
这里只保留一条最短说明：根目录放入口、公共逻辑、平台适配器和发布文件，`docs/` 放面向用户的说明，`tests/` 放最核心的测试。

## 快速开始

### 1. 安装

```bash
git clone <你的仓库地址>
cd job-hunter-skill
python -m pip install -e .
```

如果你更想用 requirements：

```bash
python -m pip install -r requirements.txt
```

### 2. 准备运行目录

默认情况下，项目会把配置、简历和日志写到你运行命令时所在的目录。通常会包含这些文件：

- `config.json`
- `resume.md`
- `job-hunter.log`
- `boss-<城市>-log.json`
- `sxs-<城市>-log.json`
- `.job_hunter/browser/...`

先复制示例配置：

```powershell
Copy-Item config.example.json config.json
Copy-Item resume.example.md resume.md
```

把你的简历内容填进 `resume.md` 后再继续。

如果你想指定别的运行目录：

```bash
job-hunter --skill-dir /path/to/workspace
```

也可以通过环境变量指定：

```bash
JOB_HUNTER_HOME=/path/to/workspace
```

### 3. 运行自检

```bash
job-hunter-doctor --json
```

或者：

```bash
python doctor.py --json
```

自检会检查：

- Python 版本
- 核心代码文件是否存在
- `config.json`
- `resume_path`
- `DrissionPage`
- LLM 配置
- 平台浏览器端口是否已监听

## 浏览器启动方式

这个项目依赖“手动登录 + CDP 接管”。

### Boss直聘

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir=".job_hunter/browser/boss"
```

### 实习僧

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9223 --user-data-dir=".job_hunter/browser/sxs"
```

登录完成后保持浏览器窗口打开，再运行脚本。

## 使用方式

### 交互式入口

```bash
python skill_entry.py
```

### 安装后的 CLI

```bash
job-hunter --platform boss --mode rehearsal --job "Java开发实习生" --city 北京 --count 1
```

### Boss 安全演练

```bash
job-hunter --platform boss --mode rehearsal --job "Java开发实习生" --city 北京 --count 1
```

### Boss 正式投递

```bash
job-hunter --platform boss --mode apply --job "Java开发实习生" --city 北京 --count 1 --min-score 80
```

### 实习僧 安全演练

```bash
job-hunter --platform sxs --mode rehearsal --job "Java开发实习生" --city 北京 --count 1
```

### 实习僧 正式投递

```bash
job-hunter --platform sxs --mode apply --job "Java开发实习生" --city 北京 --count 1 --min-score 80
```

如果你已经登录完成，可以加：

```bash
--yes
```

### 平台脚本直跑

```bash
job-hunter-boss --job "Java开发实习生" --city 北京 --count 1 --mode rehearsal
job-hunter-sxs --job "Java开发实习生" --city 北京 --count 1 --mode rehearsal
```

## 配置说明

把 [config.example.json](./config.example.json) 复制成 `config.json` 后，再按自己的情况修改。

核心字段：

- `resume_path`：本地简历路径
- `greeting`：Boss 打招呼话术
- `skills`：技能关键词
- `target_roles`：期望岗位关键词
- `exclude_keywords`：排除关键词
- `min_score`：正式投递阈值
- `default_mode`：默认模式，建议 `rehearsal`
- `platform_ports`：平台对应的 CDP 端口
- `user_data_dirs`：平台对应的浏览器用户目录
- `llm`：OpenAI 兼容接口配置

LLM 配置也可以通过环境变量设置：

- `JOB_HUNTER_LLM_BASE_URL`
- `JOB_HUNTER_LLM_API_KEY`
- `JOB_HUNTER_LLM_MODEL`
- `JOB_HUNTER_LLM_TIMEOUT`
- `JOB_HUNTER_LLM_TEMPERATURE`

## 运行模式

### `rehearsal`

- 不执行真实投递
- 适合验证搜索、详情读取、评分和按钮定位
- 建议第一次使用时先跑这个模式

### `apply`

- 达到阈值后执行真实投递
- 只建议在你确认流程稳定后使用

## 日志

每个平台都会写分析友好的 JSON 日志。

示例：

- `boss-北京-log.json`
- `sxs-北京-log.json`

日志结构简述：

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

重点字段：

- `runs`：批次级运行记录，带 `run_id`
- `records`：岗位级明细，适合筛选和导出分析
- `analytics`：总量、分数统计、高分岗位、公司统计

## 架构

- `skill_entry.py`：单平台入口调度
- `shared.py`：配置、LLM、日志、评分、浏览器接管工具
- `boss_apply.py`：Boss 适配器
- `sxs_apply.py`：实习僧适配器
- `doctor.py`：环境自检

如果要新增平台：

1. 新建 `<platform>_apply.py`
2. 实现 `apply_jobs(task, config, browser, skill_dir)`
3. 在 `skill_entry.py` 的 `SCRIPT_REGISTRY` 里注册
4. 在 `shared.py` 里补平台名称、别名、默认端口和浏览器目录

## 开发

本地检查命令：

```bash
python doctor.py --json
python -m unittest tests.test_core
python -m py_compile skill_entry.py shared.py boss_apply.py sxs_apply.py doctor.py tests/test_core.py
```

CI 配置在 [`.github/workflows/ci.yml`](./.github/workflows/ci.yml)。

## 风险说明

请自行确认你对目标平台的使用方式是否符合对应服务条款。

- 必须手动登录
- 建议先用 `rehearsal`
- 不要提交 `config.json`、`resume.md`、本地浏览器目录和日志

## 后续可以做什么

- 提升 selector 稳定性
- 增加更多平台适配器
- 增加更完整的日志分析能力
- 提升共享逻辑的测试覆盖率
