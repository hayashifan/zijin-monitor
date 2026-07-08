/**
 * 券商研报组件 — 展示研报观点、评级、目标价
 */
import React from 'react';
import { FileTextOutlined } from '@ant-design/icons';

interface AnalystOpinion {
  id: number;
  broker: string;
  analyst: string;
  rating: string;
  target_price: number | null;
  report_title: string;
  report_date: string;
}

interface Props {
  data: AnalystOpinion[];
  loading: boolean;
}

const RATING_COLORS: Record<string, string> = {
  '买入': '#ff4d4f',
  '增持': '#fa8c16',
  '推荐': '#ff4d4f',
  '强烈推荐': '#ff4d4f',
  '中性': '#8c8c8c',
  '持有': '#faad14',
  '减持': '#52c41a',
  '卖出': '#52c41a',
};

function formatDate(dateStr: string): string {
  if (!dateStr) return '';
  return dateStr.slice(5); // MM-DD
}

const AnalystCard = React.memo(function AnalystCard({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="card">
        <div className="card-head"><FileTextOutlined style={{ color: 'var(--accent)' }} /> 券商研报</div>
        <div className="card-body"><div className="empty">加载中...</div></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="card">
        <div className="card-head"><FileTextOutlined style={{ color: 'var(--accent)' }} /> 券商研报</div>
        <div className="card-body"><div className="empty">暂无研报</div></div>
      </div>
    );
  }

  // 统计
  const ratingDist = data.reduce<Record<string, number>>((acc, r) => {
    acc[r.rating] = (acc[r.rating] || 0) + 1;
    return acc;
  }, {});
  const brokerCount = new Set(data.map(r => r.broker)).size;

  return (
    <div className="card">
      <div className="card-head">
        <FileTextOutlined style={{ color: 'var(--accent)' }} /> 券商研报
        <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
          {brokerCount} 家券商 · {data.length} 份研报
        </span>
      </div>
      <div className="card-body" style={{ padding: 0 }}>
        {/* 评级分布 */}
        <div style={{
          display: 'flex', gap: '0.5rem', padding: '0.75rem 1rem',
          borderBottom: '1px solid var(--border-light)', flexWrap: 'wrap',
        }}>
          {Object.entries(ratingDist).map(([rating, count]) => (
            <span key={rating} style={{
              fontSize: '0.7rem', fontWeight: 600,
              color: RATING_COLORS[rating] || 'var(--text-secondary)',
              background: `${RATING_COLORS[rating] || '#8c8c8c'}12`,
              padding: '0.125rem 0.5rem', borderRadius: '0.25rem',
            }}>
              {rating} {count}
            </span>
          ))}
        </div>

        {/* 研报列表 */}
        <div style={{ maxHeight: 350, overflowY: 'auto' }}>
          {data.slice(0, 15).map((report, idx) => (
            <div
              key={report.id}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.5rem 1rem',
                borderBottom: idx < data.length - 1 ? '1px solid var(--border-light)' : 'none',
                transition: 'background 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              {/* 日期 */}
              <span style={{
                flexShrink: 0, fontSize: '0.65rem', color: 'var(--text-tertiary)',
                minWidth: 36,
              }}>
                {formatDate(report.report_date)}
              </span>

              {/* 评级 */}
              <span style={{
                flexShrink: 0, fontSize: '0.6rem', fontWeight: 600,
                color: RATING_COLORS[report.rating] || 'var(--text-secondary)',
                background: `${RATING_COLORS[report.rating] || '#8c8c8c'}12`,
                padding: '0.125rem 0.375rem', borderRadius: '0.25rem',
                minWidth: 32, textAlign: 'center',
              }}>
                {report.rating}
              </span>

              {/* 券商+分析师 */}
              <span style={{
                flexShrink: 0, fontSize: '0.7rem', color: 'var(--text-secondary)',
                maxWidth: 80, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {report.broker}
              </span>

              {/* 标题 */}
              <span style={{
                flex: 1, fontSize: '0.75rem', color: 'var(--text-primary)',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {report.report_title}
              </span>

              {/* 目标价 */}
              {report.target_price && (
                <span style={{
                  flexShrink: 0, fontSize: '0.65rem', color: 'var(--accent)',
                  fontWeight: 600,
                }}>
                  TP ¥{report.target_price.toFixed(0)}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

export default AnalystCard;
