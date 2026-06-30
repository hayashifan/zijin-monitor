import React, { useState, useCallback } from 'react';
import { FileTextOutlined, CalendarOutlined } from '@ant-design/icons';
import { UP, DOWN, NEUTRAL } from './constants';
import type { AnnualReport } from '../types';

interface Props {
  data: AnnualReport[];
  loading: boolean;
}

/* 报告类型标签色：只用3主色 + 中性 */
const typeStyle = (t: string): { bg: string; color: string } => {
  if (t === '年报') return { bg: 'rgba(24,144,255,0.12)', color: '#1890ff' };
  if (t === '半年报') return { bg: 'rgba(24,144,255,0.08)', color: '#1890ff' };
  if (t.includes('Q1') || t.includes('Q2')) return { bg: 'rgba(82,196,26,0.10)', color: DOWN };
  if (t.includes('Q3') || t.includes('Q4')) return { bg: 'rgba(255,77,79,0.08)', color: UP };
  return { bg: 'var(--bg-secondary)', color: NEUTRAL };
};

function LoadingSkeleton() {
  return (
    <div className="card">
      <div className="card-head"><FileTextOutlined style={{ color: 'var(--accent)' }} /> 财报时间线</div>
      <div className="card-body"><div className="empty">加载中...</div></div>
    </div>
  );
}

const ReportTimeline = React.memo(function ReportTimeline({ data, loading }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const handleToggle = useCallback((key: string) => {
    setExpanded(prev => prev === key ? null : key);
  }, []);

  if (loading && !data.length) return <LoadingSkeleton />;
  if (!data.length) return (
    <div className="card">
      <div className="card-head"><FileTextOutlined style={{ color: 'var(--accent)' }} /> 财报时间线</div>
      <div className="card-body"><div className="empty">暂无报告</div></div>
    </div>
  );

  return (
    <div className="card">
      <div className="card-head">
        <FileTextOutlined style={{ color: 'var(--accent)' }} />
        <span>财报时间线</span>
      </div>
      <div className="card-body" style={{ maxHeight: 320, overflowY: 'auto' }}>
        {data.map((report, i) => {
          const key = `${report.report_date}-${report.report_type}`;
          const isOpen = expanded === key;
          const ts = typeStyle(report.report_type);
          return (
            <div key={i}>
              <div
                className="list-item"
                style={{ cursor: 'pointer' }}
                onClick={() => handleToggle(key)}
              >
                <div className="list-icon" style={{ background: ts.bg }}>
                  <FileTextOutlined style={{ color: ts.color, fontSize: '0.875rem' }} />
                </div>
                <div className="list-content">
                  <div className="list-title">{report.title || report.report_type}</div>
                  <div className="list-meta">
                    <span style={{
                      fontSize: '0.625rem', fontWeight: 600,
                      padding: '1px 6px', borderRadius: '0.25rem',
                      background: ts.bg, color: ts.color,
                    }}>{report.report_type}</span>
                    <span className="list-date">
                      <CalendarOutlined style={{ marginRight: 4 }} />
                      {report.report_date}
                    </span>
                    {report.publish_date && (
                      <span className="list-date">发布 {report.publish_date}</span>
                    )}
                  </div>
                </div>
              </div>
              {isOpen && (
                <div style={{
                  padding: '0.75rem 1.25rem 0.75rem 3.75rem',
                  background: 'var(--bg-secondary)',
                  borderBottom: '1px solid var(--border-light)',
                  animation: 'cardEnter 0.2s var(--ease) forwards',
                }}>
                  {report.summary_llm ? (
                    <p style={{ fontSize: '0.75rem', lineHeight: 1.8, color: 'var(--text-secondary)', margin: 0 }}>
                      {report.summary_llm}
                    </p>
                  ) : (
                    <div className="empty" style={{ padding: '0.5rem 0', fontSize: '0.75rem' }}>LLM 摘要生成中...</div>
                  )}
                  {report.alert_flags && report.alert_flags.length > 0 && (
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: '0.5rem' }}>
                      {report.alert_flags.map((flag, j) => (
                        <span key={j} style={{
                          fontSize: '0.625rem', padding: '1px 6px', borderRadius: '0.25rem',
                          background: 'rgba(255,77,79,0.08)', color: UP,
                        }}>{flag}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
});

export default ReportTimeline;
