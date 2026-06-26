import React, { useState, useCallback } from 'react';
import { FileTextOutlined, BankOutlined, CalendarOutlined, LinkOutlined, CloseOutlined, FilePdfOutlined } from '@ant-design/icons';
import { Announcement } from '../types';
import { announcementAPI } from '../services/api';

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

interface AnnouncementDetail {
  id: string;
  title: string;
  content: string;
  publish_date: string;
  pdf_url: string;
  page_count: number;
  source: string;
}

interface AnnouncementCardProps {
  data: Announcement[];
  loading: boolean;
}

const AnnouncementCard = React.memo(function AnnouncementCard({ data, loading }: AnnouncementCardProps) {
  const [selectedItem, setSelectedItem] = useState<Announcement | null>(null);
  const [detail, setDetail] = useState<AnnouncementDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const handleSelect = useCallback(async (item: Announcement) => {
    setSelectedItem(item);
    setDetailLoading(true);
    setDetail(null);
    try {
      const res = await announcementAPI.getDetail(item.id);
      if (res.data?.success) {
        setDetail(res.data.data);
      }
    } catch {
      // ignore
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const handleClose = useCallback(() => {
    setSelectedItem(null);
    setDetail(null);
  }, []);

  return (
    <>
      <div className="card">
        <div className="card-head"><FileTextOutlined style={{color:'var(--accent)'}}/> 最新公告</div>
        <div className="card-body">
          {data.length===0 && !loading ? <div className="empty">暂无公告</div> : data.map((item, i) => {
            const color = catColor(item.category);
            const relTime = relativeTime(item.publish_date);
            return (
              <div key={item.id} className="list-item" style={{cursor:'pointer'}} onClick={() => handleSelect(item)}>
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
                <a href={item.url} target="_blank" rel="noreferrer" className="list-link-icon"
                   style={{color:'var(--text-tertiary)',fontSize:'0.75rem',flexShrink:0,opacity:0.5}}
                   onClick={e => e.stopPropagation()}>
                  <LinkOutlined />
                </a>
              </div>
            );
          })}
        </div>
      </div>

      {/* 公告详情弹窗 */}
      {selectedItem && (
        <div className="modal-overlay" onClick={handleClose}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                <FileTextOutlined style={{marginRight:8,color:'var(--accent)'}}/>
                {detail?.title || '公告详情'}
              </div>
              <button className="modal-close" onClick={handleClose}><CloseOutlined /></button>
            </div>
            <div className="modal-body">
              {detailLoading ? (
                <div className="empty" style={{padding:'2rem'}}>加载中...</div>
              ) : detail ? (
                <>
                  {detail.content ? (
                    <div className="announcement-content">
                      <pre style={{
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        fontFamily: 'inherit',
                        fontSize: '0.8125rem',
                        lineHeight: 1.8,
                        color: 'var(--text-primary)',
                        margin: 0,
                      }}>{detail.content}</pre>
                    </div>
                  ) : (
                    <div className="empty">暂无正文内容</div>
                  )}
                  {detail.pdf_url && (
                    <div style={{marginTop:'1rem',paddingTop:'0.75rem',borderTop:'1px solid var(--border)'}}>
                      <a href={detail.pdf_url} target="_blank" rel="noreferrer" className="btn btn-outline" style={{display:'inline-flex',alignItems:'center',gap:'0.5rem'}}>
                        <FilePdfOutlined /> 查看PDF原文
                      </a>
                    </div>
                  )}
                </>
              ) : (
                <div className="empty">详情获取失败，请
                  <a href={selectedItem.url} target="_blank" rel="noreferrer" style={{marginLeft:4}}>在东方财富查看</a>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
});

export default AnnouncementCard;
