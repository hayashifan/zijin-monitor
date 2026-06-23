import React from 'react';
import { MinusOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { StockQuote } from '../types';
import { UP, DOWN, NEUTRAL, fmt } from './constants';

interface StockCardProps {
  data: StockQuote | null;
  loading: boolean;
  flash: boolean;
  colorClass: string;
  market: string;
}

const StockCard = React.memo(function StockCard({ data, loading, flash, colorClass, market }: StockCardProps) {
  if (!data) return <div className="card"><div className="empty"><MinusOutlined style={{fontSize:24,opacity:0.3}}/>暂无数据</div></div>;
  const closed = data.is_closed;
  const up = data.change_percent > 0;
  const zero = data.change_percent === 0;
  const color = closed ? NEUTRAL : zero ? NEUTRAL : up ? UP : DOWN;
  const arrow = closed || zero ? <MinusOutlined/> : up ? <ArrowUpOutlined/> : <ArrowDownOutlined/>;
  const label = data.market_label || market;

  return (
    <div className={`card ${colorClass}`}>
      <div className="card-body">
        <div className="stock-header">
          <div style={{display:'flex',alignItems:'center',gap:'0.5rem'}}>
            <span className="stock-name">{data.name}</span>
            <span className="market-badge">{label}</span>
          </div>
          <span className="stock-code">{data.code}</span>
        </div>
        <div className="price-display">
          <div className={`price-value ${flash ? 'price-flash' : ''}`} style={{color}}>
            {market==='HK'?'$':'¥'}{data.price.toFixed(2)}
          </div>
          <div className="price-change">
            <span className="price-badge" style={{background:`${color}10`,color}}>{arrow} {Math.abs(data.change).toFixed(2)}</span>
            <span className="price-pct" style={{color}}>{zero?'0.00':(up?'+':'')}{data.change_percent.toFixed(2)}%</span>
          </div>
        </div>
        <div className="data-grid">
          {[
            ['今开', data.open.toFixed(2)],
            ['最高', data.high.toFixed(2), closed ? '' : 'data-value--up'],
            ['昨收', data.pre_close.toFixed(2)],
            ['最低', data.low.toFixed(2), closed ? '' : 'data-value--down'],
            ['成交量', fmt(data.volume)],
            ['成交额', fmt(data.amount)],
          ].map(([l,v,c]) => (
            <div className="data-cell" key={l}>
              <span className="data-label">{l}</span>
              <span className={`data-value ${c||''}`}>{v}</span>
            </div>
          ))}
        </div>
        {market==='A' && (data.pe_ratio>0 || data.pb_ratio>0) && (
          <div className="stock-footer">
            {data.pe_ratio>0 && <span className="pill">PE {data.pe_ratio.toFixed(1)}</span>}
            {data.pb_ratio>0 && <span className="pill">PB {data.pb_ratio.toFixed(2)}</span>}
          </div>
        )}
      </div>
    </div>
  );
});

export default StockCard;
