# 项目指南

## 项目概览

紫金矿业(601899/02899)个股监控系统 MVP。提供 A 股、H 股实时行情、大宗商品价格（黄金/铜）、公司公告（巨潮资讯网）和基本面估值数据的可视化看板。

前端应用位于 `frontend/`，使用 React + Vite；后端 API 位于 `backend/`，使用 Python FastAPI；数据库为 SQLite（`backend/zijin_monitor.db`）。

## 架构

- `backend/` 是后端：Python 3.11、FastAPI、uvicorn、SQLite 存储、服务层（`services/`）和路由层（`routers/`）。
- `frontend/` 是前端：React 18、TypeScript、Vite、Ant Design 5、Axios。Vite 将 `/api` 代理到后端 `3001` 端口。
- `backend/zijin_monitor.db` 是 SQLite 数据库，存储行情缓存和公告数据。只有在任务确实需要调整种子数据或配置时才修改。
- 数据源为新浪财经 API（免费），无需 API Key。
- 前端 API 调用统一走 `/api`；Vite 代理到后端 `3001` 端口。

## 命令

在对应子项目目录下执行命令。前后端命令需要分别执行。

```bash
# 后端 (端口 3001)
cd backend
./venv/Scripts/python.exe main.py
```

```bash
# 前端 (端口 5173)
cd frontend
npm run dev
```

根目录 `start.bat` 可一键启动两个服务。两个项目可以同时运行，互不干扰。

## 后端约定

- 保持 Python 3.11 兼容，使用 FastAPI + uvicorn。
- 服务层放在 `backend/services/`：`stock_service.py`（A 股/H 股行情）、`commodity_service.py`（大宗商品）、`announcement_service.py`（公告）、`fundamental_service.py`（基本面）。
- 路由层放在 `backend/routers/`：`stock.py`、`commodity.py`、`announcement.py`、`fundamental.py`，分别对应 `main.py` 中的路由前缀。
- 数据库操作集中在 `backend/database.py`，使用 `aiosqlite` 异步驱动。
- 新增服务应沿用现有服务模式，保持服务层与路由层职责分离。
- API 响应结构应与现有路由保持一致。

## 前端约定

- 遵循现有 Ant Design 5 布局和组件风格。本系统是运营型看板，应优先采用信息密度高、便于扫读、面向工作的界面。
- 面板组件（`StockCard`、`CommodityCard`、`AnnouncementCard`、`FundamentalCard`）内联定义在 `frontend/src/App.tsx` 中。
- 主页面在 `frontend/src/App.tsx`。
- API 调用逻辑通过 Axios 直接调用，Vite 配置了 `/api` 代理。
- **颜色规则**：遵循中国市场惯例——红色（`#ff4d4f`）表示上涨，绿色（`#52c41a`）表示下跌。
- 暗色主题通过 Ant Design 的 ConfigProvider `dark` 算法配置。

## 数据与领域规则

- 金融数据应保持准确性：行情数据应注明来源和时间戳，公告数据应包含发布日期和标题。
- 不要把监控数据视为投资建议。本应用是分析辅助工具，不是交易推荐引擎。
- 新浪财经 API 为免费接口，遵守其使用条款，不要频繁请求。

## 验证

- 后端变更可通过 `cd backend && ./venv/Scripts/python.exe main.py` 启动验证。
- 前端变更可通过 `cd frontend && npm run dev` 启动验证。
- 如果因为依赖缺失或外部服务不可用而无法运行命令，需要清楚说明受影响的范围。
