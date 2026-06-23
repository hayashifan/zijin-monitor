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
  cross_validation: {
    accuracies: number[];
    mean_accuracy: number;
    mean_auc: number;
    confidence: number;
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
    n_days: number;
    holding_ratio: number;
    transaction_cost: number;
    max_holding_days: number;
  };
  validation_checks: Record<string, boolean>;
  all_passed: boolean;
}
