# 紫金单股监控器 v1.5 → v1.6 重构计划

## 阶段一：后端基础设施

### 1.1 创建 `backend/core/` 目录

```
backend/core/
├── __init__.py
├── http.py      # 统一 HTTP 客户端
├── cache.py     # 统一内存缓存
├── db.py        # 连接池 + 依赖注入
└── utils.py     # safe_float、grace_period 等公共函数
```

### 1.2 `core/http.py` — 统一 HTTP 客户端

- 创建共享 `requests.Session`，统一 UA/Referer/trust_env
- 提供 `get_sync(url, timeout, encoding)` 和 `get_json_sync(url, params, timeout)`
- 内置重试逻辑（可配置 max_retries）
- 所有 service 改用这个共享 session，不再各自创建

### 1.3 `core/cache.py` — 统一内存缓存

- `CacheManager` 类：`get(key)`, `set(key, data, ttl)`, `get_or_set(key, fn, ttl)`
- 支持 per-key TTL
- 自动过期淘汰（超过 max_size 时清理过期条目）
- 替代 stock_service._cache、commodity_service._cache、fundamental_service._memory_cache 三处

### 1.4 `core/db.py` — 连接池 + 依赖注入

- `Database` 类：lifespan 期间维护 aiosqlite 连接
- `get_db()` 依赖注入函数（FastAPI Depends 用）
- `execute(sql, params)`, `fetchone(sql, params)`, `fetchall(sql, params)`, `commit()`
- 替代 db_stock/db_commodity/db_announcement/db_fundamental 中每个函数自己 connect/close

### 1.5 `core/utils.py` — 公共函数

- `safe_float(val, default=0.0)` — 统一版，支持 %、亿、万
- `safe_int(val, default=0)`
- `is_trading_hours(market='A')` — A股/港股交易时间判断
- `apply_grace_period(change, change_pct, is_closed, market)` — 收盘后 grace period

### 1.6 改造现有 service

- `stock_service.py`：移除自建 Session、_cache、_safe_float、_is_trading_hours，改用 core 模块
- `commodity_service.py`：同上，移除 _ttl dict、_get_sina_sync 重试逻辑（http.py 已有）
- `fundamental_service.py`：同上，保留磁盘缓存层（内存层用 core/cache.py）
- `correlation_service.py`：删除假单例，改成正常 class

### 1.7 改造 db 层

- `db_base.py`：保留建表逻辑，但 init_db 改用 core/db.py 的连接
- `db_stock.py`、`db_commodity.py`、`db_announcement.py`、`db_fundamental.py`：
  所有函数改为接收 `db` 参数（由依赖注入传入），不再自己 connect

### 1.8 改造 router 层

- 所有 router 的 endpoint 改用 `db: aiosqlite.Connection = Depends(get_db)` 依赖注入
- quant router 的同步文件 I/O 包一层 `asyncio.to_thread`

### 1.9 main.py

- version 改为 "1.5.0"
- lifespan 中初始化 db 连接池
- 创建 `.env.example`

### 1.10 测试

- 94 个现有测试全部通过
- 为 core/ 新增单元测试

---

## 阶段二：前端状态管理

### 2.1 安装依赖

```bash
cd frontend && npm install @tanstack/react-query
```

### 2.2 创建 hooks

```
frontend/src/hooks/
├── useStock.ts        # useQuery 包装 stockAPI
├── useCommodity.ts    # useQuery 包装 commodityAPI
├── useAnnouncement.ts # useQuery 包装 announcementAPI
├── useFundamental.ts  # useQuery 包装 fundamentalAPI
├── useQuant.ts        # useQuery 包装 quantAPI
├── useTechnical.ts    # useQuery 包装 technicalAPI
└── useCorrelation.ts  # useQuery 包装 correlationAPI
```

每个 hook：
- `useXxx()` 返回 `{ data, isLoading, error, refetch }`
- 配置 `refetchInterval: 15000`（交易时段）
- 配置 `staleTime`、`gcTime`
- Page Visibility 自动暂停（React Query 内置）

### 2.3 改造 App.tsx

改造前（当前）：
- 10 个 useState
- 1 个 Promise.allSettled 搞 8 个 API
- 手动 setInterval 15s
- 手动 Page Visibility 管理
- 手动 flash state

改造后：
- QueryClientProvider 包裹根组件
- 每个数据块用对应的 useXxx() hook
- 轮询、缓存、visibility 全交给 React Query
- Flash state 保留（这是 UI 逻辑，不属于数据获取）

### 2.4 创建 QueryClient 配置

```ts
// src/queryClient.ts
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchInterval: 15000,
      retry: 2,
      staleTime: 10000,
    },
  },
});
```

### 2.5 主题切换保留

theme state 不属于服务端数据，留在 App.tsx 或用 useContext。

---

## 执行顺序

1. core/http.py + core/utils.py（无依赖，最先做）
2. core/cache.py
3. core/db.py
4. 改造 service 层（stock → commodity → fundamental → correlation → announcement）
5. 改造 db 层
6. 改造 router 层
7. main.py + .env.example
8. 跑测试
9. 前端 npm install @tanstack/react-query
10. 创建 hooks/
11. 改造 App.tsx
12. 前端构建验证
