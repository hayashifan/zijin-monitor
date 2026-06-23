import React from 'react';
import { Row, Col } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';
import { QuantReport } from '../types';
import { UP, DOWN, NEUTRAL } from './constants';

interface QuantCardProps {
  data: QuantReport | null;
  loading: boolean;
}

const QuantCard = React.memo(function QuantCard({ data, loading }: QuantCardProps) {
  if (!data) return (
    <div className="card">
      <div className="card-head"><LineChartOutlined style={{color:'var(--accent)'}}/> 量化分析</div>
      <div className="card-body"><div className="empty">暂无量化报告（运行 python main.py analyze 生成）</div></div>
    </div>
  );

  const bt = data.backtest;
  const cv = data.cross_validation;
  const checks = data.validation_checks;
  const fmtPct = (v: number) => `${(v * 100).toFixed(2)}%`;
  const fmtTime = (ts: string) => ts ? new Date(ts).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) : '--';

  // ── 生成操作建议 ──
  const passedCount = Object.values(checks).filter(Boolean).length;
  const totalChecks = Object.values(checks).length;
  const allPassed = passedCount === totalChecks;

  // 信号判定：综合夏普、AUC、验证通过数
  let signal: string;
  let signalColor: string;
  let signalIcon: string;
  if (bt.sharpe_ratio >= 1.5 && cv.mean_auc >= 0.55 && passedCount >= 4) {
    signal = '强烈看多'; signalColor = UP; signalIcon = '⬆⬆';
  } else if (bt.sharpe_ratio >= 1.1 && cv.mean_auc >= 0.52 && passedCount >= 3) {
    signal = '看多'; signalColor = UP; signalIcon = '⬆';
  } else if (bt.sharpe_ratio >= 0.5 && cv.mean_auc >= 0.50) {
    signal = '中性观望'; signalColor = NEUTRAL; signalIcon = '➡';
  } else if (bt.sharpe_ratio >= 0) {
    signal = '谨慎'; signalColor = '#DAA520'; signalIcon = '⬇';
  } else {
    signal = '看空'; signalColor = DOWN; signalIcon = '⬇⬇';
  }

  // 置信度
  let confidence: string;
  let confColor: string;
  let confPct: number;
  if (cv.mean_auc >= 0.58 && passedCount >= 4) {
    confidence = '高'; confColor = UP; confPct = 85;
  } else if (cv.mean_auc >= 0.52 && passedCount >= 3) {
    confidence = '中'; confColor = '#DAA520'; confPct = 55;
  } else {
    confidence = '低'; confColor = DOWN; confPct = 25;
  }

  // 仓位建议
  let position: string;
  if (signal.includes('强烈')) position = '可重仓（≤60%）';
  else if (signal === '看多') position = '标准仓位（≤40%）';
  else if (signal === '中性观望') position = '轻仓试探（≤20%）';
  else position = '空仓等待';

  // 持有期建议
  const holdDays = bt.max_holding_days > 0 ? bt.max_holding_days : 5;
  const holdText = holdDays <= 3 ? '短线' : holdDays <= 10 ? '波段' : '中线';

  // 风险提示
  const warnings: string[] = [];
  if (bt.max_drawdown < -0.20) warnings.push(`回撤偏大（${fmtPct(bt.max_drawdown)}），严格止损`);
  if (bt.win_rate < 0.45) warnings.push(`胜率偏低（${fmtPct(bt.win_rate)}），依赖盈亏比补偿`);
  if (cv.mean_auc < 0.52) warnings.push(`AUC 仅 ${cv.mean_auc.toFixed(3)}，预测能力弱`);
  if (data.valid_factors < 3) warnings.push(`有效因子仅 ${data.valid_factors} 个，模型可能欠拟合`);
  if (data.data_points < 60) warnings.push(`样本仅 ${data.data_points} 天，统计显著性不足`);

  const cardBorderClass = allPassed ? 'card--quant-passed' : 'card--quant-failed';
  const sharpeGlow = bt.sharpe_ratio > 1.5;

  return (
    <div className={`card ${cardBorderClass}`}>
      <div className="card-head" style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <span><LineChartOutlined style={{color:'var(--accent)',marginRight:6}}/> 量化分析</span>
        <span className="list-date">{fmtTime(data.timestamp)}</span>
      </div>
      <div className="card-body">
        <Row gutter={[12,12]}>
          {/* ── 操作建议（置顶） ── */}
          <Col span={24}>
            <div style={{
              background: `${signalColor}10`,
              border: `1px solid ${signalColor}30`,
              borderRadius: 8,
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}>
              <div style={{fontSize: '1.8rem', lineHeight: 1}}>{signalIcon}</div>
              <div style={{flex: 1}}>
                <div style={{fontSize: '1.1rem', fontWeight: 700, color: signalColor}}>
                  信号：{signal}
                </div>
                <div style={{fontSize: '0.8rem', opacity: 0.7, marginTop: 2}}>
                  置信度 {confidence} · 建议 {holdText} · {position}
                </div>
              </div>
              <div style={{
                background: `${confColor}18`,
                color: confColor,
                padding: '4px 10px',
                borderRadius: 6,
                fontSize: '0.75rem',
                fontWeight: 600,
              }}>
                置信 {confidence}
              </div>
            </div>
            {/* Confidence meter */}
            <div className="confidence-meter-track">
              <div className="confidence-meter-fill" style={{ width: `${confPct}%`, background: confColor }} />
            </div>
          </Col>

          {/* ── 核心指标（4格） ── */}
          <Col span={6}>
            <div className="metric-card metric-card--highlight">
              <div className="metric-label">夏普比率</div>
              <div className={`metric-value metric-value--lg ${sharpeGlow ? 'sharpe-glow' : ''}`} style={{color: bt.sharpe_ratio > 1.1 ? UP : NEUTRAL}}>
                {bt.sharpe_ratio.toFixed(2)}
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div className="metric-card">
              <div className="metric-label">年化收益</div>
              <div className="metric-value" style={{color: bt.strategy_annual_return > 0 ? UP : DOWN}}>
                {fmtPct(bt.strategy_annual_return)}
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div className="metric-card">
              <div className="metric-label">最大回撤</div>
              <div className="metric-value" style={{color: DOWN}}>{fmtPct(bt.max_drawdown)}</div>
            </div>
          </Col>
          <Col span={6}>
            <div className="metric-card">
              <div className="metric-label">胜率/盈亏比</div>
              <div className="metric-value" style={{fontSize:'0.9rem'}}>
                {fmtPct(bt.win_rate)} / {bt.profit_loss_ratio.toFixed(2)}
              </div>
            </div>
          </Col>

          {/* ── 验证清单 ── */}
          <Col span={24}>
            <div style={{display:'flex',gap:'0.5rem',flexWrap:'wrap'}}>
              {Object.entries(checks).map(([k, v]) => (
                <span key={k} className="pill" style={{
                  background: v ? `${UP}15` : `${DOWN}15`,
                  color: v ? UP : DOWN,
                  fontSize: '0.7rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}>
                  <span style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    background: v ? UP : DOWN,
                    display: 'inline-block',
                    flexShrink: 0,
                  }} />
                  {v ? '✓' : '✗'} {k}
                </span>
              ))}
            </div>
          </Col>

          {/* ── 风险提示 ── */}
          {warnings.length > 0 && (
            <Col span={24}>
              <div style={{
                background: '#DAA52008',
                border: '1px solid #DAA52020',
                borderRadius: 6,
                padding: '8px 12px',
                fontSize: '0.75rem',
                color: '#DAA520',
              }}>
                ⚠ {warnings.join('；')}
              </div>
            </Col>
          )}

          {/* ── 详细数据（折叠） ── */}
          <Col span={24}>
            <details style={{fontSize: '0.75rem', opacity: 0.6}}>
              <summary style={{cursor: 'pointer'}}>详细数据</summary>
              <div style={{marginTop: 8, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 16px'}}>
                <span>模型: {data.model.toUpperCase()}</span>
                <span>因子: {data.total_factors} 个（{data.valid_factors} 有效）</span>
                <span>CV 准确率: {fmtPct(cv.mean_accuracy)}</span>
                <span>CV AUC: {cv.mean_auc.toFixed(3)}</span>
                <span>信息比率: {bt.information_ratio.toFixed(2)}</span>
                <span>交易次数: {bt.n_trades} / {bt.n_days} 天</span>
                <span>持仓比例: {fmtPct(bt.holding_ratio)}</span>
                <span>交易成本: {(bt.transaction_cost * 1000).toFixed(1)}‰</span>
                {data.top_factors.length > 0 && (
                  <span style={{gridColumn: '1 / -1'}}>Top 因子: {data.top_factors.slice(0, 5).join(' · ')}</span>
                )}
              </div>
            </details>
          </Col>
        </Row>
      </div>
    </div>
  );
});

export default QuantCard;
