export interface StockQuote {
  code: string;
  market: 'A' | 'HK';
  name: string;
  market_label?: string;  // SH / SZ / HK
  price: number;
  change: number;
  change_percent: number;
  open: number;
  high: number;
  low: number;
  pre_close: number;
  volume: number;
  amount: number;
  turnover_rate: number;
  pe_ratio: number;
  pb_ratio: number;
  is_closed?: boolean;  // 非交易时间标记
}

export interface CommodityPrice {
  type: 'gold' | 'copper_lme' | 'copper_shfe';
  name: string;
  price: number;
  currency: string;
  change: number;
  change_percent: number;
  timestamp?: string;
}

export interface Announcement {
  id: string;
  title: string;
  publish_date: string;
  url: string;
  source: string;
  category: string;
}

export interface FinancialData {
  report_date: string;
  report_type: string;
  revenue: number;
  net_profit: number;
  gross_margin: number;
  net_margin: number;
  roe: number;
  eps: number;
  bvps: number;
}

export interface KeyMetrics {
  pe_ratio: number;
  pb_ratio: number;
  total_market_cap: number;
  circulating_market_cap: number;
  turnover_rate: number;
  volume_ratio?: number;
  roe?: number;
  eps?: number;
  bvps?: number;
  gross_margin?: number;
  net_margin?: number;
  report_date?: string;
}

export interface ProfitTrendItem {
  report_date: string;
  revenue: number;
  net_profit: number;
  total_profit: number;
}

export interface FinancialOverview {
  stock_code: string;
  company_name: string;
  metrics: KeyMetrics | null;
  financial_summary: FinancialData[];
  profit_trend: ProfitTrendItem[];
  from_cache: boolean;
}

export interface StockOverview {
  a_share: StockQuote | null;
  hk_share: StockQuote | null;
}

export interface CommodityOverview {
  gold: CommodityPrice | null;
  copper_lme: CommodityPrice | null;
  copper_shfe: CommodityPrice | null;
}

export interface QuantReport {
  timestamp: string;
  model: string;
  data_points: number;
  total_factors: number;
  valid_factors: number;
  top_factors: string[];
  cross_validation?: {
    accuracies: number[];
    mean_accuracy: number;
    mean_auc: number;
    confidence: number;
  };
  walk_forward?: {
    n_windows: number;
    n_oos_samples: number;
    oos_accuracy: number;
    oos_auc: number;
    oos_sharpe: number;
  };
  backtest: {
    sharpe_ratio: number;
    strategy_annual_return: number;
    benchmark_annual_return: number;
    max_drawdown: number;
    win_rate: number;
    profit_loss_ratio: number;
    information_ratio: number;
    n_trades: number;
    n_days?: number;
    holding_ratio: number;
    transaction_cost?: number;
    max_holding_days?: number;
  };
  validation_checks: Record<string, boolean>;
  all_passed: boolean;
}

// ── 关联性分析 ──────────────────────────────

export interface CorrelationDataPoint {
  date: string;
  stock_close: number;
  commodity_close: number;
  stock_normalized: number;
  commodity_normalized: number;
}

export interface CommodityCorrelationItem {
  correlation: number;
  p_value: number;
  data_points: number;
  data: CorrelationDataPoint[];
  rolling_correlation: { date: string; r: number }[];
}

export type CommodityCorrelationMap = Record<string, CommodityCorrelationItem>;

export interface QuantCorrelationData {
  factor_correlations: Record<string, { correlation: number; p_value: number }>;
  backtest_summary: {
    sharpe_ratio: number;
    win_rate: number;
    strategy_annual_return: number;
    benchmark_annual_return: number;
    max_drawdown: number;
    n_trades: number;
    n_days: number;
    mean_accuracy: number;
    mean_auc: number;
    top_factors: string[];
    feature_importance: Record<string, number>;
    timestamp: string;
  } | null;
  data_points: number;
  stock_normalized: number[];
  daily_signals: { date: string; close: number; pct_change: number; factors?: Record<string, number> }[];
}

// ── 技术指标 ──────────────────────────────

export interface GoldVolatility {
  volatility: number;
  percentile: number;
  panic_level: 'low' | 'normal' | 'elevated' | 'high' | 'extreme';
  window: number;
  annualized_vol: number;
  trend: 'rising' | 'falling' | 'stable';
  data_points: number;
  sparkline: number[];
}

