# Hermes + Multica 集成指南

## 当前状态

- **Hermes**: v0.18.1, profile: luzi-3, model: mimo-v2.5-pro (xiaomi token plan)
- **Multica**: v0.3.40 桌面版, daemon 端口 19681
- **工作区**: 投资(e6870ec6), 项目: 紫金监视器(be0d5101)

## 已解决的坑

### 1. holographic memory provider 卡死
- **现象**: hermes ACP session/new 无限挂起, tools=0
- **根因**: luzi-3 profile 的 `memory.provider: holographic` 在 init_agent() 时尝试连接外部服务卡死
- **修复**: `~/.hermes/profiles/luzi-3/config.yaml` 中 `memory.provider` 改为 `''`

### 2. multica CLI 不在 PATH
- **现象**: mimocode 执行 `multica issue create` 时报 "command not found"
- **根因**: daemon 子进程继承的 PATH 不包含 multica CLI 路径
- **修复**: 复制 `multica.exe` 到 `%APPDATA%\npm\` (npm 全局目录一定在 PATH 中)

### 3. 大目录导致 hermes 卡死
- **现象**: hermes 在 50K+ 文件的目录里初始化时挂起
- **根因**: 紫金单股监控器目录含 node_modules(391MB) + venv(373MB), hermes 扫描 context 时卡死
- **修复**: 移除项目关联的 GitHub 仓库资源, 让 multica 用工作区目录(只含 AGENTS.md)
- **注意**: 仓库已移除, agent 通过 AGENTS.md 获取项目信息, 不直接访问源码

## 调试方法

daemon 日志: `~/.multica/profiles/desktop-api.multica.ai/daemon.log`
- hermes stderr 输出格式: `[hermes:stderr]`
- 在 agent_init.py 加 `print("DI: X.mark", file=sys.stderr, flush=True)` 可追踪卡死位置
- daemon 每次任务启动新的 hermes ACP 进程, 修改代码后需重启 multica

## 运行时对比

| 运行时 | 状态 | 特点 |
|--------|------|------|
| hermes | ✅ 可用 | 原生支持, 工具丰富, 需注意 profile 配置 |
| mimocode | ✅ 可用 | 命令 `mimo run`, 基于 opencode 协议, mimo-auto 免费 |
| OpenClaw | 未测试 | Claude Code 级别, 应该可用 |

## 注意事项

- hermes 使用 `~/.hermes/active_profile` 决定 profile, 当前为 luzi-3
- 每次 hermes 任务启动新进程, 不共享 TUI 的 session
- `HERMES_YOLO_MODE=1` 由 daemon 自动设置, agent 可直接执行命令
- multica workspace 数据存储在云端(api.multica.ai), 本地只存 daemon 配置
