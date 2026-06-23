import React from 'react';
import { MinusOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { StockQuote } from '../types';
import { UP, DOWN, NEUTRAL, fmt } from './constants';
import { useValueFlash } from './useFlash';

interface StockCardProps {
  data: StockQuote | null;
  loading: boolean;
  flash: boolean;
  colorClass: string;
  market: string;
}

/** 数据格子 — 带值变化闪烁 */
function DataCell({ label, value, colorClass }: { label: string; value: string; colorClass?: string }) {
  const flash = useValueFlash(value);
  return (
    <div className="data-cell">
      <span className="data-label">{label}</span>
      <span className={`data-value ${colorClass || ''} ${flash ? 'value-flash' : ''}`}>{value}</span>
    </div>
  );
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
          <DataCell label="今开" value={data.open.toFixed(2)} />
          <DataCell label="最高" value={data.high.toFixed(2)} colorClass={closed ? '' : 'data-value--up'} />
          <DataCell label="昨收" value={data.pre_close.toFixed(2)} />
          <DataCell label="最低" value={data.low.toFixed(2)} colorClass={closed ? '' : 'data-value--down'} />
          <DataCell label="成交量" value={fmt(data.volume)} />
          <DataCell label="成交额" value={fmt(data.amount)} />
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
