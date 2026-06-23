import React from 'react';
import { CommodityPrice } from '../types';
import { UP, DOWN, NEUTRAL } from './constants';
import { useValueFlash } from './useFlash';

/** 商品 SVG 图标 — 简洁线条风格 */
const GoldIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" width="1em" height="1em">
    <rect x="3" y="10" width="18" height="10" rx="2" />
    <path d="M7 10V7a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v3" />
    <line x1="12" y1="14" x2="12" y2="16" />
  </svg>
);

const CopperIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" width="1em" height="1em">
    <circle cx="12" cy="12" r="9" />
    <path d="M12 3v18" />
    <path d="M3 12h18" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const cfg: Record<string, { title: string; icon: React.ReactNode; color: string; cls: string }> = {
  gold:       { title: '黄金',  icon: <GoldIcon/>,   color: '#DAA520', cls: 'card--gold' },
  copper_lme: { title: 'LME铜', icon: <CopperIcon/>, color: '#f97316', cls: 'card--orange' },
  copper_shfe:{ title: '沪铜',  icon: <CopperIcon/>, color: '#ef4444', cls: 'card--red' },
};

/** 货币符号组件 */
function CurrencyBadge({ currency }: { currency: string }) {
  const isUSD = currency === 'USD';
  return (
    <span className="commodity-currency-badge" data-currency={isUSD ? 'usd' : 'cny'}>
      <span className="commodity-currency-symbol">{isUSD ? '$' : '¥'}</span>
      <span className="commodity-currency-code">{isUSD ? 'USD' : 'CNY'}</span>
    </span>
  );
}

interface CommodityCardProps {
  data: CommodityPrice | null;
  type: string;
  loading: boolean;
}

const CommodityCard = React.memo(function CommodityCard({ data, type, loading }: CommodityCardProps) {
  const c = cfg[type] || cfg.gold;

  if (!data) return <div className={`card ${c.cls}`}><div className="card-body commodity"><div className="commodity-icon" style={{color:c.color}}>{c.icon} {c.title}</div><div className="empty">暂无数据</div></div></div>;
  const up = data.change_percent > 0;
  const zero = data.change_percent === 0;
  const dColor = zero ? NEUTRAL : up ? UP : DOWN;
  const arrow = zero ? '' : up ? '↑' : '↓';

  const priceFlash = useValueFlash(data.price);
  const changeFlash = useValueFlash(data.change_percent);

  return (
    <div className={`card ${c.cls}`}>
      <div className="card-body commodity">
        <div className="commodity-header">
          <div className="commodity-icon" style={{color:c.color}}>{c.icon}</div>
          <div className="commodity-title">{c.title}</div>
          <CurrencyBadge currency={data.currency} />
        </div>
        <div className={`commodity-value ${priceFlash ? 'value-flash' : ''}`} style={{color:c.color}}>{data.price.toFixed(2)}</div>
        <div className="commodity-change-row">
          <span className={`commodity-delta ${changeFlash ? 'value-flash' : ''}`} style={{color:dColor}}>{arrow} {zero?'0.00%':`${up?'+':''}${data.change_percent.toFixed(2)}%`}</span>
        </div>
      </div>
    </div>
  );
});

export default CommodityCard;
