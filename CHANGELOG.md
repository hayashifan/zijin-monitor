# CHANGELOG

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
