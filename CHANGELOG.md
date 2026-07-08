# CHANGELOG

## v3.0.0 — 基础设施升级 (2026-07-02)

### 新增
- **PWA 支持** — 添加到手机桌面，离线缓存上次数据
  - `vite-plugin-pwa` 集成，Workbox 缓存策略
  - API 请求：Network-first（实时金融数据）
  - 静态资源：Cache-first（JS/CSS/字体）
  - PWA 图标（192x192, 512x512）
- **移动端适配** — 响应式布局优化，触控友好
  - 手机竖屏 (< 480px) 专用样式
  - 底部导航栏（移动端）
  - iPhone 安全区域支持（刘海屏/底部横条）
  - 触控反馈（点击缩放动画）
  - 最小点击区域 44px
- **Docker 部署** — 一键容器化部署
  - `backend/Dockerfile` — 多阶段构建（Node 20 + Python 3.11）
  - `docker-compose.yml` — 前端 nginx + 后端 FastAPI 编排
  - `nginx.conf` — 反向代理 + gzip + 静态资源缓存
  - `.dockerignore` — 构建优化
- **多股扩展** — 支持监控其他矿业股
  - `config/stocks/601899.yaml` — 紫金矿业配置外置
  - `services/stock_registry.py` — 股票注册表，替代全项目硬编码
  - 所有 router 默认参数改为 `config.DEFAULT_STOCK`
  - 基本面评分、护城河、LLM prompt 改为数据驱动
- **稳定性增强**
  - `core/http.py` — 指数退避 + 随机抖动重试策略
  - `core/circuit_breaker.py` — 断路器模式（连续失败熔断）
  - 结构化日志 — 55 个 `print()` 替换为 `logging`
- **ErrorBoundary** — 前端统一错误边界

### 改进
- `config.py` — 配置分层（Docker/本地模式，股票注册表，量化路径）
- `.env.example` — 补充 `DEPLOY_MODE`, `DEFAULT_STOCK`, `QUANT_DATA_PATH`
- `index.html` — PWA meta 标签（theme-color, apple-touch-icon, viewport-fit）
- `main.tsx` — 包裹 ErrorBoundary
- `requirements.txt` — 新增 `pyyaml>=6.0`

### 文件变更
- 新增：`core/circuit_breaker.py`, `services/stock_registry.py`, `config/stocks/601899.yaml`
- 新增：`backend/Dockerfile`, `docker-compose.yml`, `nginx.conf`, `.dockerignore`
- 新增：`frontend/src/components/ErrorBoundary.tsx`, `frontend/public/icons/`
- 修改：`core/http.py`, `config.py`, `main.py`, `vite.config.ts`, `index.html`, `main.tsx`, `App.css`
- 修改：9 个 router 文件（移除硬编码 stock code）
- 修改：5 个 service 文件（使用 StockRegistry 替代硬编码值）
- 修改：18 个文件（print → logging）

### 测试
- 总计 220 个测试全部通过
- 前端构建通过（951ms）
- PWA precache 14 entries (1656.58 KiB)

---

## v2.5.0 — 业务动向 (2026-07-02)

### 新增
- `db_business.py` — 5张新表（mine_info, production_plan, segment_finance, esg_data, price_sensitivity）
- `services/business_service.py` — 业务数据服务，10座全球矿山静态配置
- `routers/business.py` — 7个端点（mines, production, finance, esg, sensitivity, overview）
- `test_business_service.py` — 16个测试全部通过
- `frontend/src/components/MineMap.tsx` — SVG世界地图，矿山标注+悬浮提示+点击交互
- `frontend/src/components/ProductionCard.tsx` — 产量计划看板，金/铜/锌完成率进度条
- `frontend/src/components/SegmentFinance.tsx` — 板块财务表格，收入/毛利/EBITDA/C1成本
- `frontend/src/components/PriceSensitivity.tsx` — 价格敏感性模拟器，滑块交互+净利润预测
- `frontend/src/components/ESGDashboard.tsx` — ESG仪表盘，安全/环保/社会三维度
- `frontend/src/hooks/useBusiness.ts` — React Query hooks（useMines/useProduction/useSegmentFinance/useESG/usePriceSensitivity）

### 数据源
- 矿山信息：静态配置（10座全球矿山，含经纬度、权益比例、产品类型）
- 产量计划/板块财务/ESG/敏感性：DB持久化，支持年报PDF解析填充

### 测试
- 总计 220 个测试全部通过（+16 business_service）
- 前端构建通过（1.10s）

---

## v2.0.0 — 财报分析 (2026-07-02)

### 新增
- `db_report.py` — annual_report 表（stock_code, report_type, report_date, summary_llm, key_metrics, alert_flags）
- `services/report_service.py` — 财报抓取、解析、预警、LLM摘要（317行）
- `routers/report.py` — 4个端点（list/detail/comparison/alerts）
- `test_report_service.py` — 财报服务单元测试
- `frontend/src/components/ReportTimeline.tsx` — 财报时间线组件（垂直时间轴+展开详情）
- `frontend/src/components/ReportAlertCard.tsx` — 预警卡片（红/黄/绿三色）
- `frontend/src/hooks/useReport.ts` — React Query hooks（useReportList/useReportDetail/useReportAlerts）

