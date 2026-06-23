import React from 'react';
import { GoldOutlined, ThunderboltOutlined, FireOutlined } from '@ant-design/icons';
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
  if (!data) return <div className={`card ${c.cls}`}><div className="card-body commodity"><div className="commodity-icon" style={{color:c.color}}>{c.icon} {c.title}</div><div className="empty">暂无数据</div></div></div>;
  const up = data.change_percent > 0;
  const zero = data.change_percent === 0;
  const dColor = zero ? NEUTRAL : up ? UP : DOWN;

  return (
    <div className={`card ${c.cls}`}>
      <div className="card-body commodity">
        <div className="commodity-icon" style={{color:c.color}}>{c.icon} {c.title}</div>
        <div className="commodity-value" style={{color:c.color}}>{data.currency==='USD'?'$':'¥'}{data.price.toFixed(2)}</div>
        <div className="commodity-delta" style={{color:dColor}}>{zero?'0.00%':`${up?'+':''}${data.change_percent.toFixed(2)}%`}</div>
      </div>
    </div>
  );
});

export default CommodityCard;