export interface IndicatorDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ma5: number | null;
  ma10: number | null;
  ma20: number | null;
  ma60: number | null;
  rsi14: number | null;
  dif: number | null;
  dea: number | null;
  macd: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
}

export interface IndicatorSignals {
  ma_alignment?: 'bullish' | 'bearish' | 'mixed';
  rsi?: 'oversold' | 'overbought' | 'neutral';
  macd?: 'golden_cross' | 'death_cross' | 'bullish' | 'bearish';
  bollinger?: 'below_lower' | 'above_upper' | 'near_lower' | 'near_upper' | 'middle';
  bollinger_position?: number;
  price_vs_ma5?: 'above' | 'below';
  price_vs_ma20?: 'above' | 'below';
}

export interface TechnicalIndicators {
  data: IndicatorDataPoint[];
  latest: IndicatorDataPoint;
  signals: IndicatorSignals;
}

// ── 定期报告 v2.0 ──────────────────────────────

export interface AnnualReport {
  stock_code: string;
  report_type: string;      // 年报/半年报/Q1季报/Q3季报
  report_date: string;      // 2024-12-31
  title: string;
  pdf_url: string;
  publish_date: string;     // 实际发布日期
  summary_llm: string | null;
  key_metrics: Record<string, number> | null;
  alert_flags: string[] | null;
}

export interface QuarterlyComparisonItem {
  report_date: string;
  revenue: number;
  net_profit: number;
  total_profit: number;
  revenue_yoy: number | null;    // 同比 %
  profit_yoy: number | null;     // 同比 %
  revenue_qoq: number | null;    // 环比 %
  profit_qoq: number | null;     // 环比 %
}

export interface ReportAlert {
  level: 'success' | 'warning' | 'danger';
  type: string;                  // profit_decline / revenue_decline / roe_low / eps_decline / normal
  message: string;
  report_date: string;
}

// ── 业务动向 v2.5 ──────────────────────────────

export interface MineInfo {
  mine_id: string;
  mine_name: string;
  mine_name_en: string;
  country: string;
  country_code: string;
  latitude: number;
  longitude: number;
  primary_products: string[];    // ["金", "铜"]
  status: '运营中' | '建设中' | '停产';
  equity_ratio: number;          // 权益比例 %
  description: string;
  // 动态数据（可选）
  resource_gold_ton?: number;    // 金资源量（吨）
  resource_copper_ton?: number;  // 铜资源量（万吨）
  resource_zinc_ton?: number;    // 锌资源量（万吨）
  reserve_gold_ton?: number;     // 金储量（吨）
  reserve_copper_ton?: number;   // 铜储量（万吨）
  reserve_zinc_ton?: number;     // 锌储量（万吨）
}

export interface ProductionPlan {
  year: number;
  product_type: string;          // 金/铜/锌
  unit: string;                  // 吨/万吨
  plan_output: number | null;
  actual_output: number | null;
  completion_rate: number | null;
  report_type: string;           // 年度/半年度/季度
  report_date: string;
}

export interface SegmentFinance {
  report_date: string;
  report_type: string;
  segment: string;               // 金/铜/锌/其他
  revenue: number | null;
  cost: number | null;
  gross_profit: number | null;
  gross_margin: number | null;
  ebitda: number | null;
  c1_cost: number | null;        // C1现金成本
  aisc: number | null;           // AISC
  cost_unit: string | null;
}

export interface ESGData {
  year: number;
  ltifr: number | null;          // 百万工时损工率
  trifr: number | null;          // 可记录伤害率
  carbon_intensity: number | null; // 碳排放强度
  water_recycle_rate: number | null; // 水循环利用率
  energy_intensity: number | null; // 综合能耗
  community_investment: number | null; // 社区投资
  local_employment_rate: number | null; // 本地化雇佣率
  greening_area: number | null;  // 绿化面积
  land_reclamation_rate: number | null; // 土地复垦率
  env_incidents: number | null;  // 环境事件数
}

export interface PriceSensitivity {
  year: number;
  product: string;               // 金/铜/锌
  price_change_pct: number;      // 价格变动 %
  profit_impact: number;         // 净利润影响（亿元）
  source: string;
}

export interface BusinessOverview {
  mines_count: number;
  countries_count: number;
  production: ProductionPlan[];
  finance: SegmentFinance[];
  esg: ESGData[];
}
