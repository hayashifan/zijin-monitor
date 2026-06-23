import React from 'react';
import { FileTextOutlined, BankOutlined, CalendarOutlined, LinkOutlined } from '@ant-design/icons';
import { Announcement } from '../types';

const catColor = (c: string) => c.includes('年报')||c.includes('季报') ? '#3b82f6' : c.includes('分红') ? '#34c759' : c.includes('重大') ? '#ff3b30' : '#8b5cf6';

interface AnnouncementCardProps {
  data: Announcement[];
  loading: boolean;
}

const AnnouncementCard = React.memo(function AnnouncementCard({ data, loading }: AnnouncementCardProps) {
  return (
    <div className="card">
      <div className="card-head"><FileTextOutlined style={{color:'var(--accent)'}}/> 最新公告</div>
      <div className="card-body">
        {data.length===0 && !loading ? <div className="empty">暂无公告</div> : data.map(item => (
          <a key={item.id} href={item.url} target="_blank" rel="noreferrer" className="list-item">
            <div className="list-icon" style={{background:`${catColor(item.category)}10`}}>
              <BankOutlined style={{color:catColor(item.category),fontSize:'0.875rem'}}/>
            </div>
            <div className="list-content">
              <div className="list-title">{item.title}</div>
              <div className="list-meta">
                <span className="list-tag" style={{background:`${catColor(item.category)}10`,color:catColor(item.category)}}>{item.category||'公告'}</span>
                <span className="list-date"><CalendarOutlined style={{marginRight:4}}/>{item.publish_date}</span>
              </div>
            </div>
            <LinkOutlined style={{color:'var(--accent)',fontSize:'0.75rem',flexShrink:0}}/>
          </a>
        ))}
      </div>
    </div>
  );
});

export default AnnouncementCard;
