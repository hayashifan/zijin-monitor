/**
 * 事件流组件 — EchoPai风格的实时事件流
 * 每条事件带类型标签、影响方向、时间戳
 */
import React from 'react';
import { ThunderboltOutlined } from '@ant-design/icons';

interface Event {
  id: number;
  event_type: string;
  event_subtype: string;
  title: string;
  summary: string;
  impact_level: string;
  publish_date: string;
  related_mine: string | null;
  related_product: string | null;
}

interface Props {
  data: Event[];
  loading: boolean;
}

const TYPE_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  production: { icon: '⚒️', color: '#52c41a', label: '产量' },
  financial: { icon: '💰', color: '#DAA520', label: '财务' },
  personnel: { icon: '👤', color: '#1890ff', label: '人事' },
  safety: { icon: '⚠️', color: '#ff4d4f', label: '安环' },
  ma: { icon: '🤝', color: '#722ed1', label: '并购' },
  esg: { icon: '🌱', color: '#13c2c2', label: 'ESG' },
  operation: { icon: '🏭', color: '#faad14', label: '运营' },
  dividend: { icon: '📊', color: '#eb2f96', label: '分红' },
  regulation: { icon: '📋', color: '#8c8c8c', label: '监管' },
  other: { icon: '📌', color: '#595959', label: '其他' },
};

const IMPACT_COLORS: Record<string, string> = {
  positive: '#ff4d4f',
  negative: '#52c41a',
  neutral: '#8c8e93',
};

function formatDate(dateStr: string): string {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffDays === 0) return '今天';
  if (diffDays === 1) return '昨天';
  if (diffDays < 7) return `${diffDays}天前`;
  return dateStr.slice(5); // MM-DD
}

const EventStream = React.memo(function EventStream({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="card">
        <div className="card-head">
          <ThunderboltOutlined style={{ color: 'var(--accent)' }} /> 事件流
        </div>
        <div className="card-body"><div className="empty">加载中...</div></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="card">
        <div className="card-head">
          <ThunderboltOutlined style={{ color: 'var(--accent)' }} /> 事件流
        </div>
        <div className="card-body"><div className="empty">暂无事件</div></div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-head">
        <ThunderboltOutlined style={{ color: 'var(--accent)' }} /> 事件流
        <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
          近30天 {data.length} 条
        </span>
      </div>
      <div className="card-body" style={{ padding: 0 }}>
        <div style={{ maxHeight: 400, overflowY: 'auto' }}>
          {data.map((event, idx) => {
            const config = TYPE_CONFIG[event.event_type] || TYPE_CONFIG.other;
            const impactColor = IMPACT_COLORS[event.impact_level] || IMPACT_COLORS.neutral;

            return (
              <div
                key={event.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.75rem',
                  padding: '0.625rem 1rem',
                  borderBottom: idx < data.length - 1 ? '1px solid var(--border-light)' : 'none',
                  transition: 'background 0.15s',
                  cursor: 'default',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                {/* 类型标签 */}
                <span style={{
                  flexShrink: 0,
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  color: config.color,
                  background: `${config.color}12`,
                  padding: '0.125rem 0.5rem',
                  borderRadius: '0.25rem',
                  minWidth: 36,
                  textAlign: 'center',
                }}>
                  {config.icon} {config.label}
                </span>

                {/* 内容 */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: '0.8rem',
                    color: 'var(--text-primary)',
                    lineHeight: 1.4,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {event.title.replace(/^紫金矿业[:：]\s*紫金矿业集团股份有限公司\s*/, '')}
                  </div>
                  {(event.related_mine || event.related_product) && (
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', marginTop: 2 }}>
                      {event.related_mine && <span>📍{event.related_mine} </span>}
                      {event.related_product && <span>🪙{event.related_product}</span>}
                    </div>
                  )}
                </div>

                {/* 影响方向 */}
                {event.impact_level !== 'neutral' && (
                  <span style={{
                    flexShrink: 0,
                    fontSize: '0.6rem',
                    fontWeight: 600,
                    color: impactColor,
                    background: `${impactColor}12`,
                    padding: '0.125rem 0.375rem',
                    borderRadius: '0.25rem',
                  }}>
                    {event.impact_level === 'positive' ? '利好' : '利空'}
                  </span>
                )}

                {/* 日期 */}
                <span style={{
                  flexShrink: 0,
                  fontSize: '0.65rem',
                  color: 'var(--text-tertiary)',
                  minWidth: 40,
                  textAlign: 'right',
                }}>
                  {formatDate(event.publish_date)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
});

export default EventStream;
