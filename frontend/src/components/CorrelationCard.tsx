import React, { useState, useEffect, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { LinkOutlined } from '@ant-design/icons';
import { correlationAPI } from '../services/api';
import type { CommodityCorrelationMap, QuantCorrelationData } from '../types';

interface Props {
  theme: string;
}

const TYPE_LABELS: Record<string, string> = {
  gold: '纽约金',
  copper_lme: 'LME铜',
  copper_shfe: '沪铜',
};

const TYPE_COLORS: Record<string, string> = {
  gold: '#DAA520',
  copper_lme: '#f97316',
  copper_shfe: '#ef4444',
};

const FACTOR_LABELS: Record<string, string> = {
  sentiment: '舆情情绪',
  volume: '讨论量',
  topic_core: '核心话题',
  topic_commodity: '商品话题',
  engagement: '互动热度',
  authority: '权威度',
  hot_list: '热榜排名',
};

function corrLabel(r: number): { text: string; color: string } {
  const abs = Math.abs(r);
  if (abs >= 0.7) return { text: r > 0 ? '强正相关' : '强负相关', color: r > 0 ? '#52c41a' : '#ff4d4f' };
  if (abs >= 0.4) return { text: r > 0 ? '中等正相关' : '中等负相关', color: r > 0 ? '#73d13d' : '#ff7875' };
  return { text: '弱相关', color: '#8c8c8c' };
}

export default function CorrelationCard({ theme }: Props) {
  const isDark = theme === 'dark';
  const [tab, setTab] = useState<'commodity' | 'quant'>('commodity');
  const [days, setDays] = useState(60);
  const [commData, setCommData] = useState<CommodityCorrelationMap | null>(null);
  const [quantData, setQuantData] = useState<QuantCorrelationData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeType, setActiveType] = useState('gold');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const fetcher = tab === 'commodity'
      ? correlationAPI.getCommodity('gold,copper_lme,copper_shfe', days).then(r => { if (!cancelled) setCommData(r.data?.data ?? null); })
      : correlationAPI.getQuant(days).then(r => { if (!cancelled) setQuantData(r.data?.data ?? null); });
    fetcher.catch(() => {}).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [tab, days]);

  // ── 商品关联图表 ──
  const commOption = useMemo(() => {
    if (!commData || !commData[activeType]) return null;
    const item = commData[activeType];
    const dates = item.data.map(d => d.date);
    const sNorm = item.data.map(d => d.stock_normalized);
    const cNorm = item.data.map(d => d.commodity_normalized);
    const stockColor = '#3b82f6';
    const commColor = TYPE_COLORS[activeType] || '#f97316';
    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        trigger: 'axis',
        backgroundColor: isDark ? '#1e1e2e' : '#fff',
        borderColor: isDark ? '#333' : '#e5e5e5',
        textStyle: { color: isDark ? '#e0e0e0' : '#333', fontSize: 12 },
        appendToBody: true,
      },
      legend: {
        data: ['紫金矿业', TYPE_LABELS[activeType] || activeType],
        top: 0,
        textStyle: { color: isDark ? '#aaa' : '#666', fontSize: 11 },
      },
      grid: { left: '8%', right: '8%', top: '14%', bottom: '12%' },
      xAxis: {
        type: 'category', data: dates, boundaryGap: false,
        axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } },
        axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10, rotate: dates.length > 40 ? 45 : 0 },
      },
      yAxis: [
        {
          type: 'value', scale: true, position: 'left',
          splitLine: { lineStyle: { color: isDark ? '#2a2a3a' : '#f0f0f0' } },
          axisLine: { lineStyle: { color: stockColor } },
          axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10, formatter: (v: number) => v.toFixed(1) },
        },
        {
          type: 'value', scale: true, position: 'right',
          splitLine: { show: false },
          axisLine: { lineStyle: { color: commColor } },
          axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10, formatter: (v: number) => v.toFixed(1) },
        },
      ],
      dataZoom: [{ type: 'inside', start: 0, end: 100 }],
      series: [
        { name: '紫金矿业', type: 'line', data: sNorm, yAxisIndex: 0, smooth: true, symbol: 'none', lineStyle: { width: 2, color: stockColor } },
        { name: TYPE_LABELS[activeType] || activeType, type: 'line', data: cNorm, yAxisIndex: 1, smooth: true, symbol: 'none', lineStyle: { width: 2, color: commColor } },
      ],
    };
  }, [commData, activeType, isDark]);

  // ── 量化因子图表 ──
  const quantOption = useMemo(() => {
    if (!quantData?.factor_correlations) return null;
    const entries = Object.entries(quantData.factor_correlations).sort((a, b) => Math.abs(b[1].correlation) - Math.abs(a[1].correlation));
    const names = entries.map(([k]) => {
      const key = k.replace(/^F\d+_/, '');
      return FACTOR_LABELS[key] || key;
    });
    const values = entries.map(([, v]) => v.correlation);
    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        trigger: 'axis',
        backgroundColor: isDark ? '#1e1e2e' : '#fff',
        borderColor: isDark ? '#333' : '#e5e5e5',
        textStyle: { color: isDark ? '#e0e0e0' : '#333', fontSize: 12 },
        appendToBody: true,
        formatter: (params: any) => {
          const p = params[0];
          const entry = entries[p.dataIndex];
          const rawKey = entry[0].replace(/^F\d+_/, '');
          const label = FACTOR_LABELS[rawKey] || rawKey;
          return `<b>${label}</b><br/>相关系数: ${entry[1].correlation.toFixed(4)}<br/>p值: ${entry[1].p_value}`;
        },
      },
      grid: { left: '20%', right: '10%', top: '8%', bottom: '8%' },
      xAxis: {
        type: 'value',
        min: -1, max: 1,
        splitLine: { lineStyle: { color: isDark ? '#2a2a3a' : '#f0f0f0' } },
        axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10 },
      },
      yAxis: {
        type: 'category', data: names,
        axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } },
        axisLabel: { color: isDark ? '#aaa' : '#666', fontSize: 11 },
      },
      series: [{
        type: 'bar',
        data: values.map(v => ({
          value: v,
          itemStyle: { color: Math.abs(v) >= 0.1 ? (v > 0 ? '#52c41a' : '#ff4d4f') : '#8c8c8c' },
        })),
        barWidth: '60%',
      }],
    };
  }, [quantData, isDark]);

  return (
    <div className="card">
      <div className="card-body" style={{ padding: '0.75rem' }}>
        {/* Tab 切换 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: '0.25rem' }}>
            <button className={`btn ${tab === 'commodity' ? 'btn-outline active' : 'btn-outline'}`}
              style={{ padding: '2px 10px', fontSize: '0.75rem' }}
              onClick={() => setTab('commodity')}>商品关联</button>
            <button className={`btn ${tab === 'quant' ? 'btn-outline active' : 'btn-outline'}`}
              style={{ padding: '2px 10px', fontSize: '0.75rem' }}
              onClick={() => setTab('quant')}>量化关联</button>
          </div>
          <div style={{ display: 'flex', gap: '0.25rem', marginLeft: 'auto' }}>
            {[30, 60, 90].map(d => (
              <button key={d} className={`btn ${days === d ? 'btn-outline active' : 'btn-outline'}`}
                style={{ padding: '2px 10px', fontSize: '0.75rem' }}
                onClick={() => setDays(d)}>{d}日</button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="empty" style={{ height: 280 }}>加载中...</div>
        ) : tab === 'commodity' ? (
          /* ── 商品关联 ── */
          !commData || Object.keys(commData).length === 0 ? (
            <div className="empty" style={{ height: 280 }}>暂无关联数据</div>
          ) : (
            <>
              {/* 商品类型选择 + 相关系数 */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
                {Object.keys(commData).map(t => {
                  const r = commData[t].correlation;
                  const { color: corrColor } = corrLabel(r);
                  const isActive = activeType === t;
                  const typeColor = TYPE_COLORS[t] || '#8c8c8c';
                  return (
                    <button key={t}
                      style={{
                        padding: '3px 12px',
                        fontSize: '0.75rem',
                        borderRadius: '0.375rem',
                        border: `1.5px solid ${typeColor}`,
                        background: isActive ? `${typeColor}18` : 'transparent',
                        color: isDark ? '#f5f5f7' : '#1d1d1f',
                        cursor: 'pointer',
                        fontWeight: isActive ? 600 : 400,
                        transition: 'all 0.15s',
                        lineHeight: 1.5,
                      }}
                      onClick={() => setActiveType(t)}>
                      {TYPE_LABELS[t] || t}
                      <span style={{ marginLeft: 6, fontSize: '0.625rem', color: corrColor, fontWeight: 600 }}>r={r.toFixed(2)}</span>
                    </button>
                  );
                })}
              </div>
              {/* 相关系数卡片 */}
              {commData[activeType] && (() => {
                const { correlation, p_value, data_points } = commData[activeType];
                const { text, color } = corrLabel(correlation);
                return (
                  <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem', fontSize: '0.75rem', color: isDark ? '#aaa' : '#666' }}>
                    <span>相关系数: <b style={{ color, fontSize: '1rem' }}>{correlation.toFixed(4)}</b></span>
                    <span>显著性: {p_value < 0.01 ? '***' : p_value < 0.05 ? '**' : p_value < 0.1 ? '*' : 'n.s.'}</span>
                    <span>数据点: {data_points}</span>
                    <span style={{ color, fontWeight: 600 }}>{text}</span>
                  </div>
                );
              })()}
              {commOption && <ReactECharts key={`${activeType}-${days}`} option={commOption} style={{ height: 260 }} notMerge={true} />}
            </>
          )
        ) : (
          /* ── 量化关联 ── */
          !quantData ? (
            <div className="empty" style={{ height: 280 }}>暂无量化数据</div>
          ) : (
            <>
              {/* 回测摘要 */}
              {quantData.backtest_summary && (() => {
                const bt = quantData.backtest_summary;
                return (
                  <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '0.75rem', flexWrap: 'wrap', fontSize: '0.75rem', color: isDark ? '#aaa' : '#666' }}>
                    <span>夏普比率: <b style={{ color: bt.sharpe_ratio > 1 ? '#52c41a' : '#faad14' }}>{bt.sharpe_ratio?.toFixed(2)}</b></span>
                    <span>胜率: <b>{(bt.win_rate * 100).toFixed(1)}%</b></span>
                    <span>策略年化: <b style={{ color: bt.strategy_annual_return > 0 ? '#52c41a' : '#ff4d4f' }}>{(bt.strategy_annual_return * 100).toFixed(1)}%</b></span>
                    <span>基准年化: <b>{(bt.benchmark_annual_return * 100).toFixed(1)}%</b></span>
                    <span>最大回撤: <b style={{ color: '#ff4d4f' }}>{(bt.max_drawdown * 100).toFixed(1)}%</b></span>
                    <span>准确率: <b>{(bt.mean_accuracy * 100).toFixed(1)}%</b></span>
                    <span>交易次数: <b>{bt.n_trades}</b></span>
                  </div>
                );
              })()}
              {/* 因子相关性图 */}
              {quantOption && <ReactECharts key={`quant-${days}`} option={quantOption} style={{ height: 220 }} notMerge={true} />}
              {/* 顶部因子 */}
              {quantData.backtest_summary?.top_factors && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.6875rem', color: isDark ? '#888' : '#999' }}>
                  关键因子: {quantData.backtest_summary.top_factors.map(f => {
                    const key = f.replace(/^F\d+_/, '');
                    return FACTOR_LABELS[key] || key;
                  }).join(', ')}
                </div>
              )}
            </>
          )
        )}
      </div>
    </div>
  );
}
