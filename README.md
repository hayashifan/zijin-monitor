# 紫金单股监控器

紫金矿业(601899/02899)个股监控系统 — 实时行情、大宗商品、技术指标、量化因子、关联性分析一站式看板

## ✨ 功能特性

### 行情 & K线
- **A股/H股双市场** — 601899 + 02899 实时行情，15秒自动刷新
- **K线走势图** — 新浪财经K线API，支持30/60/90日切换，MA5/MA10均线叠加
- **收盘变灰** — 非交易时段数据自动灰显，PE/PB/市值用昨收兜底

### 大宗商品
- **实时价格** — 国际金价(伦敦现货)、LME铜、沪铜，多源自动切换
- **历史K线** — 金价/铜价趋势图表，30/60/90日切换，东方财富+新浪双通道
- **COMEX黄金波动率恐慌指数** — SVG环形仪表盘，年化波动率→恐慌等级(平静/正常/偏高/恐慌/极端恐慌)，悬停展开

### 技术分析
- **技术指标** — MA、RSI、MACD、布林带，基于历史K线实时计算
- **量化因子** — 73因子(66技术+7舆情)LightGBM模型，IC衰减分析，回测夏普3.15
- **关联性分析** — 股价与金/铜Pearson相关系数，滚动相关性，归一化双轴折线

### 数据 & 公告
- **基本面数据** — PE/PB/市值/换手率/ROE/EPS，盈利趋势并排双行图，磁盘缓存兜底
- **公司公告** — 东方财富公告API，详情弹窗+PDF原文链接

### 交互 & 视觉
- **中国市场配色** — 红涨绿跌标准
- **数字动效** — 金色微光+颜色平滑过渡
- **Stripe级质感** — 多层阴影、物理按压、节奏控制
- **暗色主题** — CSS变量主题系统，一键切换
- **中文排版** — Noto Sans SC，优化字重/字距/行高
- **Page Visibility** — 切标签页自动暂停轮询，回来恢复

## 🚀 快速开始

### 前置条件

- Python 3.11+
- Node.js 18+

### 安装

```bash
git clone https://github.com/hayashifan/zijin-monitor.git
cd zijin-monitor

# 后端
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

### 启动

```bash
# 一键启动 (Windows)
双击 start.bat

# 或手动
cd backend && python main.py     # 终端1: 后端 :3002
cd frontend && npm run dev        # 终端2: 前端 :5174

