# Multica 开发工作交接文档

## 一、环境配置

### Hermes Agent
- 版本: v0.18.1
- Profile: `luzi-3` (`~/.hermes/profiles/luzi-3/`)
- Model: `mimo-v2.5-pro` (xiaomi token plan, 免费)
- API: `https://token-plan-cn.xiaomimimo.com/v1`
- Key: `tp-cv951zxwvivxllye2usg8jh8vhkkl75uui98e7wutlulc5ak`

### Multica
- 版本: v0.3.40 桌面版
- Daemon: `http://localhost:19681`
- 工作区: 投资(e6870ec6)
- GitHub: hayashifan

### 已知坑
1. **holographic memory provider**: luzi-3 profile 曾配置 `memory.provider: holographic`, 导致 ACP 初始化卡死。已改为空串。
2. **PATH 问题**: multica CLI 必须在 npm 全局目录(`%APPDATA%\npm\`)才能被 daemon 子进程找到。
3. **大目录卡死**: 50K+ 文件的目录会导致 hermes 初始化挂起。已移除项目仓库资源解决。

---

## 二、会话索引

### 成功的会话

| Task ID | 目标 | 耗时 | 工具调用 | 说明 |
|---------|------|------|---------|------|
| f897560b | 紫金监视器 issue | 9m40s | 23 | 首次成功执行, 使用工作区目录 |
| 8b161980 | 紫金监视器 issue | 5m20s | 36 | 梳理开发现状 |
| d22c0f44 | 紫金监视器 issue | 3m27s | 23 | 后续任务 |
| a63ee3ed | 紫金监视器 issue | 1m20s | 9 | 快速任务 |
| 4bb24295 | 聊天测试 | 1m1s | 4 | 直接对话测试 |
| e35cfff9 | quick-create | 1m46s | 10 | mimocode 创建 issue |
| 3e1a79d4 | 聊天 | 14s | 1 | 简单对话 |
| 7c05810a | 聊天 | 19s | 1 | 简单对话 |

### 失败的会话

| Task ID | 耗时 | 错误 | 原因 |
|---------|------|------|------|
| 68829afe | 26m42s | session/prompt failed | 紫金单股监控器目录 50K 文件卡死 |
| dc608666 | 9s | cancelled | holographic provider 卡死(已修) |
| 1669fcd8 | 11s | completed, tools=0 | mimocode PATH 问题(已修) |

---

## 三、Multica Issues

| ID | 标题 | 状态 | 说明 |
|----|------|------|------|
| TZ-6 | 梳理清楚紫金监视器开发现状 | in_review | hermes 执行中 |
| TZ-5 | 根据 multica-agents.md 拆解并创建6个投资工作区智能体 | done | 已完成 |
| TZ-3 | 测试 | done | 测试任务 |
| TZ-2 | 接入 Multica：整理 Agent 技能清单与擅长领域 | done | 已完成 |
| TZ-7 | 测试新建issue功能 | cancelled | 测试 |
| TZ-1 | mimocode测试issue | cancelled | 测试 |

---

## 四、紫金监视器项目信息

### 项目结构
- 前端: React 18 + TypeScript + Vite + Ant Design 5 + ECharts (端口 5174)
- 后端: Python 3.11 + FastAPI + uvicorn + aiosqlite (端口 3002)
- 数据库: SQLite (`data/zijin_monitor.db`), 6 张表
- PM2: `ecosystem.config.cjs`

### 数据源
- A 股/H 股行情: 新浪财经 API
- 大宗商品: 新浪财经 + 东方财富
- 公告: 东方财富公告 API
- 基本面: akshare
- 量化报告: `~/zijin-quant/data/`

### 开发规范
- 后端: service → router → main.py 注册路由 → 前端 API → 组件 → App.tsx
- 前端: Ant Design 5 + CSS 变量主题, 红涨绿跌
- 测试: `cd backend && ./venv/Scripts/python.exe -m pytest -v`

---

## 五、注意事项

1. hermes 每次任务启动新进程, 不共享 TUI session
2. multica workspace 数据在云端, 本地只存 daemon 配置
3. daemon 日志: `~/.multica/profiles/desktop-api.multica.ai/daemon.log`
4. 修改 hermes 代码后需重启 multica 才能生效
5. 紫金单股监控器目录已移除仓库资源, agent 通过 AGENTS.md 获取项目信息
