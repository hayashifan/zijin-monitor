import React from 'react';
import { FileTextOutlined, BankOutlined, CalendarOutlined, LinkOutlined } from '@ant-design/icons';
import { Announcement } from '../types';

const catColor = (c: string) => {
  if (c.includes('年报') || c.includes('季报') || c.includes('定期')) return '#3b82f6';
  if (c.includes('业绩') || c.includes('预告')) return '#52c41a';
  if (c.includes('分红') || c.includes('派')) return '#DAA520';
  if (c.includes('重大')) return '#ff3b30';
  return '#8b5cf6';
};

const catLabel = (c: string) => c || '公告';

/** 计算相对时间 */
function relativeTime(dateStr: string): string {
  if (!dateStr) return '';
  const now = Date.now();
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  const diff = now - d.getTime();
  if (diff < 0) return dateStr;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return '刚刚';
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}天前`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}个月前`;
  return `${Math.floor(months / 12)}年前`;
}

interface AnnouncementCardProps {
  data: Announcement[];
  loading: boolean;
}

const AnnouncementCard = React.memo(function AnnouncementCard({ data, loading }: AnnouncementCardProps) {
  return (
    <div className="card">
      <div className="card-head"><FileTextOutlined style={{color:'var(--accent)'}}/> 最新公告</div>
      <div className="card-body">
        {data.length===0 && !loading ? <div className="empty">暂无公告</div> : data.map((item, i) => {
          const color = catColor(item.category);
          const relTime = relativeTime(item.publish_date);
          return (
            <a key={item.id} href={item.url} target="_blank" rel="noreferrer" className="list-item">
              <div className="list-icon" style={{background:`${color}08`}}>
                <BankOutlined style={{color:'var(--text-tertiary)',fontSize:'0.875rem'}}/>
              </div>
              <div className="list-content">
                <div className="list-title">{item.title}</div>
                <div className="list-meta">
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '0.625rem',
                    fontWeight: 600,
                    color: `${color}cc`,
                  }}>
                    <span style={{
                      width: 5,
                      height: 5,
                      borderRadius: '50%',
                      background: color,
                      display: 'inline-block',
                      flexShrink: 0,
                    }} className="cat-dot" />
                    {catLabel(item.category)}
                  </span>
                  <span className="list-date">
                    <CalendarOutlined style={{marginRight:4}}/>
                    {relTime || item.publish_date}
                  </span>
                </div>
              </div>
              <LinkOutlined className="list-link-icon" style={{color:'var(--text-tertiary)',fontSize:'0.75rem',flexShrink:0,opacity:0.5}}/>
            </a>
          );
        })}
      </div>
    </div>
  );
});

export default AnnouncementCard;
