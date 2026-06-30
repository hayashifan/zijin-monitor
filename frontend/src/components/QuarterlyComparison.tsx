import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Row, Col } from 'antd';
import { BarChartOutlined, AlertOutlined } from '@ant-design/icons';
import { UP, DOWN, NEUTRAL, fmt } from './constants';
import type { QuarterlyComparisonItem, ReportAlert } from '../types';

interface Props {
  data: QuarterlyComparisonItem[];
  alerts?: ReportAlert[];
  theme: 'light' | 'dark';
  loading: boolean;
}

function LoadingSkeleton() {
  return (
    <div className="card">
      <div className="card-head"><BarChartOutlined style={{ color: 'var(--accent)' }} /> 季度同比环比</div>
      <div className="card-body"><div className="empty">加载中...</div></div>
    </div>
  );
}

const yoyColor = (v: number | null) => v == null ? NEUTRAL : v >= 0 ? UP : DOWN;

const QuarterlyComparison = React.memo(function QuarterlyComparison({ data, alerts, theme, loading }: Props) {
  const isDark = theme === 'dark';

  const { sorted, latest } = useMemo(() => {
    if (!data.length) return { sorted: [], latest: null };
    const s = [...data].reverse();
    return { sorted: s, latest: data[0] };
  }, [data]);

  if (loading && !data.length) return <LoadingSkeleton />;
  if (!data.length) return (
    <div className="card">
      <div className="card-head"><BarChartOutlined style={{ color: 'var(--accent)' }} /> 季度同比环比</div>
      <div className="card-body"><div className="empty">暂无数据</div></div>
    </div>
  );

  const textColor = isDark ? '#98989d' : '#6e6e73';
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';

  const option = {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      appendToBody: true,
      backgroundColor: isDark ? '#1c1c1e' : '#fff',
      borderColor: isDark ? '#38383a' : '#e5e5ea',
      textStyle: { color: isDark ? '#f5f5f7' : '#1d1d1f', fontSize: 12 },
      formatter: (params: any[]) => {
        const idx = params[0]?.dataIndex;
        const d = sorted[idx];
        if (!d) return '';
        const fmtYoY = (v: number | null) => v != null ? `${v > 0 ? '+' : ''}${v.toFixed(1)}%` : '-';
        return `<b>${d.report_date}</b><br/>` +
          `<span style="color:#1890ff">●</span> 营收: ${(d.revenue / 1e8).toFixed(1)}亿 (${fmtYoY(d.revenue_yoy)})<br/>` +
          `<span style="color:#52c41a">●</span> 净利: ${(d.net_profit / 1e8).toFixed(1)}亿 (${fmtYoY(d.profit_yoy)})`;
      },
    },
    legend: { data: ['营收', '净利润'], textStyle: { color: textColor, fontSize: 11 }, top: 4, right: 8 },
    grid: { top: 36, bottom: 24, left: 48, right: 12 },
    xAxis: {
      type: 'category',
      data: sorted.map(d => d.report_date.slice(0, 7)),
      axisLabel: { color: textColor, fontSize: 11 },
      axisLine: { lineStyle: { color: gridColor } },
    },
    yAxis: {
      type: 'value', name: '亿元',
      axisLabel: { color: textColor, fontSize: 11 },
      splitLine: { lineStyle: { color: gridColor } },
      nameTextStyle: { color: textColor, fontSize: 11 },
    },
    series: [
      {
        name: '营收', type: 'bar', data: sorted.map(d => +(d.revenue / 1e8).toFixed(2)),
        itemStyle: { color: '#1890ff', borderRadius: [3, 3, 0, 0] }, barMaxWidth: 24,
      },
      {
        name: '净利润', type: 'bar', data: sorted.map(d => +(d.net_profit / 1e8).toFixed(2)),
        itemStyle: { color: '#52c41a', borderRadius: [3, 3, 0, 0] }, barMaxWidth: 24,
      },
    ],
  };

  // 筛选危险预警
  const dangerAlerts = (alerts || []).filter(a => a.level === 'danger');

  return (
    <div className="card">
      <div className="card-head">
        <BarChartOutlined style={{ color: 'var(--accent)' }} />
        <span>季度同比环比</span>
        {latest && <span className="list-date" style={{ marginLeft: 'auto' }}>{latest.report_date}</span>}
      </div>
      <div className="card-body">
        {/* 指标卡 */}
        {latest && (
          <Row gutter={[10, 10]} style={{ marginBottom: '0.75rem' }}>
            <Col span={6}>
              <div className="metric-card metric-card--highlight">
                <div className="metric-label">营收</div>
                <div className="metric-value metric-value--sm">{fmt(latest.revenue)}</div>
              </div>
            </Col>
            <Col span={6}>
              <div className="metric-card">
                <div className="metric-label">净利</div>
                <div className="metric-value metric-value--sm">{fmt(latest.net_profit)}</div>
              </div>
            </Col>
            <Col span={6}>
              <div className="metric-card">
                <div className="metric-label">营收同比</div>
                <div className="metric-value metric-value--sm" style={{ color: yoyColor(latest.revenue_yoy) }}>
                  {latest.revenue_yoy != null ? `${latest.revenue_yoy > 0 ? '+' : ''}${latest.revenue_yoy.toFixed(1)}%` : '--'}
                </div>
              </div>
            </Col>
            <Col span={6}>
              <div className="metric-card">
                <div className="metric-label">净利同比</div>
                <div className="metric-value metric-value--sm" style={{ color: yoyColor(latest.profit_yoy) }}>
                  {latest.profit_yoy != null ? `${latest.profit_yoy > 0 ? '+' : ''}${latest.profit_yoy.toFixed(1)}%` : '--'}
                </div>
              </div>
            </Col>
          </Row>
        )}

        {/* 预警内联提示 */}
        {dangerAlerts.length > 0 && (
          <div style={{
            display: 'flex', gap: 'var(--space-sm)', flexWrap: 'wrap',
            marginBottom: '0.75rem', padding: '0.5rem 0.75rem',
            background: 'rgba(255,77,79,0.06)', borderRadius: 'var(--radius-sm)',
            borderLeft: `3px solid ${UP}`,
          }}>
            <AlertOutlined style={{ color: UP, marginTop: 2 }} />
            {dangerAlerts.map((a, i) => (
              <span key={i} style={{ fontSize: '0.75rem', color: UP }}>{a.message}</span>
            ))}
          </div>
        )}

        {/* 图表 */}
        <ReactECharts option={option} style={{ height: 240 }} />
      </div>
    </div>
  );
});

export default QuarterlyComparison;
