import React, { useState, useEffect, useRef } from 'react';
import { GoldOutlined, ThunderboltOutlined, FireOutlined, DollarOutlined } from '@ant-design/icons';
import { CommodityPrice } from '../types';
import { UP, DOWN, NEUTRAL } from './constants';

const cfg: Record<string, { title: string; icon: React.ReactNode; color: string; cls: string }> = {
  gold:       { title: '黄金',  icon: <GoldOutlined/>,        color: '#DAA520', cls: 'card--gold' },
  copper_lme: { title: 'LME铜', icon: <ThunderboltOutlined/>, color: '#f97316', cls: 'card--orange' },
  copper_shfe:{ title: '沪铜',  icon: <FireOutlined/>,        color: '#ef4444', cls: 'card--red' },
};

interface CommodityCardProps {
  data: CommodityPrice | null;
  type: string;
  loading: boolean;
}

const CommodityCard = React.memo(function CommodityCard({ data, type, loading }: CommodityCardProps) {
  const c = cfg[type] || cfg.gold;
  const [flash, setFlash] = useState(false);
  const prevPriceRef = useRef<number | null>(null);

  useEffect(() => {
    if (!data) return;
    if (prevPriceRef.current !== null && prevPriceRef.current !== data.price) {
      setFlash(true);
      const t = setTimeout(() => setFlash(false), 600);
      return () => clearTimeout(t);
    }
    prevPriceRef.current = data.price;
  }, [data?.price]);

  if (!data) return <div className={`card ${c.cls}`}><div className="card-body commodity"><div className="commodity-icon" style={{color:c.color}}>{c.icon} {c.title}</div><div className="empty">暂无数据</div></div></div>;
  const up = data.change_percent > 0;
  const zero = data.change_percent === 0;
  const dColor = zero ? NEUTRAL : up ? UP : DOWN;
  const arrow = zero ? '' : up ? '↑' : '↓';
  const isUSD = data.currency === 'USD';

  // Gradient background based on price direction
  const gradientBg = zero
    ? undefined
    : up
      ? 'linear-gradient(135deg, rgba(255,77,79,0.04) 0%, transparent 60%)'
      : 'linear-gradient(135deg, rgba(82,196,26,0.04) 0%, transparent 60%)';

  return (
    <div className={`card ${c.cls}`} style={{ background: gradientBg || undefined }}>
      <div className="card-body commodity">
        <div className="commodity-icon" style={{color:c.color}}>{c.icon} {c.title}</div>
        <div className={`commodity-value ${flash ? 'commodity-flash' : ''}`} style={{color:c.color}}>{data.price.toFixed(2)}</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginTop: '0.375rem' }}>
          <span className="commodity-delta" style={{color:dColor}}>{arrow} {zero?'0.00%':`${up?'+':''}${data.change_percent.toFixed(2)}%`}</span>
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 2,
            fontSize: '0.625rem',
            fontWeight: 700,
            padding: '1px 6px',
            borderRadius: '0.25rem',
            background: isUSD ? 'rgba(82,196,26,0.12)' : 'rgba(255,77,79,0.12)',
            color: isUSD ? '#52c41a' : '#ff4d4f',
          }}>
            {isUSD ? <DollarOutlined style={{ fontSize: '0.5rem' }} /> : '¥'}
            {isUSD ? 'USD' : 'CNY'}
          </span>
        </div>
      </div>
    </div>
  );
});

export default CommodityCard;
