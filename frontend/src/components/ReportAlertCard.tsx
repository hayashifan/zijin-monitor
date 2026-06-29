import React from 'react';
import { AlertOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { UP, DOWN, NEUTRAL } from './constants';
import type { ReportAlert } from '../types';

interface Props {
  data: ReportAlert[] | null;
  loading: boolean;
}

const levelIcon = (level: string) => {
  if (level === 'success') return <CheckCircleOutlined style={{ color: DOWN }} />;
  if (level === 'danger') return <AlertOutlined style={{ color: UP }} />;
  return <WarningOutlined style={{ color: NEUTRAL }} />;
};

const levelColor = (level: string) => {
  if (level === 'success') return DOWN;
  if (level === 'danger') return UP;
  return NEUTRAL;
};

function LoadingSkeleton() {
  return (
    <div className="card">
      <div className="card-head"><AlertOutlined style={{ color: 'var(--accent)' }} /> 财报预警</div>
      <div className="card-body"><div className="empty">加载中...</div></div>
    </div>
  );
}

const ReportAlertCard = React.memo(function ReportAlertCard({ data, loading }: Props) {
  if (loading && !data) return <LoadingSkeleton />;
  if (!data || data.length === 0) return (
    <div className="card">
      <div className="card-head"><AlertOutlined style={{ color: 'var(--accent)' }} /> 财报预警</div>
      <div className="card-body"><div className="empty">暂无预警</div></div>
    </div>
  );

  return (
    <div className="card">
      <div className="card-head">
        <AlertOutlined style={{ color: 'var(--accent)' }} />
        <span>财报预警</span>
      </div>
      <div className="card-body">
        {data.map((alert, i) => {
          const color = levelColor(alert.level);
          return (
            <div key={i} className="list-item">
              <div className="list-icon" style={{ background: `${color}10` }}>
                {levelIcon(alert.level)}
              </div>
              <div className="list-content">
                <div className="list-title">{alert.message}</div>
                <div className="list-meta">
                  <span className="list-date">{alert.report_date}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});

export default ReportAlertCard;
