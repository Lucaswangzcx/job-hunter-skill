# 代码导航图

这个仓库的文件很多，但核心其实很少。第一次看时，建议按下面这个顺序。

## 先看入口

- [README.md](../README.md)：总说明和使用方法
- [CLAUDE.md](../CLAUDE.md)：给 Claude 系列 agent 的说明
- [CODEBUDDY.md](../CODEBUDDY.md)：给 CodeBuddy 的说明
- [TRAE.md](../TRAE.md)：给 Trae 的说明

## 再看执行链

- [skill_entry.py](../skill_entry.py)：总入口，负责接收参数、分发平台
- [shared.py](../shared.py)：公共能力，配置、日志、评分、浏览器接管、LLM
- [doctor.py](../doctor.py)：环境自检

## 平台适配器

- [boss_apply.py](../boss_apply.py)：Boss直聘投递逻辑
- [sxs_apply.py](../sxs_apply.py)：实习僧投递逻辑

## 示例与发布文件

- [config.example.json](../config.example.json)：配置示例
- [resume.example.md](../resume.example.md)：简历示例
- [requirements.txt](../requirements.txt)：依赖列表
- [pyproject.toml](../pyproject.toml)：包信息与命令入口
- [docs/GITHUB_RELEASE_v0.1.0.md](./GITHUB_RELEASE_v0.1.0.md)：发布说明
- [docs/GITHUB_REPO_COPY.md](./GITHUB_REPO_COPY.md)：仓库简介文案

## 开发与测试

- [tests/test_core.py](../tests/test_core.py)：核心测试
- [scripts/](../scripts/)：辅助脚本

## 运行时产物

这些文件不应该提交到 GitHub：

- `config.json`
- `resume.md`
- `job-hunter.log`
- `boss-*-log.json`
- `sxs-*-log.json`
- `.job_hunter/`
- `__pycache__/`

## 最短上手路径

1. 先看 `README.md`
2. 再看 `config.example.json`
3. 然后看 `skill_entry.py`
4. 最后分别看 `boss_apply.py` 和 `sxs_apply.py`
