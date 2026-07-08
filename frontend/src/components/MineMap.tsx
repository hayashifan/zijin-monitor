/**
 * 矿山地图 (v2.5) — 方块版 + 手动防重叠
 */
import React, { useState, useCallback } from 'react';
import { GlobalOutlined } from '@ant-design/icons';
import type { MineInfo } from '../types';
import { NEUTRAL } from './constants';

interface Props {
  mines: MineInfo[];
  loading: boolean;
  onMineClick?: (mine: MineInfo) => void;
  selectedMineId?: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  '运营中': '#52c41a', '建设中': '#faad14', '停产': '#ff4d4f',
};

const PRODUCT_ICONS: Record<string, string> = {
  '金': 'Au', '铜': 'Cu', '锌': 'Zn', '钴': 'Co', '钒': 'V', '银': 'Ag',
};

// 手动布局：每座矿山的SVG坐标+标签偏移（避免堆叠）
// 基于真实经纬度等矩形投影，手动微调中国区密集矿山
const MINE_LAYOUT: Record<string, { x: number; y: number; lx: number; ly: number }> = {
  'zijinshan':     { x: 818, y: 258, lx: 832, ly: 252 },  // 紫金山（福建）
  'kamoa-kakula':  { x: 533, y: 295, lx: 547, ly: 289 },  // 卡莫阿（刚果金）
  'kolwezi':       { x: 520, y: 296, lx: 506, ly: 302 },  // 科卢韦齐（刚果金）
  'boroo':         { x: 740, y: 118, lx: 754, ly: 112 },  // 宝力格（蒙古）
  'neves-corvo':   { x: 460, y: 143, lx: 446, ly: 137 },  // 内维什（葡萄牙）
  'orado':         { x: 280, y: 240, lx: 294, ly: 234 },  // 奥拉多（苏里南）
  'rtb-bor':       { x: 533, y: 138, lx: 547, ly: 132 },  // RTB Bor（塞尔维亚）
  'dadi':          { x: 768, y: 148, lx: 782, ly: 142 },  // 大地（宁夏）
  'longnan':       { x: 755, y: 188, lx: 741, ly: 194 },  // 陇南（甘肃）
  'shibing':       { x: 790, y: 235, lx: 804, ly: 229 },  // 施秉（贵州）
};

function MineTooltip({ mine, x, y }: { mine: MineInfo; x: number; y: number }) {
  return (
    <div style={{
      position: 'absolute', left: x + 15, top: y - 10,
      background: 'var(--bg-card)', border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-sm)', padding: '0.75rem',
      boxShadow: 'var(--shadow-hover)', zIndex: 100, minWidth: 200, pointerEvents: 'none',
    }}>
      <div style={{ fontWeight: 600, marginBottom: '0.25rem', color: 'var(--text-primary)' }}>
        {mine.mine_name}
      </div>
      <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginBottom: '0.5rem' }}>
        {mine.country} · {mine.status}
      </div>
      <div style={{ display: 'flex', gap: '0.25rem' }}>
        {mine.primary_products.map(p => (
          <span key={p} style={{
            fontSize: '0.6rem', background: 'var(--accent-bg)', color: 'var(--accent)',
            padding: '0.125rem 0.375rem', borderRadius: '0.25rem', fontWeight: 600,
          }}>{PRODUCT_ICONS[p] || p}</span>
        ))}
      </div>
    </div>
  );
}

