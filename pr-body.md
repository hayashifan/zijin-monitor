## 改动

### feat: COMEX黄金波动率恐慌指数
- 后端 `get_gold_volatility()`：从东方财富COMEX金90天K线计算20日滚动对数收益率年化波动率
- 返回：当前波动率、历史百分位、恐慌等级(低/正常/偏高/恐慌/极端)、趋势方向、40天火花线数据
- 新端点 `GET /api/commodity/gold-volatility`，10分钟缓存
- 前端 `GoldVolatilityCard`：SVG环形仪表盘 + 恐慌标签 + 三列统计 + 迷你火花线
- 前端 `GoldHoverCard`：鼠标悬停黄金卡片时浮现波动率卡片，cubic-bezier弹簧回弹动效

### fix: A股收盘后不变灰
- `is_closed` 从依赖Sina API返回的price=0判断，改为基于交易时间判断（与港股逻辑统一）
- 15:00-15:30 grace period 仍显示当天涨跌，15:30后清零变灰

### fix: 商品Tab按钮文字不可见
- 选中状态按钮文字从 `val.color`（金色）改为 `#1a1a2e`（深色），修复金色字+金色背景冲突

## 测试
- [x] `/api/commodity/gold-volatility` 返回正确数据
- [x] 前端 hover 动效正常
- [x] A股收盘后卡片变灰 + 0.00%
- [x] 纽约金按钮文字可见
