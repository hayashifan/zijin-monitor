/**
 * 产量计划卡片 (v2.5)
 * 显示金/铜/锌年度产量计划完成率
 */
import React from 'react';
import { BarChartOutlined } from '@ant-design/icons';
import type { ProductionPlan } from '../types';
import { UP, DOWN, NEUTRAL } from './constants';

interface Props {
  data: ProductionPlan[];
  loading: boolean;
}

// 产品颜色
const PRODUCT_COLORS: Record<string, string> = {
  '金': '#DAA520',
  '铜': '#B87333',
  '锌': '#7B868C',
};

function ProgressBar({ value, max, color }: { value: number; max: number; color: string }) {
  const percent = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div style={{
      width: '100%',
      height: '8px',
      background: 'var(--bg-page)',
      borderRadius: '4px',
      overflow: 'hidden',
    }}>
      <div style={{
        width: `${percent}%`,
        height: '100%',
        background: color,
        borderRadius: '4px',
        transition: 'width 0.5s ease',
      }} />
    </div>
  );
}

function getStatusColor(rate: number | null): string {
  if (rate === null) return NEUTRAL;
  if (rate >= 95) return UP;      // 红涨
  if (rate >= 80) return '#faad14'; // 黄色
  return DOWN;                      // 绿跌
}

const ProductionCard = React.memo(function ProductionCard({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="card">
        <div className="card-head">
          <BarChartOutlined style={{ color: 'var(--accent)' }} /> 产量计划
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
          <BarChartOutlined style={{ color: 'var(--accent)' }} /> 产量计划
        </div>
        <div className="card-body">
          <div className="empty">暂无数据</div>
        </div>
      </div>
    );
  }

  // 按产品分组
  const grouped = data.reduce<Record<string, ProductionPlan[]>>((acc, item) => {
    if (!acc[item.product_type]) acc[item.product_type] = [];
    acc[item.product_type].push(item);
    return acc;
  }, {});

  return (
    <div className="card">
      <div className="card-head">
        <BarChartOutlined style={{ color: 'var(--accent)' }} /> 产量计划
        <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
          {data[0]?.year || new Date().getFullYear()} 年度
        </span>
      </div>
      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {Object.entries(grouped).map(([product, plans]) => {
          const latest = plans[plans.length - 1];
          const planOutput = latest.plan_output || 0;
          const actualOutput = latest.actual_output || 0;
          const completionRate = latest.completion_rate;
          const color = PRODUCT_COLORS[product] || 'var(--accent)';
          const statusColor = getStatusColor(completionRate);

          return (
            <div key={product} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {/* 产品标题 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '6px',
                    background: `${color}15`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    color,
                  }}>
                    {product.charAt(0)}
                  </span>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    矿产{product}
                  </span>
                </div>
                <span style={{
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  color: statusColor,
                }}>
                  {completionRate !== null ? `${completionRate.toFixed(1)}%` : '待更新'}
                </span>
              </div>

              {/* 进度条 */}
              <ProgressBar value={actualOutput} max={planOutput} color={color} />

              {/* 数值详情 */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.75rem',
                color: 'var(--text-secondary)',
              }}>
                <span>
                  实际 <strong style={{ color: 'var(--text-primary)' }}>{actualOutput}</strong> {latest.unit}
                </span>
                <span>
                  计划 {planOutput} {latest.unit}
                </span>
              </div>
            </div>
          );
        })}

        {/* 数据来源 */}
        {data[0]?.report_date && (
          <div style={{
            fontSize: '0.7rem',
            color: 'var(--text-tertiary)',
            textAlign: 'right',
            marginTop: '0.5rem',
          }}>
            报告期: {data[0].report_date}
          </div>
        )}
      </div>
    </div>
  );
});

export default ProductionCard;
