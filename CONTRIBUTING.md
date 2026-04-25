# 贡献指南

感谢你愿意一起完善 `Job Hunter Skill`。

## 提交 PR 之前

1. 请保持浏览器自动化栈为 `DrissionPage`。
2. 不要把运行方式改成 Playwright 或 Selenium 主动拉起浏览器。
3. 新平台尽量做成独立适配器，不要把平台逻辑继续堆进入口脚本。
4. 默认行为请尽量保持安全，`rehearsal` 仍然建议作为默认模式。

## 本地准备

```bash
python -m pip install -e .
python doctor.py --json
python -m unittest tests.test_core
```

## 适配器规范

- 新平台请新建 `<platform>_apply.py`
- 统一暴露 `apply_jobs(task, config, browser, skill_dir)`
- 配置、浏览器接管、日志、评分逻辑尽量复用 `shared.py`
- 不要硬编码某一台电脑上的绝对路径
- 不要默认自动填写平台表单，除非这个行为已经明确说明

## 选择器修改

- 尽量使用稳定 class 片段和文本关键字
- 网站有多个布局时保留 fallback
- 如果 selector 是从真实页面上调出来的，建议在 PR 里说明场景

## 测试

- 共享逻辑有变化时，请补充或更新单元测试
- 测试要尽量独立、可重复，不依赖真实登录状态
- CI 里不要依赖登录后的浏览器会话