# PM2 部署 (可选)
pm2 start ecosystem.config.cjs
```

访问 http://localhost:5174

## 📁 项目结构

```
├── backend/
│   ├── main.py                          # FastAPI 入口
│   ├── config.py                        # 环境变量配置
│   ├── database.py                      # DB facade (re-export)
│   ├── db_base.py                       # 建表 + 索引
│   ├── db_stock.py                      # 股票行情 CRUD
│   ├── db_commodity.py                  # 商品价格 CRUD
│   ├── db_announcement.py               # 公告 CRUD
│   ├── db_fundamental.py                # 基本面 CRUD
│   ├── services/
│   │   ├── stock_service.py             # 新浪 A股/H股行情
│   │   ├── commodity_service.py         # 大宗商品 (新浪+东方财富+全球期货)
│   │   ├── announcement_service.py      # 公告 (东方财富)
│   │   ├── fundamental_service.py       # 基本面 (akshare + 磁盘缓存)
│   │   ├── correlation_service.py       # 关联性分析 (Pearson)
│   │   └── technical_indicators_service.py  # 技术指标 (MA/RSI/MACD/布林带)
│   └── routers/
│       ├── stock.py                     # /api/stock/*
│       ├── commodity.py                 # /api/commodity/*
│       ├── announcement.py              # /api/announcement/*
│       ├── fundamental.py               # /api/fundamental/*
│       ├── quant.py                     # /api/quant/*
│       ├── correlation.py               # /api/correlation/*
│       └── technical_indicators.py      # /api/indicators/*
│
├── frontend/src/
│   ├── App.tsx                          # 主页面 (15s轮询)
│   ├── App.css                          # CSS变量主题系统
│   ├── types/index.ts                   # TypeScript 类型
│   ├── services/api.ts                  # Axios API 层
│   └── components/
│       ├── StockCard.tsx                # A股/H股行情卡片
│       ├── KlineChart.tsx               # 股价K线图 (MA5/MA10)
│       ├── CommodityCard.tsx            # 商品价格卡片
│       ├── CommodityHistoryChart.tsx     # 商品历史K线图
│       ├── GoldHoverCard.tsx            # 金价悬停→波动率展开
│       ├── GoldVolatilityCard.tsx       # COMEX波动率恐慌指数
│       ├── FundamentalCard.tsx          # 基本面+盈利趋势
│       ├── AnnouncementCard.tsx         # 公告列表+详情Modal
│       ├── QuantCard.tsx                # 量化分析报告
│       └── CorrelationCard.tsx          # 关联性分析
│
├── data/                                # 运行时数据 (gitignore)
├── ecosystem.config.cjs                 # PM2 部署配置
├── AGENTS.md                            # 开发指南
└── start.bat                            # 一键启动脚本
```

## 🔌 API 接口

| 接口 | 说明 |
|------|------|
| `GET /api/stock/realtime?code=601899&market=A` | A股实时行情 |
| `GET /api/stock/realtime?code=02899&market=HK` | H股实时行情 |
| `GET /api/stock/overview` | 股票概览 (A+H) |
| `GET /api/stock/history?code=601899&market=A&days=30` | 股价历史K线 |
| `GET /api/commodity/overview` | 大宗商品概览 |
| `GET /api/commodity/history?type=gold&days=30` | 商品历史K线 |
| `GET /api/commodity/volatility` | COMEX黄金波动率 |
| `GET /api/announcement/list?code=601899` | 公告列表 |
| `GET /api/fundamental/metrics?code=601899` | 估值指标+盈利趋势 |
| `GET /api/indicators?code=601899&days=120` | 技术指标 (MA/RSI/MACD/布林带) |
| `GET /api/quant/report` | 量化分析报告 |
| `GET /api/correlation/commodity` | 商品关联性分析 |
| `GET /api/correlation/quant` | 量化因子关联性 |
| `GET /health` | 健康检查 |

## 📊 数据源

| 数据 | 来源 | 备用 |
|------|------|------|
| A股/H股行情 | 新浪财经API | — |
| 大宗商品实时 | 东方财富 | 新浪全球期货 |
| 大宗商品历史K线 | 东方财富K线API | 新浪期货API |
| COMEX黄金历史 | 新浪全球期货 | — |
| 公告 | 东方财富公告API | — |
| 基本面 | akshare | 磁盘缓存 |
| 量化报告 | zijin-quant输出JSON | — |

## 🛠 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11 + FastAPI + aiosqlite + uvicorn |
| 前端 | React 18 + TypeScript + Ant Design 5 + ECharts + Vite |
| 量化 | 73因子 + LightGBM + Qlib模式 (独立仓库 zijin-quant) |
| 数据库 | SQLite (6张表，UPSERT) |
| 部署 | PM2 (可选) |
| 数据源 | 新浪财经/东方财富/akshare (免费，无需API Key) |

## ⚙️ 配置

```bash
PORT=3002                          # 后端端口
DATABASE_PATH=../data/zijin_monitor.db
CORS_ORIGIN=http://localhost:5174
SINA_API_TIMEOUT=10                # API超时(秒)
CACHE_TTL_SECONDS=300              # 缓存TTL(秒)
STOCK_CODES=A:601899,HK:02899     # 监控股票
BYPASS_SYSTEM_PROXY=True           # 绕过系统代理
```

## 🧪 测试

```bash
cd backend
python -m pytest -v                # 全量测试 (94个)
python -m pytest test_stock_service.py -v  # 单模块
```

## 📝 开发规范

详见 [AGENTS.md](./AGENTS.md)

## 📄 License

MIT