### 数据源
- 东方财富定期报告 API（主）
- akshare 财务数据（辅）
- fundamental_service 兜底

### 预警规则
- 净利同比下滑 > 20%
- 毛利率同比变化 > 5pp
- ROE < 5%（连续两期）
- 营收同比下滑 > 15%
- EPS 连续两期下降

### LLM 摘要
- MiMo API 异步生成，不阻塞前端
- 摘要为空时显示"生成中..."
- Cron 每日 20:00 检查新财报

---

## v1.6.0 — 基础设施重构 (2026-06-29)

### 新增
- `backend/core/` 公共基础设施模块（utils/cache/http/db）
- `test_core_utils.py` — 29 个测试（safe_float/safe_int/is_trading_hours/apply_grace_period）
- `test_core_cache.py` — 45 个测试（CacheManager/TtlCacheManager/per-key TTL/淘汰策略）
- `test_core_http.py` — 14 个测试（get_session/get_sync/get_json_sync/重试/状态码检查）
- `test_core_db.py` — 12 个测试（Database/get_db/连接管理/事务清理）
- `.env.example` 环境变量模板

### 改进
- **缓存系统**：`CacheManager` 支持 per-key TTL（`set(key, data, ttl)`），`TtlCacheManager` 通过 `_resolve_ttl()` 正确解析优先级
- **HTTP 客户端**：`get_sync`/`get_json_sync` 新增 `check_status` 参数（默认 `True`），4xx/5xx 触发重试
- **safe_float**：支持逗号分隔数字（`"293,050,000,000"` → `293050000000.0`）
- **磁盘缓存**：`fundamental_service._get_valid_data` 检查 `saved_at + ttl` 过期
- **数据库注入**：`get_db()` 依赖注入增加 `finally` 块 rollback pending 事务
- **关联性分析**：`correlation_service` 增加 5 分钟内存缓存，避免前端轮询重复计算
- **公告服务**：移除冗余 `User-Agent` headers，复用全局 Session 配置
- **商品概览**：`/api/commodity/overview` 端点现在也保存数据到 DB（与单独端点行为一致）
- **stock_service**：`_get_sina` 改用 `core.http.get_sync`，统一重试逻辑
- **前端**：`queryClient` 支持 Page Visibility（后台标签页暂停轮询），`useStockOverview` 独立 15s 轮询

### 重构
- 5 个 service 层统一使用 `core.cache`/`core.http`/`core.utils`
- 4 个 db 层统一使用 `core.db.get_database()` 单例
- 3 个 router 层改用 `Depends(get_db)` 依赖注入
- `stock_service._get_cached`/`_set_cache` 使用 per-key TTL 标准接口，不再手动操作 `_store`
- `correlation_service` 假单例改为正常 class
- `main.py` version 升级至 `1.5.0`

### 修复
- **P0**：`CacheManager.set()` 的 `ttl` 参数被忽略（改为三元组存储 `(data, ts, ttl)`）
- **P0**：`TtlCacheManager._evict_expired` 使用 per-key ttl 淘汰（不再用 `default_ttl * 2`）
- **P1**：`safe_float` 不处理逗号分隔数字
- **P1**：`http` 模块不检查 HTTP 状态码
- **P1**：`fundamental_service` 磁盘缓存不检查 TTL
- **P1**：`get_db()` 依赖注入无 cleanup
- **P2**：`CacheManager.__contains__` 绕过 TTL 检查
- **P2**：`CacheManager.__getitem__`/`__setitem__` 绕过 TTL 检查

### 测试
- 总计 182 个测试全部通过（88 core + 83 service/db + 11 router）
- 前端构建通过（1.59s）

---

## v1.5.0 — 视觉升级 + 波动率恐慌指数 ✅

- COMEX 黄金波动率恐慌指数（SVG 环形仪表盘）
- 收盘变灰、数字动效、Stripe 级交互质感
- 中文排版优化（Noto Sans SC）
- README 全面更新

## v1.4.0 — 数据深度 + 基本面改版 ✅

- 基本面大改版（组合接口 + 盈利趋势并排双行图 + ROE/EPS）
- safe_float 中文单位支持
- 收盘兜底（PE/PB/市值用昨收兜底）

## v1.3.0 — 代码质量 + 维运 ✅

- 死代码清理（292 行）
- database.py 按 feature 拆分
- 94 个测试全部通过

## v1.2.0 — 关联性分析 ✅

- 商品关联分析（Pearson 相关系数）
- 量化因子关联分析
- 新浪全球期货备用通道

## v1.1.0 — 数据增强 ✅

- 股价历史K线图
- 基本面数据缓存
- 量化因子系统（73 因子 LightGBM）
- 前端组件拆分（8 个子组件）
