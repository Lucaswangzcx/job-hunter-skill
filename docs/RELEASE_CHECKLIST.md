# 发布检查清单

在发新版本之前，建议先把下面这些检查一遍。

## 仓库卫生

- [ ] 确认 `config.json`、`resume.md`、`job-hunter.log`、`*-log.json` 和 `.job_hunter/` 没有提交
- [ ] 确认文档里没有私有密钥或个人绝对路径
- [ ] 确认 `README.md`、`CHANGELOG.md` 和 `LICENSE` 都存在
- [ ] 确认 `pyproject.toml` 里的版本号和你准备发布的 tag 一致

## 验证

- [ ] `python doctor.py --json`
- [ ] `python -m unittest tests.test_core`
- [ ] `python -m py_compile skill_entry.py shared.py boss_apply.py sxs_apply.py doctor.py tests/test_core.py`
- [ ] 可选：`python -m pip install -e .`

## 手动抽查

- [ ] Boss 演练跑通
- [ ] 实习僧演练跑通
- [ ] 如果要看真实效果，务必只在你明确授权的目标上测试

## GitHub 配置

- [ ] 如果还没有仓库，先创建一个空仓库
- [ ] 推送默认分支
- [ ] 按需开启 Issues 和 Discussions
- [ ] 检查 GitHub 的仓库简介和 Topics

## Tag 和 Release

- [ ] 提交所有发布文件
- [ ] 创建 tag，比如 `v0.1.0`
- [ ] 根据 `CHANGELOG.md` 写 GitHub Release Notes
