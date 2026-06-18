# 紫金单股监控器 - 项目提交材料

---

## 1. 项目名称

紫金单股监控器

## 2. 项目简介

紫金矿业(601899/02899)个股实时监控系统，集成A股/H股行情、大宗商品价格联动、公司公告抓取和基本面数据分析的一站式金融看板。

## 3. 项目类型

选择：**工具软件** 或 **金融科技**

## 4. 项目版本

1.0.0

## 5. 项目说明（详细版）

```markdown
# 紫金单股监控器

## 项目简介

紫金单股监控器是一款专注于紫金矿业(601899.SH / 02899.HK)的个股监控系统。通过实时行情展示、大宗商品价格联动、公司公告自动抓取和基本面数据可视化，为投资者提供全面、及时的决策参考信息。

## 核心功能

### 1. 实时行情监控
- A股(601899)和H股(02899)双市场实时行情
- 15秒自动刷新，价格变化动画提示
- 红涨绿跌中国市场标准配色
- 展示今开/最高/最低/昨收/成交量/成交额

### 2. 大宗商品联动
- 国际金价(COMEX黄金期货)
- LME铜价 / 沪铜价格
- 与紫金矿业主营业务高度相关的商品价格监控
- 双数据源自动切换(新浪财经 + 东方财富)

### 3. 公司公告
- 自动抓取巨潮资讯网/东方财富公告数据
- 支持按类型分类(董事会决议、定期报告等)
- 10分钟缓存，降低API调用频率

### 4. 基本面数据
- 市盈率(PE)、市净率(PB)
- 总市值/流通市值
- 换手率/量比

## 技术架构

```
前端 (React + TypeScript + Ant Design 5)
    ↓ /api 代理
后端 (Python FastAPI + aiosqlite)
    ↓
数据源 (新浪财经API + 东方财富API)
    ↓
SQLite 本地存储
```

### 后端设计
- **服务层分离**: stock_service / commodity_service / announcement_service / fundamental_service
- **熔断器模式**: 连续失败自动暂停，避免无效重试
- **多源容灾**: 主数据源失败自动切换备选源
- **实例级缓存**: 减少外部API调用，提升响应速度

### 前端设计
- React 18 + TypeScript + Vite 构建
- Ant Design 5 暗色主题
- 响应式布局，支持移动端
- 矢量SVG图标，零图片依赖

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18, TypeScript, Ant Design 5, Vite |
| 后端 | Python 3.11, FastAPI, aiosqlite |
| 数据源 | 新浪财经API, 东方财富API |
| 部署 | PM2 (可选) |

## 项目特色

1. **零成本运行**: 使用免费公开API，无需申请API Key
2. **配置化管理**: .env文件统一管理端口、路径、超时等参数
3. **模块化架构**: 服务层/路由层/存储层职责清晰，易于扩展
4. **中国市场适配**: 红涨绿跌配色、中文界面、A股/H股双市场支持
5. **开发规范完善**: AGENTS.md文档、.gitignore、PM2部署配置一应俱全

## 安装与使用

### 环境要求
- Python 3.11+
- Node.js 18+

### 快速启动
```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/zijin-monitor.git
cd zijin-monitor

# 安装后端依赖
cd backend
pip install -r requirements.txt
cp .env.example .env

# 安装前端依赖
cd ../frontend
npm install

# 启动 (Windows)
cd .. && start.bat
```

### API接口
- GET /api/stock/overview - 股票概览(A+H)
- GET /api/commodity/overview - 大宗商品概览
- GET /api/announcement/list - 公告列表
- GET /api/fundamental/metrics - 估值指标
- GET /health - 健康检查

## 未来规划

1. 财报数据集成与自动分析
2. 股价与商品价格相关性图表
3. 历史行情K线图
4. 移动端适配优化
5. Docker容器化部署
```

---

## 提交清单

- [x] 项目名称: 紫金单股监控器
- [x] 项目简介: 已准备
- [x] 项目类型: 工具软件/金融科技
- [x] 项目版本: 1.0.0
- [x] GitHub链接: 待推送后填写
- [x] 项目说明: 已准备(上方详细版)
