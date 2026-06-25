import React from 'react';
import { GoldVolatility } from '../types';

const PANIC_COLORS: Record<string, string> = {
  low: '#52c41a', normal: '#1890ff', elevated: '#faad14', high: '#ff4d4f', extreme: '#cf1322',
};
const PANIC_LABELS: Record<string, string> = {
  low: '平静', normal: '正常', elevated: '偏高', high: '恐慌', extreme: '极端恐慌',
};

/** SVG 环形仪表盘 */
function PanicGauge({ value, level }: { value: number; level: string }) {
  // Map annualized vol (0-50%) to arc (0-270deg)
  const clamped = Math.min(Math.max(value, 0), 50);
  const angle = (clamped / 50) * 270;
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * (270 / 360);
  const dashOffset = arcLength - (angle / 270) * arcLength;
  const color = PANIC_COLORS[level] || '#1890ff';

  return (
    <div className="vol-gauge">
      <svg viewBox="0 0 100 100" width="96" height="96">
        <circle cx="50" cy="50" r={radius} fill="none" stroke="var(--border)" strokeWidth="6"
          strokeDasharray={`${arcLength} ${circumference}`} strokeLinecap="round"
          transform="rotate(135 50 50)" />
        <circle cx="50" cy="50" r={radius} fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={`${arcLength} ${circumference}`} strokeDashoffset={dashOffset}
          strokeLinecap="round" transform="rotate(135 50 50)"
          style={{ transition: 'stroke-dashoffset 0.6s ease, stroke 0.3s ease' }} />
        <text x="50" y="45" textAnchor="middle" fill="var(--text-primary)" fontSize="14" fontWeight="700">
          {value.toFixed(1)}%
        </text>
        <text x="50" y="60" textAnchor="middle" fill={color} fontSize="9" fontWeight="600">
          {PANIC_LABELS[level] || level}
        </text>
      </svg>
    </div>
  );
}

/** 迷你火花线 */
function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (!data || data.length < 2) return null;
  const w = 80, h = 24, pad = 2;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ display: 'block' }}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

interface Props {
  data: GoldVolatility | null;
  loading: boolean;
}

const GoldVolatilityCard = React.memo(function GoldVolatilityCard({ data, loading }: Props) {
  if (loading && !data) {
    return (
      <div className="card card--gold-vol">
        <div className="card-body">
          <div className="vol-header">
            <span className="vol-icon">📊</span>
            <span className="vol-title">黄金波动率</span>
          </div>
          <div className="empty">加载中...</div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card card--gold-vol">
        <div className="card-body">
          <div className="vol-header">
            <span className="vol-icon">📊</span>
            <span className="vol-title">黄金波动率</span>
          </div>
          <div className="empty">暂无数据</div>
        </div>
      </div>
    );
  }

  const color = PANIC_COLORS[data.panic_level] || '#1890ff';
  const trendIcon = data.trend === 'rising' ? '↑' : data.trend === 'falling' ? '↓' : '→';
  const trendColor = data.trend === 'rising' ? '#ff4d4f' : data.trend === 'falling' ? '#52c41a' : '#faad14';

  return (
    <div className="card card--gold-vol">
      <div className="card-body">
        <div className="vol-header">
          <span className="vol-icon">📊</span>
          <span className="vol-title">黄金波动率</span>
          <span className="vol-badge" style={{ background: color }}>{PANIC_LABELS[data.panic_level]}</span>
        </div>

        <PanicGauge value={data.annualized_vol} level={data.panic_level} />

        <div className="vol-stats">
          <div className="vol-stat">
            <div className="vol-stat-value" style={{ color }}>{data.annualized_vol.toFixed(1)}%</div>
            <div className="vol-stat-label">{data.window}日年化</div>
          </div>
          <div className="vol-stat">
            <div className="vol-stat-value">{data.percentile.toFixed(0)}%</div>
            <div className="vol-stat-label">历史分位</div>
          </div>
          <div className="vol-stat">
            <div className="vol-stat-value" style={{ color: trendColor }}>
              {trendIcon} {data.trend === 'rising' ? '上升' : data.trend === 'falling' ? '下降' : '平稳'}
            </div>
            <div className="vol-stat-label">趋势</div>
          </div>
        </div>

        {data.sparkline && data.sparkline.length > 2 && (
          <div className="vol-sparkline">
            <Sparkline data={data.sparkline} color={color} />
          </div>
        )}
      </div>
    </div>
  );
});

export default GoldVolatilityCard;
