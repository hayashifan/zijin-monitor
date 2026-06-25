import React, { useState, useEffect, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { LineChartOutlined } from '@ant-design/icons';
import { commodityAPI } from '../services/api';

export interface CommodityHistoryItem {
  trade_date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface CommodityHistoryChartProps {
  theme: string;
  defaultType?: string;
}

const typeConfig: Record<string, { label: string; color: string; unit: string }> = {
  gold: { label: '纽约金', color: '#DAA520', unit: 'USD' },
  copper_lme: { label: 'LME铜', color: '#f97316', unit: 'USD' },
  copper_shfe: { label: '沪铜', color: '#ef4444', unit: 'CNY' },
};

const CommodityHistoryChart = React.memo(function CommodityHistoryChart({ theme, defaultType = 'gold' }: CommodityHistoryChartProps) {
  const [type, setType] = useState(defaultType);
  const [days, setDays] = useState(30);
  const [data, setData] = useState<CommodityHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    commodityAPI.getHistory(type, days).then(res => {
      if (cancelled) return;
      if (res.data?.success) {
        setData(res.data.data || []);
      } else {
        setData([]);
      }
    }).catch(() => {
      if (!cancelled) setData([]);
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [type, days]);

  const isDark = theme === 'dark';
  const cfg = typeConfig[type] || typeConfig.gold;

  const option = useMemo(() => {
    if (!data || data.length === 0) return null;
    const dates = data.map(d => d.trade_date);
    const closes = data.map(d => d.close);
    const highs = data.map(d => d.high);
    const lows = data.map(d => d.low);
    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        trigger: 'axis',
        backgroundColor: isDark ? '#1e1e2e' : '#fff',
        borderColor: isDark ? '#333' : '#e5e5e5',
        textStyle: { color: isDark ? '#e0e0e0' : '#333', fontSize: 12 },
        appendToBody: true,
        extraCssText: 'box-shadow: 0 4px 20px rgba(0,0,0,0.4);',
        formatter: (params: any[]) => {
          if (!params.length) return '';
          const d = params[0].axisValue;
          const c = closes[params[0].dataIndex];
          const h = highs[params[0].dataIndex];
          const l = lows[params[0].dataIndex];
          return `<div style="font-size:12px">
            <div style="font-weight:600;margin-bottom:4px">${d}</div>
            <div>收盘: ${c?.toFixed(2)} ${cfg.unit}</div>
            <div>最高: ${h?.toFixed(2)} · 最低: ${l?.toFixed(2)}</div>
          </div>`;
        },
      },
      grid: { left: '10%', right: '5%', top: '10%', bottom: '15%' },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } },
        axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10, rotate: dates.length > 40 ? 45 : 0 },
        boundaryGap: false,
      },
      yAxis: {
        type: 'value',
        scale: true,
        splitLine: { lineStyle: { color: isDark ? '#2a2a3a' : '#f0f0f0' } },
        axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } },
        axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10 },
      },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }],
      series: [
        {
          name: cfg.label,
          type: 'line',
          data: closes,
          smooth: true,
          symbol: 'none',
          lineStyle: { width: 2, color: cfg.color },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: `${cfg.color}30` },
                { offset: 1, color: `${cfg.color}05` },
              ],
            },
          },
        },
      ],
    };
  }, [data, theme, type, cfg]);

  return (
    <div className="card">
      <div className="card-body" style={{ padding: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: '0.25rem' }}>
            {Object.entries(typeConfig).map(([key, val]) => (
              <button
                key={key}
                className={`btn ${type === key ? 'btn-outline active' : 'btn-outline'}`}
                style={{ padding: '2px 10px', fontSize: '0.75rem', borderColor: type === key ? val.color : undefined, color: type === key ? '#1a1a2e' : undefined }}
                onClick={() => setType(key)}
              >
                {val.label}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '0.25rem', marginLeft: 'auto' }}>
            {[30, 60, 90].map(d => (
              <button
                key={d}
                className={`btn ${days === d ? 'btn-outline active' : 'btn-outline'}`}
                style={{ padding: '2px 10px', fontSize: '0.75rem' }}
                onClick={() => setDays(d)}
              >
                {d}日
              </button>
            ))}
          </div>
        </div>
        {loading ? (
          <div className="empty" style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>加载中...</div>
        ) : !option ? (
          <div className="empty" style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <LineChartOutlined style={{ fontSize: 24, opacity: 0.3 }} /> 暂无历史数据
          </div>
        ) : (
          <ReactECharts key={`${type}-${days}`} option={option} style={{ height: 260 }} notMerge={true} />
        )}
      </div>
    </div>
  );
});

export default CommodityHistoryChart;
