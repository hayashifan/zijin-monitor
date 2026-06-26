import React, { useMemo, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { LineChartOutlined } from '@ant-design/icons';
import { UP, DOWN } from './constants';
import type { IndicatorDataPoint } from '../types';

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
  indicators?: IndicatorDataPoint[] | null;
}

const KlineChart = React.memo(function KlineChart({ data, theme, period, indicators }: KlineChartProps) {
  const [showBB, setShowBB] = useState(false);
  const [showRSI, setShowRSI] = useState(false);
  const [showMACD, setShowMACD] = useState(false);

  const isDark = theme === 'dark';
  const hasIndicators = indicators && indicators.length > 0;

  // 构建日期→指标映射（所有 hooks 必须在条件 return 之前）
  const indicatorMap = useMemo(() => {
    if (!hasIndicators) return null;
    const map = new Map<string, IndicatorDataPoint>();
    for (const ind of indicators!) map.set(ind.date, ind);
    return map;
  }, [indicators]);

  // 从指标数据中取值，按当前K线日期对齐
  const getIndicatorValues = (field: keyof IndicatorDataPoint): (number | null)[] => {
    if (!indicatorMap || !data.length) return data.map(() => null);
    return data.map(d => {
      const ind = indicatorMap.get(d.date);
      return ind ? (ind[field] as number | null) ?? null : null;
    });
  };

  // ECharts option（必须在条件 return 之前，否则 hooks 数量不一致会崩）
  const option = useMemo(() => {
    if (!data || data.length === 0) return null;

    const dates = data.map(d => d.date);
    const ohlc = data.map(d => [d.open, d.close, d.low, d.high]);
    const volumes = data.map(d => d.volume);

    const ma5 = hasIndicators ? getIndicatorValues('ma5') : data.map((_, i) => i >= 4 ? +(data.slice(i-4, i+1).reduce((s, d) => s + d.close, 0) / 5).toFixed(2) : undefined);
    const ma10 = hasIndicators ? getIndicatorValues('ma10') : data.map((_, i) => i >= 9 ? +(data.slice(i-9, i+1).reduce((s, d) => s + d.close, 0) / 10).toFixed(2) : undefined);
    const ma20 = getIndicatorValues('ma20');
    const ma60 = getIndicatorValues('ma60');
    const bbUpper = getIndicatorValues('bb_upper');
    const bbMiddle = getIndicatorValues('bb_middle');
    const bbLower = getIndicatorValues('bb_lower');
    const rsi14 = getIndicatorValues('rsi14');
    const dif = getIndicatorValues('dif');
    const dea = getIndicatorValues('dea');
    const macdHist = getIndicatorValues('macd');

    const showSubChart = showRSI || showMACD;
    const subChartCount = (showRSI ? 1 : 0) + (showMACD ? 1 : 0);

    const grids: any[] = [
      { left: '8%', right: '3%', top: '8%', height: showSubChart ? '40%' : '55%' },
      { left: '8%', right: '3%', top: showSubChart ? '54%' : '70%', height: '16%' },
    ];
    const xAxes: any[] = [
      { type: 'category', data: dates, gridIndex: 0, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { show: false }, boundaryGap: true },
      { type: 'category', data: dates, gridIndex: 1, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { show: !showSubChart }, boundaryGap: true },
    ];
    const yAxes: any[] = [
      { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: isDark ? '#2a2a3a' : '#f0f0f0' } }, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10 } },
      { scale: true, gridIndex: 1, splitNumber: 2, splitLine: { lineStyle: { color: isDark ? '#2a2a3a' : '#f0f0f0' } }, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10, formatter: (v: number) => v >= 1e8 ? `${(v/1e8).toFixed(0)}亿` : `${(v/1e4).toFixed(0)}万` } },
    ];

    let subGridIdx = 2;
    const subChartGrids: number[] = [];

    if (showRSI) {
      const height = subChartCount === 2 ? '12%' : '18%';
      grids.push({ left: '8%', right: '3%', top: '74%', height });
      xAxes.push({ type: 'category', data: dates, gridIndex: subGridIdx, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { show: !showMACD, color: isDark ? '#888' : '#666', fontSize: 10 }, boundaryGap: true });
      yAxes.push({ scale: true, gridIndex: subGridIdx, splitNumber: 2, min: 0, max: 100, splitLine: { lineStyle: { color: isDark ? '#2a2a3a' : '#f0f0f0' } }, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10 } });
      subChartGrids.push(subGridIdx);
      subGridIdx++;
    }

    if (showMACD) {
      grids.push({ left: '8%', right: '3%', top: '88%', height: '8%' });
      xAxes.push({ type: 'category', data: dates, gridIndex: subGridIdx, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10 }, boundaryGap: true });
      yAxes.push({ scale: true, gridIndex: subGridIdx, splitNumber: 2, splitLine: { lineStyle: { color: isDark ? '#2a2a3a' : '#f0f0f0' } }, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10 } });
      subChartGrids.push(subGridIdx);
    }

    const series: any[] = [
      { name: 'K线', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0, data: ohlc, itemStyle: { color: UP, color0: DOWN, borderColor: UP, borderColor0: DOWN } },
      { name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumes.map((v, i) => ({ value: v, itemStyle: { color: data[i].close >= data[i].open ? `${UP}88` : `${DOWN}88` } })) },
      { name: 'MA5', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma5, smooth: true, lineStyle: { width: 1, color: '#f59e0b' }, symbol: 'none' },
      { name: 'MA10', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma10, smooth: true, lineStyle: { width: 1, color: '#3b82f6' }, symbol: 'none' },
      { name: 'MA20', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma20, smooth: true, lineStyle: { width: 1, color: '#a855f7' }, symbol: 'none' },
      { name: 'MA60', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma60, smooth: true, lineStyle: { width: 1.5, color: '#ef4444', type: 'dashed' }, symbol: 'none' },
    ];

    if (showBB) {
      series.push(
        { name: 'BB上轨', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: bbUpper, smooth: true, lineStyle: { width: 1, color: '#6366f1', type: 'dotted' }, symbol: 'none' },
        { name: 'BB中轨', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: bbMiddle, smooth: true, lineStyle: { width: 1, color: '#6366f1', opacity: 0.5 }, symbol: 'none' },
        { name: 'BB下轨', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: bbLower, smooth: true, lineStyle: { width: 1, color: '#6366f1', type: 'dotted' }, symbol: 'none' },
      );
    }

    if (showRSI) {
      const rsiGridIdx = subChartGrids[0];
      series.push(
        { name: 'RSI14', type: 'line', xAxisIndex: rsiGridIdx, yAxisIndex: rsiGridIdx, data: rsi14, smooth: true, lineStyle: { width: 1.5, color: '#f59e0b' }, symbol: 'none' },
        { name: 'RSI-70', type: 'line', xAxisIndex: rsiGridIdx, yAxisIndex: rsiGridIdx, data: dates.map(() => 70), symbol: 'none', lineStyle: { width: 1, color: isDark ? '#555' : '#ddd', type: 'dashed' } },
        { name: 'RSI-30', type: 'line', xAxisIndex: rsiGridIdx, yAxisIndex: rsiGridIdx, data: dates.map(() => 30), symbol: 'none', lineStyle: { width: 1, color: isDark ? '#555' : '#ddd', type: 'dashed' } },
      );
    }

    if (showMACD) {
      const macdGridIdx = subChartGrids[showRSI ? 1 : 0];
      series.push(
        { name: 'DIF', type: 'line', xAxisIndex: macdGridIdx, yAxisIndex: macdGridIdx, data: dif, smooth: true, lineStyle: { width: 1, color: '#3b82f6' }, symbol: 'none' },
        { name: 'DEA', type: 'line', xAxisIndex: macdGridIdx, yAxisIndex: macdGridIdx, data: dea, smooth: true, lineStyle: { width: 1, color: '#f59e0b' }, symbol: 'none' },
        { name: 'MACD柱', type: 'bar', xAxisIndex: macdGridIdx, yAxisIndex: macdGridIdx, data: macdHist.map((v: number | null) => ({ value: v ?? 0, itemStyle: { color: (v ?? 0) >= 0 ? UP : `${DOWN}88` } })) },
      );
    }

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
      legend: { show: false },
      grid: grids,
      xAxis: xAxes,
      yAxis: yAxes,
      dataZoom: [{ type: 'inside', xAxisIndex: xAxes.map((_: any, i: number) => i), start: 0, end: 100 }],
      series,
    };
  }, [data, theme, period, indicators, showBB, showRSI, showMACD, indicatorMap]);

  // 条件 return 放在所有 hooks 之后
  if (!data || data.length === 0 || !option) {
    return <div className="card"><div className="card-body"><div className="empty"><LineChartOutlined style={{fontSize:24,opacity:0.3}}/>暂无K线数据</div></div></div>;
  }

  const btnStyle: React.CSSProperties = { padding: '2px 8px', fontSize: '0.7rem', borderRadius: '4px', border: '1px solid transparent', cursor: 'pointer', transition: 'all 0.15s' };

  return (
    <div className="card kline-card">
      <div className="card-body" style={{padding:'0.5rem'}}>
        <div style={{display:'flex',gap:'0.35rem',marginBottom:'0.35rem',flexWrap:'wrap',alignItems:'center'}}>
          <span style={{fontSize:'0.7rem',opacity:0.5,marginRight:'0.25rem'}}>指标</span>
          <button style={{...btnStyle, background: showBB ? '#6366f120' : 'transparent', borderColor: showBB ? '#6366f1' : (isDark ? '#444' : '#ddd'), color: showBB ? '#6366f1' : (isDark ? '#aaa' : '#666')}} onClick={() => setShowBB(v => !v)}>BB</button>
          <button style={{...btnStyle, background: showRSI ? '#f59e0b20' : 'transparent', borderColor: showRSI ? '#f59e0b' : (isDark ? '#444' : '#ddd'), color: showRSI ? '#f59e0b' : (isDark ? '#aaa' : '#666')}} onClick={() => setShowRSI(v => !v)}>RSI</button>
          <button style={{...btnStyle, background: showMACD ? '#3b82f620' : 'transparent', borderColor: showMACD ? '#3b82f6' : (isDark ? '#444' : '#ddd'), color: showMACD ? '#3b82f6' : (isDark ? '#aaa' : '#666')}} onClick={() => setShowMACD(v => !v)}>MACD</button>
          {!hasIndicators && <span style={{fontSize:'0.65rem',opacity:0.4,marginLeft:'0.5rem'}}>MA20/MA60/BB/RSI/MACD 需后端指标数据</span>}
        </div>
        <ReactECharts key={`${period}-${showBB}-${showRSI}-${showMACD}`} option={option} style={{height: (showRSI || showMACD) ? ((showRSI && showMACD) ? 480 : 420) : 360}} notMerge={true} />
      </div>
    </div>
  );
});

export default KlineChart;
