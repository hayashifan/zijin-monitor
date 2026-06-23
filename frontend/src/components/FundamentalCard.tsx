import React, { useMemo } from 'react';
import { Row, Col } from 'antd';
import { FundOutlined, DollarOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import { FinancialOverview } from '../types';
import { UP, DOWN, NEUTRAL } from './constants';

interface FundamentalCardProps {
  data: FinancialOverview | null;
  loading: boolean;
}

/** 格式化大数字 */
const fmtCap = (v: number) => !v ? '--' : v >= 1e8 ? `${(v / 1e8).toFixed(0)}亿` : v >= 1e4 ? `${(v / 1e4).toFixed(0)}万` : v.toLocaleString();
const fmtMoney = (v: number) => !v ? '--' : v >= 1e8 ? `${(v / 1e8).toFixed(1)}亿` : v >= 1e4 ? `${(v / 1e4).toFixed(1)}万` : v.toFixed(0);

/** PE 颜色：低估值绿，高估值红 */
const peColor = (pe: number) => pe <= 0 ? NEUTRAL : pe < 15 ? UP : pe < 30 ? '#DAA520' : DOWN;

/** 条形图组件 */
function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min(Math.abs(value) / max * 100, 100) : 0;
  return (
    <div className="profit-bar-track">
      <div className="profit-bar-fill" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

const FundamentalCard = React.memo(function FundamentalCard({ data, loading }: FundamentalCardProps) {
  const metrics = data?.metrics ?? null;
  const trend = data?.profit_trend ?? [];

  // 计算盈利趋势的最大值用于条形图归一化
  const { maxRevenue, maxProfit } = useMemo(() => {
    if (!trend.length) return { maxRevenue: 0, maxProfit: 0 };
    let mr = 0, mp = 0;
    for (const t of trend) {
      mr = Math.max(mr, Math.abs(t.revenue));
      mp = Math.max(mp, Math.abs(t.net_profit));
    }
    return { maxRevenue: mr, maxProfit: mp };
  }, [trend]);

  if (!metrics && !trend.length) {
    return (
      <div className="card">
        <div className="card-head"><FundOutlined style={{ color: 'var(--accent)' }} /> 基本面数据</div>
        <div className="card-body"><div className="empty">暂无数据</div></div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-head">
        <FundOutlined style={{ color: 'var(--accent)' }} /> 基本面数据
        {data?.from_cache && <span className="cache-badge">缓存</span>}
      </div>
      <div className="card-body">
        {/* 核心估值指标 */}
        <Row gutter={[10, 10]} style={{ marginBottom: '1rem' }}>
          <Col span={8}>
            <div className="metric-card">
              <div className="metric-label">市盈率 PE</div>
              <div className="metric-value" style={{ color: metrics ? peColor(metrics.pe_ratio) : NEUTRAL }}>
                {metrics && metrics.pe_ratio > 0 ? metrics.pe_ratio.toFixed(1) : '--'}
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div className="metric-card">
              <div className="metric-label">市净率 PB</div>
              <div className="metric-value" style={{ color: metrics && metrics.pb_ratio > 1 ? 'var(--accent)' : UP }}>
                {metrics && metrics.pb_ratio > 0 ? metrics.pb_ratio.toFixed(2) : '--'}
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div className="metric-card">
              <div className="metric-label">ROE</div>
              <div className="metric-value" style={{ color: metrics && metrics.roe && metrics.roe > 15 ? UP : metrics && metrics.roe && metrics.roe > 0 ? '#DAA520' : NEUTRAL }}>
                {metrics && metrics.roe ? `${metrics.roe.toFixed(1)}%` : '--'}
              </div>
            </div>
          </Col>
        </Row>

        {/* 盈利趋势条形图 */}
        {trend.length > 0 && (
          <div className="profit-trend-section">
            <div className="profit-trend-header">
              <span className="profit-trend-title">盈利趋势</span>
              <span className="profit-trend-legend">
                <span className="profit-legend-item"><span className="profit-legend-dot" style={{ background: 'var(--accent)' }} /> 营收</span>
                <span className="profit-legend-item"><span className="profit-legend-dot" style={{ background: UP }} /> 净利</span>
              </span>
            </div>
            <div className="profit-trend-chart">
              {trend.slice(0, 6).reverse().map((item, i) => {
                const dateLabel = item.report_date.length >= 10 ? item.report_date.slice(5, 10) : item.report_date;
                return (
                  <div key={i} className="profit-trend-row">
                    <span className="profit-trend-date">{dateLabel}</span>
                    <div className="profit-trend-bars">
                      <MiniBar value={item.revenue} max={maxRevenue} color="var(--accent)" />
                      <MiniBar value={item.net_profit} max={maxProfit} color={item.net_profit >= 0 ? UP : DOWN} />
                    </div>
                    <span className="profit-trend-val">{fmtMoney(item.net_profit)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 详细指标网格 */}
        <Row gutter={[10, 10]} style={{ marginTop: '1rem' }}>
          <Col span={12}>
            <div className="metric-card metric-card--highlight">
              <div className="metric-label"><DollarOutlined style={{ marginRight: 4 }} />总市值</div>
              <div className="metric-value metric-value--lg">{metrics ? fmtCap(metrics.total_market_cap) : '--'}</div>
            </div>
          </Col>
          <Col span={12}>
            <div className="metric-card">
              <div className="metric-label">流通市值</div>
              <div className="metric-value metric-value--sm">{metrics ? fmtCap(metrics.circulating_market_cap) : '--'}</div>
            </div>
          </Col>
          <Col span={8}>
            <div className="metric-card">
              <div className="metric-label">换手率</div>
              <div className="metric-value metric-value--sm">{metrics && metrics.turnover_rate > 0 ? `${metrics.turnover_rate.toFixed(2)}%` : '--'}</div>
            </div>
          </Col>
          <Col span={8}>
            <div className="metric-card">
              <div className="metric-label">EPS</div>
              <div className="metric-value metric-value--sm">{metrics && metrics.eps ? metrics.eps.toFixed(2) : '--'}</div>
            </div>
          </Col>
          <Col span={8}>
            <div className="metric-card">
              <div className="metric-label">BVPS</div>
              <div className="metric-value metric-value--sm">{metrics && metrics.bvps ? metrics.bvps.toFixed(2) : '--'}</div>
            </div>
          </Col>
          <Col span={12}>
            <div className="metric-card">
              <div className="metric-label">毛利率</div>
              <div className="metric-value metric-value--sm" style={{ color: metrics && metrics.gross_margin && metrics.gross_margin > 20 ? UP : NEUTRAL }}>
                {metrics && metrics.gross_margin ? `${metrics.gross_margin.toFixed(1)}%` : '--'}
              </div>
            </div>
          </Col>
          <Col span={12}>
            <div className="metric-card">
              <div className="metric-label">净利率</div>
              <div className="metric-value metric-value--sm" style={{ color: metrics && metrics.net_margin && metrics.net_margin > 10 ? UP : NEUTRAL }}>
                {metrics && metrics.net_margin ? `${metrics.net_margin.toFixed(1)}%` : '--'}
              </div>
            </div>
          </Col>
        </Row>

        {/* 报告期 */}
        {metrics?.report_date && (
          <div className="report-date-label">报告期: {metrics.report_date}</div>
        )}
      </div>
    </div>
  );
});

export default FundamentalCard;
