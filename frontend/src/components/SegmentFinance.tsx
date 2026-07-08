/**
 * 板块财务卡片 (v2.5)
 * 显示金/铜/锌板块收入、毛利、EBITDA
 */
import React from 'react';
import { PieChartOutlined } from '@ant-design/icons';
import type { SegmentFinance } from '../types';
import { UP, DOWN, NEUTRAL } from './constants';

interface Props {
  data: SegmentFinance[];
  loading: boolean;
}

// 板块颜色
const SEGMENT_COLORS: Record<string, string> = {
  '金': '#DAA520',
  '铜': '#B87333',
  '锌': '#7B868C',
  '其他': '#8e8e93',
};

function formatNumber(num: number | null, unit: string = '亿'): string {
  if (num === null) return '-';
  if (num >= 10000) return `${(num / 10000).toFixed(2)}万${unit}`;
  if (num >= 100) return `${num.toFixed(1)}${unit}`;
  return `${num.toFixed(2)}${unit}`;
}

function formatCost(num: number | null, unit: string | null): string {
  if (num === null) return '-';
  return `${num.toFixed(0)} ${unit || ''}`;
}

const SegmentFinanceCard = React.memo(function SegmentFinanceCard({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="card">
        <div className="card-head">
          <PieChartOutlined style={{ color: 'var(--accent)' }} /> 板块财务
        </div>
        <div className="card-body">
          <div className="empty">加载中...</div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="card">
        <div className="card-head">
          <PieChartOutlined style={{ color: 'var(--accent)' }} /> 板块财务
        </div>
        <div className="card-body">
          <div className="empty">暂无数据</div>
        </div>
      </div>
    );
  }

  // 计算总收入占比
  const totalRevenue = data.reduce((sum, d) => sum + (d.revenue || 0), 0);

  return (
    <div className="card">
      <div className="card-head">
        <PieChartOutlined style={{ color: 'var(--accent)' }} /> 板块财务
        <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
          {data[0]?.report_date || ''}
        </span>
      </div>
      <div className="card-body">
        {/* 表头 */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '60px 1fr 1fr 1fr 1fr',
          gap: '0.5rem',
          marginBottom: '0.75rem',
          paddingBottom: '0.5rem',
          borderBottom: '1px solid var(--border-light)',
          fontSize: '0.7rem',
          color: 'var(--text-tertiary)',
          fontWeight: 500,
        }}>
          <span>板块</span>
          <span style={{ textAlign: 'right' }}>收入</span>
          <span style={{ textAlign: 'right' }}>毛利</span>
          <span style={{ textAlign: 'right' }}>毛利率</span>
          <span style={{ textAlign: 'right' }}>C1成本</span>
        </div>

        {/* 数据行 */}
        {data.map((item, idx) => {
          const color = SEGMENT_COLORS[item.segment] || SEGMENT_COLORS['其他'];
          const revenuePercent = totalRevenue > 0 && item.revenue
            ? (item.revenue / totalRevenue * 100).toFixed(1)
            : '-';

          return (
            <div
              key={item.segment}
              style={{
                display: 'grid',
                gridTemplateColumns: '60px 1fr 1fr 1fr 1fr',
                gap: '0.5rem',
                padding: '0.5rem 0',
                borderBottom: idx < data.length - 1 ? '1px solid var(--border-light)' : 'none',
                fontSize: '0.8rem',
              }}
            >
              {/* 板块名 */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                <span style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '2px',
                  background: color,
                }} />
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {item.segment}
                </span>
              </div>

              {/* 收入 */}
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                  {formatNumber(item.revenue)}
                </div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)' }}>
                  {revenuePercent}%
                </div>
              </div>

              {/* 毛利 */}
              <div style={{ textAlign: 'right', color: 'var(--text-primary)' }}>
                {formatNumber(item.gross_profit)}
              </div>

              {/* 毛利率 */}
              <div style={{ textAlign: 'right' }}>
                <span style={{
                  color: item.gross_margin && item.gross_margin > 30 ? UP :
                         item.gross_margin && item.gross_margin < 15 ? DOWN : NEUTRAL,
                  fontWeight: 500,
                }}>
                  {item.gross_margin !== null ? `${item.gross_margin.toFixed(1)}%` : '-'}
                </span>
              </div>

              {/* C1成本 */}
              <div style={{ textAlign: 'right', color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                {formatCost(item.c1_cost, item.cost_unit)}
              </div>
            </div>
          );
        })}

        {/* 汇总 */}
        <div style={{
          marginTop: '0.75rem',
          padding: '0.5rem',
          background: 'var(--bg-page)',
          borderRadius: 'var(--radius-sm)',
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.75rem',
          color: 'var(--text-secondary)',
        }}>
          <span>EBITDA 合计</span>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
            {formatNumber(data.reduce((sum, d) => sum + (d.ebitda || 0), 0))}
          </span>
        </div>
      </div>
    </div>
  );
});

export default SegmentFinanceCard;
