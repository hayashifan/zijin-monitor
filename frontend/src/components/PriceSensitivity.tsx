/**
 * 价格敏感性模拟器 (v2.5)
 * 滑动金价/铜价变动，模拟净利润影响
 */
import React, { useState, useMemo, useCallback } from 'react';
import { SlidersOutlined } from '@ant-design/icons';
import type { PriceSensitivity } from '../types';
import { UP, DOWN, NEUTRAL } from './constants';

interface Props {
  data: PriceSensitivity[];
  loading: boolean;
}

// 产品颜色
const PRODUCT_COLORS: Record<string, string> = {
  '金': '#DAA520',
  '铜': '#B87333',
  '锌': '#7B868C',
};

// 默认敏感性系数（当没有数据时使用）
const DEFAULT_SENSITIVITY: Record<string, number> = {
  '金': 15.5,    // 金价每涨10%，净利润增15.5亿
  '铜': 12.3,    // 铜价每涨10%，净利润增12.3亿
  '锌': 3.2,     // 锌价每涨10%，净利润增3.2亿
};

function formatProfitImpact(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)} 亿`;
}

const PriceSensitivityCard = React.memo(function PriceSensitivityCard({ data, loading }: Props) {
  const [goldChange, setGoldChange] = useState(0);
  const [copperChange, setCopperChange] = useState(0);
  const [zincChange, setZincChange] = useState(0);

  // 从数据中提取敏感性系数
  const sensitivityMap = useMemo(() => {
    const map: Record<string, number> = {};
    data.forEach(item => {
      // 使用最接近10%变动的系数
      if (!map[item.product] || Math.abs(item.price_change_pct - 10) < Math.abs(map[item.product + '_pct'] - 10)) {
        map[item.product] = item.profit_impact;
        map[item.product + '_pct'] = item.price_change_pct;
      }
    });
    return map;
  }, [data]);

  // 计算净利润影响
  const calculateImpact = useCallback((product: string, changePct: number): number => {
    const coeff = sensitivityMap[product] || DEFAULT_SENSITIVITY[product] || 0;
    const refPct = sensitivityMap[product + '_pct'] || 10;
    // 线性外推
    return (coeff / refPct) * changePct;
  }, [sensitivityMap]);

  const goldImpact = calculateImpact('金', goldChange);
  const copperImpact = calculateImpact('铜', copperChange);
  const zincImpact = calculateImpact('锌', zincChange);
  const totalImpact = goldImpact + copperImpact + zincImpact;

  const getImpactColor = (value: number): string => {
    if (value > 0) return UP;
    if (value < 0) return DOWN;
    return NEUTRAL;
  };

  if (loading) {
    return (
      <div className="card">
        <div className="card-head">
          <SlidersOutlined style={{ color: 'var(--accent)' }} /> 价格敏感性
        </div>
        <div className="card-body">
          <div className="empty">加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-head">
        <SlidersOutlined style={{ color: 'var(--accent)' }} /> 价格敏感性
        <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
          模拟价格变动对净利润影响
        </span>
      </div>
      <div className="card-body">
        {/* 滑块控件 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* 金价 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: 600, color: PRODUCT_COLORS['金'] }}>
                金价变动
              </span>
              <span style={{
                fontWeight: 600,
                color: getImpactColor(goldImpact),
                fontSize: '0.85rem',
              }}>
                {formatProfitImpact(goldImpact)}
              </span>
            </div>
            <input
              type="range"
              min={-30}
              max={30}
              step={1}
              value={goldChange}
              onChange={(e) => setGoldChange(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                appearance: 'none',
                background: `linear-gradient(to right, ${DOWN} 0%, ${NEUTRAL} 50%, ${UP} 100%)`,
                borderRadius: '3px',
                outline: 'none',
                cursor: 'pointer',
              }}
            />
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.7rem',
              color: 'var(--text-tertiary)',
              marginTop: '0.25rem',
            }}>
              <span>-30%</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                {goldChange >= 0 ? '+' : ''}{goldChange}%
              </span>
              <span>+30%</span>
            </div>
          </div>

          {/* 铜价 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: 600, color: PRODUCT_COLORS['铜'] }}>
                铜价变动
              </span>
              <span style={{
                fontWeight: 600,
                color: getImpactColor(copperImpact),
                fontSize: '0.85rem',
              }}>
                {formatProfitImpact(copperImpact)}
              </span>
            </div>
            <input
              type="range"
              min={-30}
              max={30}
              step={1}
              value={copperChange}
              onChange={(e) => setCopperChange(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                appearance: 'none',
                background: `linear-gradient(to right, ${DOWN} 0%, ${NEUTRAL} 50%, ${UP} 100%)`,
                borderRadius: '3px',
                outline: 'none',
                cursor: 'pointer',
              }}
            />
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.7rem',
              color: 'var(--text-tertiary)',
              marginTop: '0.25rem',
            }}>
              <span>-30%</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                {copperChange >= 0 ? '+' : ''}{copperChange}%
              </span>
              <span>+30%</span>
            </div>
          </div>

          {/* 锌价 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: 600, color: PRODUCT_COLORS['锌'] }}>
                锌价变动
              </span>
              <span style={{
                fontWeight: 600,
                color: getImpactColor(zincImpact),
                fontSize: '0.85rem',
              }}>
                {formatProfitImpact(zincImpact)}
              </span>
            </div>
            <input
              type="range"
              min={-30}
              max={30}
              step={1}
              value={zincChange}
              onChange={(e) => setZincChange(Number(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                appearance: 'none',
                background: `linear-gradient(to right, ${DOWN} 0%, ${NEUTRAL} 50%, ${UP} 100%)`,
                borderRadius: '3px',
                outline: 'none',
                cursor: 'pointer',
              }}
            />
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.7rem',
              color: 'var(--text-tertiary)',
              marginTop: '0.25rem',
            }}>
              <span>-30%</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                {zincChange >= 0 ? '+' : ''}{zincChange}%
              </span>
              <span>+30%</span>
            </div>
          </div>
        </div>

        {/* 汇总影响 */}
        <div style={{
          marginTop: '1.5rem',
          padding: '1rem',
          background: totalImpact >= 0 ? 'rgba(82,196,26,0.08)' : 'rgba(255,77,79,0.08)',
          borderRadius: 'var(--radius-sm)',
          border: `1px solid ${totalImpact >= 0 ? 'rgba(82,196,26,0.2)' : 'rgba(255,77,79,0.2)'}`,
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              合计净利润影响
            </span>
            <span style={{
              fontSize: '1.25rem',
              fontWeight: 700,
              color: getImpactColor(totalImpact),
            }}>
              {formatProfitImpact(totalImpact)}
            </span>
          </div>
        </div>

        {/* 说明 */}
        <div style={{
          marginTop: '0.75rem',
          fontSize: '0.7rem',
          color: 'var(--text-tertiary)',
          lineHeight: 1.5,
        }}>
          * 基于年报敏感性系数线性外推，仅供参考
        </div>
      </div>
    </div>
  );
});

export default PriceSensitivityCard;
