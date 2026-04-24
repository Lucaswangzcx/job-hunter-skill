# Job Hunter Skill v0.1.0

首个公开 `alpha` 版本发布。

`Job Hunter Skill` 是一个基于 `DrissionPage + CDP 端口接管` 的自动化求职投递工具，当前支持：

- `Boss直聘`
- `实习僧`

这个版本的目标不是“大而全”，而是先把真实可跑通的核心链路做扎实：

- 手动登录浏览器
- 接管本地调试端口
- 搜索职位
- 抓取 JD
- 简历与岗位匹配评分
- 安全演练 / 正式投递
- 结构化日志记录

## 本次发布包含

### 核心能力

- 支持 `Boss直聘` 独立投递链路
- 支持 `实习僧` 独立投递链路
- 显式运行模式：
  - `rehearsal` 安全演练
  - `apply` 正式投递
- OpenAI 兼容格式的 LLM 接口预留
- 启发式评分兜底，未配置 LLM 时也可运行

### 架构特性

- 严格基于 `DrissionPage`
- 不使用 Playwright / Selenium 主动启动浏览器
- 平台适配器与入口调度解耦
- `Boss` 与 `实习僧` 分别使用独立端口和独立浏览器目录

### 工程化补全

- `pyproject.toml` / `requirements.txt`
- 可安装 CLI：
  - `job-hunter`
  - `job-hunter-boss`
  - `job-hunter-sxs`
  - `job-hunter-doctor`
- 自检脚本 `doctor.py`
- 基础单元测试
- GitHub CI
- Issue / PR 模板
- License / Contributing / Security / Code of Conduct

## 使用方式

安装：

```bash
python -m pip install -e .
```

自检：

```bash
job-hunter-doctor --json
```

Boss 安全演练：

```bash
job-hunter --platform boss --mode rehearsal --job "Java开发实习生" --city 北京 --count 1
```

实习僧 安全演练：

```bash
job-hunter --platform sxs --mode rehearsal --job "Java开发实习生" --city 北京 --count 1
```

## 当前限制

- 当前版本为 `alpha`
- 暂不支持 `51job`
- 真实站点 selector 未来可能发生变化
- 仍需用户手动登录目标平台
- 建议先始终使用 `rehearsal` 模式验证，再切换到 `apply`

## 适合谁

- 想基于真实浏览器会话做求职自动化的人
- 想扩展新的投递平台适配器的人
- 想把简历匹配、日志分析、自动化投递串起来的人

## 下一步计划

- 提高页面 selector 的稳健性
- 增加更多日志分析能力
- 增加更多平台适配器
- 补更多共享逻辑测试

欢迎试用、提 Issue、提 PR。

