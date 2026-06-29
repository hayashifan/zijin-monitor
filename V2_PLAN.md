# v2.0 财报分析 — 实现计划

## 核心思路

不造新轮子。复用已有 `fundamental_service` 的财务数据管线，新增"定期报告"维度。
LLM 摘要用 MiMo（已有 token plan），不引入新依赖。

## 阶段一：数据层（后端）

### 1.1 数据库 — 新增 `annual_report` 表

```sql
CREATE TABLE IF NOT EXISTS annual_report (
    stock_code TEXT NOT NULL,
    report_type TEXT NOT NULL,       -- 年报/半年报/季报
    report_date TEXT NOT NULL,       -- 2025-12-31
    title TEXT,
    pdf_url TEXT,                    -- 巨潮/东方财富 PDF 链接
    publish_date TEXT,               -- 实际发布日期 2026-04-29
    summary_llm TEXT,                -- LLM 摘要（可为空，后台填充）
    key_metrics TEXT,                -- JSON: {"revenue":..., "net_profit":..., ...}
    alert_flags TEXT,                -- JSON: ["净利下滑30%", "毛利率异常"]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (stock_code, report_date, report_type)
);
```

→ `db_report.py` + `db_base.py` 建表

### 1.2 服务层 — `services/report_service.py`

```
ReportService
├── fetch_report_list(stock_code)     # 东方财富定期报告列表
├── fetch_report_detail(art_code)     # 报告详情 + PDF链接
├── parse_key_metrics(report_text)    # 正则提取营收/净利/毛利率/ROE/EPS
├── generate_llm_summary(report_text) # MiMo 摘要（异步，后台队列）
├── detect_alerts(stock_code)         # 阈值预警检测
└── get_quarterly_comparison(stock_code, periods=8)  # 同比环比
```

**数据源优先级**：
1. 东方财富定期报告 API（`akshare.stock_report_fund_em`）
2. 巨潮资讯网（`cninfo.com.cn`）
3. 已有的 `fundamental_service.get_financial_summary` 兜底

**LLM 摘要流程**：
```
报告抓取 → 存 DB(summary_llm=null) → 后台 cron 触发 →
拼 prompt（营收/净利/毛利率/ROE/EPS 同比变化）→
MiMo API → 存 DB(summary_llm=text)
```

**预警规则**（硬编码，不引入规则引擎）：
- 净利同比下滑 > 20%
- 毛利率同比变化 > 5pp
- ROE < 5%（连续两期）
- 营收同比下滑 > 15%
- EPS 连续两期下降

### 1.3 路由层 — `routers/report.py`

| 接口 | 说明 |
|------|------|
| `GET /api/report/list?code=601899` | 定期报告列表 |
| `GET /api/report/detail?code=601899&date=2025-12-31` | 单期报告详情+LLM摘要 |
| `GET /api/report/comparison?code=601899&periods=8` | 季度同比环比 |
| `GET /api/report/alerts?code=601899` | 预警列表 |

→ `main.py` 注册路由

---

## 阶段二：前端展示

### 2.1 新增组件

| 组件 | 说明 |
|------|------|
| `ReportTimeline.tsx` | 财报时间线（垂直时间轴，每期一个节点） |
| `QuarterlyComparison.tsx` | 同比环比图表（ECharts 柱状图+折线） |
| `ReportAlertCard.tsx` | 预警卡片（红/黄/绿三色） |
| `ReportSummaryCard.tsx` | LLM 摘要卡片（Markdown 渲染） |

### 2.2 Hooks

```ts
// hooks/useReport.ts
useReportList(code)
useReportDetail(code, date)
useQuarterlyComparison(code, periods)
useReportAlerts(code)
```

### 2.3 集成到 App.tsx

```tsx
<div className="section-label">财报分析</div>
<Row gutter={[16,16]}>
  <Col xs={24} lg={12}><ReportAlertCard /></Col>
  <Col xs={24} lg={12}><QuarterlyComparison /></Col>
</Row>
<ReportTimeline />
<ReportSummaryCard />  {/* 懒加载，点击展开 */}
```

---

## 阶段三：LLM 摘要 + Cron

### 3.1 MiMo 摘要 Prompt

```
你是紫金矿业的财报分析助手。以下是{report_date}的{report_type}关键数据：

营收：{revenue}（同比 {revenue_yoy}%）
净利润：{net_profit}（同比 {profit_yoy}%）
毛利率：{gross_margin}%（同比变化 {margin_change}pp）
ROE：{roe}%
EPS：{eps}

请用 3-5 句话总结这份财报的核心变化，指出亮点和风险。
```

### 3.2 Cron 任务

```
每日 20:00 检查是否有新财报发布
→ 有新报告：抓取 → 解析 → 存 DB → 触发 LLM 摘要
→ 有预警：推送微信通知
```

---

## 执行顺序

```
1. db_report.py + db_base.py 建表
2. report_service.py（数据抓取 + 解析 + 预警）
3. routers/report.py
4. 测试（test_report_service.py + test_report_router.py）
5. hooks/useReport.ts
6. ReportTimeline + QuarterlyComparison + ReportAlertCard
7. App.tsx 集成
8. LLM 摘要（MiMo API）
9. Cron 任务
10. 构建验证
```

## 约束

- LLM 摘要是异步后台任务，不阻塞前端请求（摘要为空时显示"生成中..."）
- 财报数据源免费，不需要额外 API key
- MiMo 用已有的 token plan，不引入新模型
- 预警阈值硬编码，不做成可配置（v2.0 够用）
