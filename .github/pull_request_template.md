## 变更摘要

- 这次 PR 改了什么？
- 为什么要改？

## 检查清单

- [ ] 我仍然使用 `DrissionPage`
- [ ] 我没有引入 Playwright 或 Selenium 主动启动浏览器
- [ ] 我在本地验证了相关逻辑
- [ ] 如果影响用户，我已经更新文档
- [ ] 我没有提交私有路径、密钥或日志

## 验证方式

```bash
python doctor.py --json
python -m unittest tests.test_core
python -m py_compile skill_entry.py shared.py boss_apply.py sxs_apply.py doctor.py tests/test_core.py
```

## 备注

- 选择器有什么假设：
- 真实站点可能有什么变化：

