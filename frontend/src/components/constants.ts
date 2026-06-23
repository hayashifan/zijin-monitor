/* 中国市场：红涨绿跌 */
export const UP = '#ff4d4f';
export const DOWN = '#52c41a';
export const NEUTRAL = '#8e8e93';

export const fmt = (v: number) => v >= 1e8 ? `${(v/1e8).toFixed(1)}亿` : v >= 1e4 ? `${(v/1e4).toFixed(1)}万` : v.toLocaleString();
export const fmtTime = (d: Date) => d.toLocaleTimeString('zh-CN', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
