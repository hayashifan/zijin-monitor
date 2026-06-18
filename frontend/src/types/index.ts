export interface StockQuote {
  code: string;
  market: 'A' | 'HK';
  name: string;
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
