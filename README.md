# 紫金单股监控器

紫金矿业(601899/02899)个股监控系统 — 实时行情、大宗商品、公告、基本面一站式看板

## ✨ 功能特性

- **股票行情**: A股 601899 + H股 02899 实时行情，15秒刷新
- **大宗商品**: 国际金价、LME铜、沪铜价格联动
- **公司公告**: 巨潮资讯网/东方财富公告抓取
- **基本面数据**: PE/PB/市值/换手率等关键指标
- **中国市场配色**: 红涨绿跌标准

## 🚀 快速开始

### 前置条件

- Python 3.11+
- Node.js 18+

### 安装

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/zijin-monitor.git
cd zijin-monitor

# 后端依赖
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env  # 复制配置文件

# 前端依赖
cd ../frontend
npm install
```

### 启动

```bash
# Windows一键启动
双击 start.bat

# 或手动启动
# 终端1: 后端
cd backend && python main.py

# 终端2: 前端
cd frontend && npm run dev
```

访问 http://localhost:5173

## 📁 项目结构

```
├── backend/                 # Python FastAPI 后端
│   ├── main.py              # 入口 (端口3001)
│   ├── config.py            # 配置管理
│   ├── database.py          # SQLite 操作
│   ├── services/            # 业务逻辑层
│   │   ├── stock_service.py       # 股票行情
│   │   ├── commodity_service.py   # 大宗商品
│   │   ├── announcement_service.py # 公告
│   │   └── fundamental_service.py  # 基本面
│   ├── routers/             # API 路由
│   ├── utils/               # 工具类
│   │   └── circuit_breaker.py # 熔断器
│   └── crawlers/            # 爬虫基类
├── frontend/                # React + Vite 前端
│   └── src/
│       ├── App.tsx          # 主页面
│       ├── services/api.ts  # API 客户端
│       └── types/           # TypeScript 类型
├── data/                    # 运行时数据 (git忽略)
├── assets/                  # 静态资源
├── ecosystem.config.cjs     # PM2 部署配置
├── AGENTS.md                # 开发指南
└── start.bat                # Windows 启动脚本
```

## 🔌 API 接口

| 接口 | 说明 |
|------|------|
| `GET /api/stock/realtime?code=601899&market=A` | A股实时行情 |
| `GET /api/stock/realtime?code=02899&market=HK` | H股实时行情 |
| `GET /api/stock/overview` | 股票概览 (A+H) |
| `GET /api/commodity/overview` | 大宗商品概览 |
| `GET /api/announcement/list?code=601899` | 公告列表 |
| `GET /api/fundamental/metrics?code=601899` | 估值指标 |
| `GET /health` | 健康检查 |

## ⚙️ 配置

复制 `backend/.env.example` 为 `backend/.env`：

```bash
PORT=3001                    # 后端端口
DATABASE_PATH=../data/zijin_monitor.db  # 数据库路径
CORS_ORIGIN=http://localhost:5173       # 前端地址
SINA_API_TIMEOUT=10          # API超时(秒)
CACHE_TTL_SECONDS=300        # 缓存TTL(秒)
STOCK_CODES=A:601899,HK:02899  # 监控股票
BYPASS_SYSTEM_PROXY=True     # 绕过系统代理
```

## 🛠 技术栈

- **后端**: Python 3.11 + FastAPI + aiosqlite
- **前端**: React 18 + TypeScript + Ant Design 5 + Vite
- **数据源**: 新浪财经API (免费，无需API Key)
- **部署**: PM2 (可选)

## 📝 开发规范

详见 [AGENTS.md](./AGENTS.md)

## 📄 License

MIT
