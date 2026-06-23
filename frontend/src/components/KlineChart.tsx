import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { LineChartOutlined } from '@ant-design/icons';
import { UP, DOWN } from './constants';

export interface KlineItem {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface KlineChartProps {
  data: KlineItem[];
  theme: string;
  period: number;
}

const KlineChart = React.memo(function KlineChart({ data, theme, period }: KlineChartProps) {
  if (!data || data.length === 0) {
    return <div className="card"><div className="card-body"><div className="empty"><LineChartOutlined style={{fontSize:24,opacity:0.3}}/>暂无K线数据</div></div></div>;
  }

  const isDark = theme === 'dark';

  const option = useMemo(() => {
    const dates = data.map(d => d.date);
    const ohlc = data.map(d => [d.open, d.close, d.low, d.high]);
    const volumes = data.map(d => d.volume);
    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: isDark ? '#1e1e2e' : '#fff',
        borderColor: isDark ? '#333' : '#e5e5e5',
        textStyle: { color: isDark ? '#e0e0e0' : '#333', fontSize: 12 },
        appendToBody: true,
        extraCssText: 'max-width: 280px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);',
      },
      grid: [
        { left: '8%', right: '3%', top: '8%', height: '55%' },
        { left: '8%', right: '3%', top: '70%', height: '20%' },
      ],
      xAxis: [
        { type: 'category', data: dates, gridIndex: 0, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10 }, boundaryGap: true },
        { type: 'category', data: dates, gridIndex: 1, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { show: false }, boundaryGap: true },
      ],
      yAxis: [
        { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: isDark ? '#2a2a3a' : '#f0f0f0' } }, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10 } },
        { scale: true, gridIndex: 1, splitNumber: 2, splitLine: { lineStyle: { color: isDark ? '#2a2a3a' : '#f0f0f0' } }, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10, formatter: (v: number) => v >= 1e8 ? `${(v/1e8).toFixed(0)}亿` : `${(v/1e4).toFixed(0)}万` } },
      ],
      dataZoom: [{ type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 }],
      series: [
        { name: 'K线', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0, data: ohlc, itemStyle: { color: UP, color0: DOWN, borderColor: UP, borderColor0: DOWN } },
        { name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumes.map((v, i) => ({ value: v, itemStyle: { color: data[i].close >= data[i].open ? `${UP}88` : `${DOWN}88` } })) },
        { name: 'MA5', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: data.map((_, i) => { if (i < 4) return undefined; return +(data.slice(i-4, i+1).reduce((s, d) => s + d.close, 0) / 5).toFixed(2); }), smooth: true, lineStyle: { width: 1, color: '#f59e0b' }, symbol: 'none' },
        { name: 'MA10', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: data.map((_, i) => { if (i < 9) return undefined; return +(data.slice(i-9, i+1).reduce((s, d) => s + d.close, 0) / 10).toFixed(2); }), smooth: true, lineStyle: { width: 1, color: '#3b82f6' }, symbol: 'none' },
      ],
    };
  }, [data, theme, period]);

  return (
    <div className="card kline-card">
      <div className="card-body" style={{padding:'0.5rem'}}>
        <ReactECharts key={period} option={option} style={{height: 360}} notMerge={true} />
      </div>
    </div>
  );
});

export default KlineChart;
