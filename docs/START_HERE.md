# 3 分钟上手版

如果你第一次打开这个仓库，不用先读所有文件，按这 4 步就能开始：

1. 先看 [README.md](../README.md)
2. 再看 [config.example.json](../config.example.json) 和 [resume.example.md](../resume.example.md)
3. 打开浏览器，手动登录要用的平台
4. 运行 [skill_entry.py](../skill_entry.py)

## 你会看到什么

- 路人用户：先用安全演练，不会马上真实投递
- 开发者：先看入口、公共逻辑、平台适配器
- agent：先看 `CLAUDE.md`、`CODEBUDDY.md`、`TRAE.md`

## 你需要准备什么

- 一个 `resume.md`
- 一个 `config.json`
- 一个已经登录好的浏览器会话
- 至少一个可用平台：
  - Boss直聘
  - 实习僧

## 最常用的入口

```bash
python skill_entry.py
```

如果你已经安装成命令行工具，也可以：

```bash
job-hunter --platform boss --mode rehearsal --job "Java开发实习生" --city 北京 --count 1
```

## 看不懂代码时先看哪里

1. [README.md](../README.md)
2. [docs/REPO_MAP.md](./REPO_MAP.md)
3. [skill_entry.py](../skill_entry.py)
4. [shared.py](../shared.py)
