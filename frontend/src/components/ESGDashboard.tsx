/**
 * ESG仪表盘 (v2.5)
 * 安全、环保、社会指标
 */
import React from 'react';
import { SafetyOutlined, EnvironmentOutlined, TeamOutlined } from '@ant-design/icons';
import type { ESGData } from '../types';
import { UP, DOWN, NEUTRAL } from './constants';

interface Props {
  data: ESGData[];
  loading: boolean;
}

function formatValue(value: number | null, unit: string, reverse: boolean = false): string {
  if (value === null) return '-';
  const formatted = value < 1 ? value.toFixed(3) : value < 100 ? value.toFixed(1) : value.toFixed(0);
  return `${formatted} ${unit}`;
}

function getStatusColor(value: number | null, threshold: number, reverse: boolean = false): string {
  if (value === null) return NEUTRAL;
  if (reverse) {
    return value <= threshold ? UP : value <= threshold * 1.5 ? '#faad14' : DOWN;
  }
  return value >= threshold ? UP : value >= threshold * 0.7 ? '#faad14' : DOWN;
}

interface MetricCardProps {
  icon: React.ReactNode;
  title: string;
  value: number | null;
  unit: string;
  threshold: number;
  reverse?: boolean;
  description: string;
}

function MetricCard({ icon, title, value, unit, threshold, reverse = false, description }: MetricCardProps) {
  const color = getStatusColor(value, threshold, reverse);
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '0.5rem',
      padding: '0.75rem',
      background: 'var(--bg-page)',
      borderRadius: 'var(--radius-sm)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ color: 'var(--accent)', fontSize: '1rem' }}>{icon}</span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{title}</span>
      </div>
      <div style={{
        fontSize: '1.25rem',
        fontWeight: 700,
        color: value !== null ? color : 'var(--text-tertiary)',
      }}>
        {formatValue(value, unit, reverse)}
      </div>
      <div style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', lineHeight: 1.4 }}>
        {description}
      </div>
    </div>
  );
}

const ESGDashboard = React.memo(function ESGDashboard({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="card">
        <div className="card-head">
          <SafetyOutlined style={{ color: 'var(--accent)' }} /> ESG 指标
        </div>
        <div className="card-body">
          <div className="empty">加载中...</div>
        </div>
      </div>
    );
  }

  const latest = data && data.length > 0 ? data[0] : null;

  return (
    <div className="card">
      <div className="card-head">
        <SafetyOutlined style={{ color: 'var(--accent)' }} /> ESG 指标
        {latest && (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
            {latest.year} 年度
          </span>
        )}
      </div>
      <div className="card-body">
        {!latest ? (
          <div className="empty">暂无数据</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* 安全 */}
            <div>
              <div style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
              }}>
                <SafetyOutlined /> 安全
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <MetricCard
                  icon={<SafetyOutlined />}
                  title="LTIFR"
                  value={latest.ltifr}
                  unit=""
                  threshold={0.2}
                  reverse
                  description="百万工时损工率，越低越好"
                />
                <MetricCard
                  icon={<SafetyOutlined />}
                  title="TRIFR"
                  value={latest.trifr}
                  unit=""
                  threshold={1.0}
                  reverse
                  description="可记录伤害率，越低越好"
                />
              </div>
            </div>

            {/* 环保 */}
            <div>
              <div style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
              }}>
                <EnvironmentOutlined /> 环保
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <MetricCard
                  icon={<EnvironmentOutlined />}
                  title="碳排放强度"
                  value={latest.carbon_intensity}
                  unit="tCO₂/t"
                  threshold={0.5}
                  reverse
                  description="吨CO₂/吨矿，越低越好"
                />
                <MetricCard
                  icon={<EnvironmentOutlined />}
                  title="水循环利用率"
                  value={latest.water_recycle_rate}
                  unit="%"
                  threshold={80}
                  description="水资源循环利用比例"
                />
                <MetricCard
                  icon={<EnvironmentOutlined />}
                  title="综合能耗"
                  value={latest.energy_intensity}
                  unit="tce/t"
                  threshold={0.3}
                  reverse
                  description="吨标煤/吨矿，越低越好"
                />
                <MetricCard
                  icon={<EnvironmentOutlined />}
                  title="绿化面积"
                  value={latest.greening_area}
                  unit="公顷"
                  threshold={500}
                  description="矿区绿化复垦面积"
                />
              </div>
            </div>

            {/* 社会 */}
            <div>
              <div style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
              }}>
                <TeamOutlined /> 社会
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <MetricCard
                  icon={<TeamOutlined />}
                  title="本地化雇佣"
                  value={latest.local_employment_rate}
                  unit="%"
                  threshold={90}
                  description="当地员工雇佣比例"
                />
                <MetricCard
                  icon={<TeamOutlined />}
                  title="社区投资"
                  value={latest.community_investment}
                  unit="万元"
                  threshold={1000}
                  description="社区发展投入金额"
                />
              </div>
            </div>

            {/* 环境事件 */}
            {latest.env_incidents !== null && latest.env_incidents > 0 && (
              <div style={{
                padding: '0.75rem',
                background: 'rgba(255,77,79,0.08)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid rgba(255,77,79,0.2)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}>
                <span style={{ color: DOWN, fontWeight: 600 }}>
                  ⚠ {latest.env_incidents} 起环境事件
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

export default ESGDashboard;