const MineMap = React.memo(function MineMap({ mines, loading, onMineClick, selectedMineId }: Props) {
  const [hoveredMine, setHoveredMine] = useState<MineInfo | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const handleMouseMove = useCallback((e: React.MouseEvent, mine: MineInfo) => {
    const rect = e.currentTarget.closest('.mine-map-container')?.getBoundingClientRect();
    if (rect) setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    setHoveredMine(mine);
  }, []);
  const handleMouseLeave = useCallback(() => setHoveredMine(null), []);

  if (loading) {
    return (
      <div className="card">
        <div className="card-head"><GlobalOutlined style={{ color: 'var(--accent)' }} /> 全球矿山分布</div>
        <div className="card-body"><div className="empty">加载中...</div></div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-head">
        <GlobalOutlined style={{ color: 'var(--accent)' }} /> 全球矿山分布
        <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
          {mines.length} 座矿山 · {new Set(mines.map(m => m.country)).size} 个国家
        </span>
      </div>
      <div className="card-body mine-map-container" style={{ position: 'relative', padding: 0 }}>
        <svg viewBox="0 0 1000 500" style={{ width: '100%', height: 'auto', display: 'block', minHeight: 320 }}>
          <rect width="1000" height="500" fill="var(--bg-page)" rx="8" />

          {/* 大陆方块 */}
          <rect x="80" y="80" width="250" height="180" fill="var(--bg-card)" stroke="var(--border-medium)" strokeWidth="1" rx="4" opacity="0.7" />
          <rect x="180" y="280" width="150" height="180" fill="var(--bg-card)" stroke="var(--border-medium)" strokeWidth="1" rx="4" opacity="0.7" />
          <rect x="420" y="80" width="150" height="120" fill="var(--bg-card)" stroke="var(--border-medium)" strokeWidth="1" rx="4" opacity="0.7" />
          <rect x="420" y="210" width="150" height="190" fill="var(--bg-card)" stroke="var(--border-medium)" strokeWidth="1" rx="4" opacity="0.7" />
          <rect x="560" y="60" width="350" height="250" fill="var(--bg-card)" stroke="var(--border-medium)" strokeWidth="1" rx="4" opacity="0.7" />
          <rect x="750" y="320" width="150" height="120" fill="var(--bg-card)" stroke="var(--border-medium)" strokeWidth="1" rx="4" opacity="0.7" />

          {/* 矿山标注 */}
          {mines.map(mine => {
            const layout = MINE_LAYOUT[mine.mine_id];
            if (!layout) return null;
            const isSelected = mine.mine_id === selectedMineId;
            const isHovered = mine.mine_id === hoveredMine?.mine_id;
            const color = STATUS_COLORS[mine.status] || NEUTRAL;
            const r = isSelected ? 10 : isHovered ? 9 : 7;
            const product = PRODUCT_ICONS[mine.primary_products[0]] || mine.primary_products[0];

            return (
              <g key={mine.mine_id} style={{ cursor: 'pointer' }}
                onClick={() => onMineClick?.(mine)}
                onMouseMove={(e) => handleMouseMove(e, mine)}
                onMouseLeave={handleMouseLeave}>

                {(isSelected || isHovered) && (
                  <circle cx={layout.x} cy={layout.y} r={r + 6} fill={color} opacity={0.15}>
                    <animate attributeName="r" values={`${r + 4};${r + 8};${r + 4}`} dur="1.5s" repeatCount="indefinite" />
                  </circle>
                )}

                {/* 引线 */}
                <line x1={layout.x} y1={layout.y} x2={layout.lx} y2={layout.ly}
                  stroke="var(--text-tertiary)" strokeWidth="0.5" opacity="0.3" />

                <circle cx={layout.x} cy={layout.y} r={r} fill={color}
                  stroke={isSelected ? 'var(--accent)' : 'var(--bg-card)'}
                  strokeWidth={isSelected ? 2 : 1} />

                <text x={layout.lx} y={layout.ly + 3} textAnchor="middle"
                  fontSize="10" fill="var(--text-primary)" fontWeight="700">
                  {product}
                </text>
              </g>
            );
          })}

          {/* 图例 */}
          <g transform="translate(20, 460)">
            {Object.entries(STATUS_COLORS).map(([status, color], i) => (
              <g key={status} transform={`translate(${i * 80}, 0)`}>
                <circle cx="5" cy="5" r="4" fill={color} />
                <text x="14" y="9" fontSize="10" fill="var(--text-tertiary)">{status}</text>
              </g>
            ))}
          </g>
        </svg>

        {hoveredMine && <MineTooltip mine={hoveredMine} x={tooltipPos.x} y={tooltipPos.y} />}
      </div>
    </div>
  );
});

export default MineMap;
