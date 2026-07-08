# 项目指南

## 项目概览

紫金矿业(601899/02899)个股监控系统。提供 A 股/H 股实时行情、大宗商品价格（黄金/铜）、公司公告、基本面估值、量化因子分析、股价与商品/量化关联性分析的可视化看板。

- **前端**：`frontend/` — React 18 + TypeScript + Vite + Ant Design 5 + ECharts
- **后端**：`backend/` — Python 3.11 + FastAPI + uvicorn + aiosqlite
- **数据库**：`data/zijin_monitor.db` — SQLite，6 张表
- **PM2**：`ecosystem.config.cjs` — zijin-web(5174) + zijin-server(3002)

## 架构

```
backend/
├── main.py                  # FastAPI 入口，注册 6 个路由
├── config.py                # 环境变量配置
├── database.py              # DB facade（re-export 子模块）
├── db_base.py               # DB 路径 + init_db（建表 + 索引）
├── db_stock.py              # stock_realtime / stock_history CRUD
├── db_commodity.py           # commodity_price / commodity_history CRUD
├── db_announcement.py        # announcement CRUD
├── db_fundamental.py         # company_fundamental CRUD
├── services/                # 服务层：数据获取 + 缓存 + 业务逻辑
│   ├── stock_service.py         # 新浪 A 股/H 股行情
│   ├── commodity_service.py     # 大宗商品（新浪 + 东方财富 + 新浪全球期货）
│   ├── announcement_service.py  # 公告（东方财富 API）
│   ├── fundamental_service.py   # 基本面（akshare + 磁盘缓存）
│   └── correlation_service.py   # 关联性分析（Pearson + 归一化 + 滚动相关）
├── routers/                 # 路由层：HTTP 契约 + 参数校验
│   ├── stock.py                 # /api/stock/*
│   ├── commodity.py             # /api/commodity/*
│   ├── announcement.py          # /api/announcement/*
│   ├── fundamental.py           # /api/fundamental/*
│   ├── quant.py                 # /api/quant/*（读 zijin-quant 报告 JSON）
│   └── correlation.py           # /api/correlation/*
└── test_*.py                # 94 个单元测试

frontend/src/
├── App.tsx                  # 主页面（219行，10 个 state，15s 轮询）
├── App.css                  # 全局样式 + CSS 变量主题系统
├── types/index.ts           # TypeScript 类型定义
├── services/api.ts          # Axios API 层（按模块分组）
└── components/              # 8 个独立组件
    ├── StockCard.tsx            # A 股/H 股行情卡片
    ├── CommodityCard.tsx        # 商品价格卡片（含更新时间戳）
    ├── CommodityHistoryChart.tsx # 商品历史K线图
    ├── AnnouncementCard.tsx     # 公告列表 + 详情 Modal
    ├── FundamentalCard.tsx      # 基本面指标 + 盈利趋势
    ├── KlineChart.tsx           # 股价K线图（MA5/MA10）
    ├── QuantCard.tsx            # 量化分析报告卡片
    └── CorrelationCard.tsx      # 关联性分析（商品 + 量化因子）
```

## 命令

```bash
# 后端 (端口 3002)
cd backend
./venv/Scripts/python.exe main.py

# 前端 (端口 5174)
cd frontend
npm run dev

# 一键启动
start.bat

# PM2 管理
pm2 start ecosystem.config.cjs
pm2 restart zijin-server   # 后端改动后
pm2 restart zijin-web      # 前端改动后（HMR 通常不需要）

# 测试
cd backend
./venv/Scripts/python.exe -m pytest -v
```

## 后端约定

- Python 3.11 兼容，FastAPI + uvicorn。
- **服务层**（`services/`）：数据获取 + 缓存 + 业务逻辑，不直接处理 HTTP。
- **路由层**（`routers/`）：HTTP 契约 + 参数校验 + 响应格式，不包含业务逻辑。
- **数据库**（`db_*.py`）：按 feature 拆分，`database.py` 为 facade 统一 re-export。
- API 响应格式统一：`{"success": true, "data": ...}` 或 `{"success": false, "message": "..."}`
- 新增模块：service → router → main.py 注册路由 → 前端 API → 组件 → App.tsx 集成

## 数据源

| 数据 | 来源 | 备用 |
|------|------|------|
| A 股/H 股行情 | 新浪财经 API | — |
| 大宗商品实时价 | 新浪财经 API（沪铜）/ 东方财富（金/铜） | 新浪全球期货（金/铜 fallback） |
| 大宗商品历史K线 | 东方财富 K 线 API（金/铜）/ 新浪期货 API（沪铜） | 新浪全球期货（金/铜 fallback） |
| 公告 | 东方财富公告 API | — |
| 基本面 | akshare（财务/估值/盈利） | 磁盘缓存兜底 |
| 量化报告 | ~/zijin-quant/data/report_*.json | — |
| 量化因子 | ~/zijin-quant/data/synthetic_factors.csv | — |

## 前端约定

- Ant Design 5 布局 + 自定义 CSS 变量主题系统（暗色/亮色）。
- 组件独立文件，`React.memo` 优化，`useValueFlash` 价格闪烁 hook。
- **颜色规则**：中国市场惯例 — 红色（`#ff4d4f`）上涨，绿色（`#52c41a`）下跌。
- 15s 轮询 + Page Visibility API（切标签页暂停/恢复）。
- 商品历史图表 / 关联性图表按需加载（不参与 15s 轮询）。

## 数据库表

| 表名 | 模块 | 说明 |
|------|------|------|
| stock_realtime | db_stock | A 股/H 股实时行情（UPSERT by code+market） |
| stock_history | db_stock | 股价历史K线（UPSERT by code+date） |
| commodity_price | db_commodity | 商品实时价格（UPSERT by type） |
| commodity_history | db_commodity | 商品历史K线（UPSERT by type+date） |
| announcement | db_announcement | 公告列表（INSERT IGNORE by code+url） |
| company_fundamental | db_fundamental | 基本面财务数据（UPSERT by code+date） |

## 测试

```bash
cd backend
./venv/Scripts/python.exe -m pytest -v              # 全量
./venv/Scripts/python.exe -m pytest test_stock_service.py -v  # 单模块
```

测试文件按 `test_{module}_service.py` / `test_{module}.py` 命名。mock 外部 API，不依赖网络。

## CI/CD

### 流水线

`.github/workflows/ci.yml` 定义了两个并行 job：

| Job | 检查项 | 目录 |
|-----|--------|------|
| backend-tests | `pytest -v --tb=short` | `backend/` |
| frontend-build | `npm ci && npm run build` | `frontend/` |

**触发条件**：push 到 main/master 或 PR 目标为 main/master。

### 本地验证

提交前必须通过：

```bash
# 后端测试
cd backend && ./venv/Scripts/python.exe -m pytest -v --tb=short

# 前端构建
cd frontend && npm run build
```

### 质量门禁

- pytest 全量通过（不允许有 failed）
- 前端 build 成功
- **CI 红了不允许合并**

### 测试覆盖率基线

当前：190 passed / 14 failed（commodity_history 相关测试需要 DB migration 修复）。
目标：0 failed，新增代码必须带测试。

## 外部依赖

- **zijin-quant**：量化因子系统，输出报告 JSON 和 CSV 到 `~/zijin-quant/data/`。quant router 和 correlation service 读取这些文件。
- **PM2**：进程管理，`ecosystem.config.cjs` 定义两个服务。

## 注意事项

- 金融数据仅供参考，不是投资建议。
- 新浪/东方财富为免费接口，遵守使用条款，不要频繁请求。
- SQLite 写操作串行，高并发场景需注意。
