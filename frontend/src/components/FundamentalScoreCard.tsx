import React from 'react';
import { Row, Col } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, MinusCircleOutlined } from '@ant-design/icons';
import { UP, DOWN, NEUTRAL } from './constants';

interface ScoreDetail {
  name: string;
  value: string;
  score: number;
  max: number;
  status: string;
}

interface ScoreDimension {
  score: number;
  max: number;
  details: ScoreDetail[];
}

interface FundamentalScoreData {
  total: number;
  max: number;
  grade: string;
  dimensions: {
    earning: ScoreDimension;    // 赚钱能力 40
    safety: ScoreDimension;     // 安全性 30
    moat: ScoreDimension;       // 护城河 20
    sector: ScoreDimension;     // 赛道 10
  };
  summary: string;
}

interface Props {
  data: FundamentalScoreData | null;
  loading: boolean;
}

const gradeColor = (g: string) => {
  if (g === 'A') return UP;
  if (g === 'B') return 'var(--accent)';
  if (g === 'C') return '#DAA520';
  return DOWN;
};

const statusIcon = (s: string) => {
  if (s === 'excellent' || s === 'good') return <CheckCircleOutlined style={{ color: DOWN, fontSize: '0.75rem' }} />;
  if (s === 'poor') return <CloseCircleOutlined style={{ color: UP, fontSize: '0.75rem' }} />;
  return <MinusCircleOutlined style={{ color: NEUTRAL, fontSize: '0.75rem' }} />;
};

function LoadingSkeleton() {
  return (
    <div className="card">
      <div className="card-head">基本面评分</div>
      <div className="card-body"><div className="empty">加载中...</div></div>
    </div>
  );
}

const DimensionBar = ({ label, score, max, color }: { label: string; score: number; max: number; color: string }) => {
  const pct = max > 0 ? (score / max * 100) : 0;
  return (
    <div style={{ marginBottom: '0.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: 4 }}>
        <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
        <span style={{ color, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{score}/{max}</span>
      </div>
      <div className="profit-bar-track">
        <div className="profit-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
};

const FundamentalScoreCard = React.memo(function FundamentalScoreCard({ data, loading }: Props) {
  if (loading && !data) return <LoadingSkeleton />;
  if (!data) return (
    <div className="card">
      <div className="card-head">基本面评分</div>
      <div className="card-body"><div className="empty">暂无评分数据</div></div>
    </div>
  );

  const { dimensions: dim } = data;

  return (
    <div className="card">
      <div className="card-head" style={{ justifyContent: 'space-between' }}>
        <span>基本面评分</span>
        <span style={{ fontSize: '1.5rem', fontWeight: 700, color: gradeColor(data.grade) }}>
          {data.grade}
        </span>
      </div>
      <div className="card-body">
        {/* 总分 */}
        <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: gradeColor(data.grade), lineHeight: 1 }}>
            {data.total}
          </div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-tertiary)' }}>/{data.max} 分</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 4 }}>{data.summary}</div>
        </div>

        {/* 四维雷达 */}
        <DimensionBar label="赚钱能力" score={dim.earning.score} max={dim.earning.max} color="var(--accent)" />
        <DimensionBar label="安全性" score={dim.safety.score} max={dim.safety.max} color={DOWN} />
        <DimensionBar label="护城河" score={dim.moat.score} max={dim.moat.max} color="#1890ff" />
        <DimensionBar label="赛道" score={dim.sector.score} max={dim.sector.max} color={UP} />

        {/* 明细（可折叠） */}
        <details style={{ marginTop: '0.75rem', fontSize: '0.75rem' }}>
          <summary style={{ cursor: 'pointer', color: 'var(--text-tertiary)' }}>评分明细</summary>
          {Object.entries(dim).map(([key, d]) => (
            <div key={key} style={{ marginTop: '0.5rem' }}>
              <div style={{ fontWeight: 600, fontSize: '0.6875rem', color: 'var(--text-secondary)', marginBottom: 4 }}>
                {key === 'earning' ? '赚钱能力' : key === 'safety' ? '安全性' : key === 'moat' ? '护城河' : '赛道'}
              </div>
              {d.details.map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '2px 0' }}>
                  {statusIcon(item.status)}
                  <span style={{ flex: 1 }}>{item.name}</span>
                  <span style={{ fontVariantNumeric: 'tabular-nums', color: 'var(--text-secondary)' }}>{item.value}</span>
                  <span style={{ fontSize: '0.625rem', color: 'var(--text-tertiary)' }}>{item.score}/{item.max}</span>
                </div>
              ))}
            </div>
          ))}
        </details>
      </div>
    </div>
  );
});

export default FundamentalScoreCard;
