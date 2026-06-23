import React from 'react';
import { Row, Col } from 'antd';
import { FundOutlined, DollarOutlined } from '@ant-design/icons';
import { KeyMetrics } from '../types';
import { UP, DOWN, NEUTRAL } from './constants';

interface FundamentalCardProps {
  metrics: KeyMetrics | null;
  loading: boolean;
}

const FundamentalCard = React.memo(function FundamentalCard({ metrics, loading }: FundamentalCardProps) {
  if (!metrics) return <div className="card"><div className="card-head"><FundOutlined style={{color:'var(--accent)'}}/> 基本面数据</div><div className="card-body"><div className="empty">暂无数据</div></div></div>;
  const fmtCap = (v: number) => !v ? '--' : v>=1e8 ? `${(v/1e8).toFixed(0)}亿` : v>=1e4 ? `${(v/1e4).toFixed(0)}万` : v.toLocaleString();
  const peColor = metrics.pe_ratio<=0 ? NEUTRAL : metrics.pe_ratio<15 ? UP : metrics.pe_ratio<30 ? '#DAA520' : DOWN;
  return (
    <div className="card">
      <div className="card-head"><FundOutlined style={{color:'var(--accent)'}}/> 基本面数据</div>
      <div className="card-body">
        <Row gutter={[12,12]}>
          <Col span={12}><div className="metric-card"><div className="metric-label">市盈率(PE)</div><div className="metric-value" style={{color:peColor}}>{metrics.pe_ratio>0?metrics.pe_ratio.toFixed(1):'--'}</div></div></Col>
          <Col span={12}><div className="metric-card"><div className="metric-label">市净率(PB)</div><div className="metric-value" style={{color:metrics.pb_ratio>1?'var(--accent)':'var(--color-up)'}}>{metrics.pb_ratio>0?metrics.pb_ratio.toFixed(2):'--'}</div></div></Col>
          <Col span={24}><div className="metric-card metric-card--highlight"><div className="metric-label"><DollarOutlined style={{marginRight:6}}/>总市值</div><div className="metric-value metric-value--lg">{fmtCap(metrics.total_market_cap)}</div></div></Col>
          <Col span={12}><div className="metric-card"><div className="metric-label">流通市值</div><div className="metric-value metric-value--sm">{fmtCap(metrics.circulating_market_cap)}</div></div></Col>
          <Col span={12}><div className="metric-card"><div className="metric-label">换手率</div><div className="metric-value metric-value--sm">{metrics.turnover_rate>0?`${metrics.turnover_rate.toFixed(2)}%`:'--'}</div></div></Col>
        </Row>
      </div>
    </div>
  );
});

export default FundamentalCard;
