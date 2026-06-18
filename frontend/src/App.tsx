import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Row, Col, message } from 'antd';
import {
  ReloadOutlined, StockOutlined, LineChartOutlined,
  FundOutlined, ArrowUpOutlined, ArrowDownOutlined, MinusOutlined,
  GoldOutlined, ThunderboltOutlined, FireOutlined,
  FileTextOutlined, LinkOutlined, CalendarOutlined, BankOutlined,
  DollarOutlined,
} from '@ant-design/icons';
import { stockAPI, commodityAPI, announcementAPI, fundamentalAPI } from './services/api';
import { StockQuote, CommodityPrice, Announcement, KeyMetrics } from './types';
import './App.css';

const SunSvg = () => <svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>;
const MoonSvg = () => <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>;

const fmt = (v: number) => v >= 1e8 ? `${(v/1e8).toFixed(1)}亿` : v >= 1e4 ? `${(v/1e4).toFixed(1)}万` : v.toLocaleString();
const fmtTime = (d: Date) => d.toLocaleTimeString('zh-CN', { hour:'2-digit', minute:'2-digit', second:'2-digit' });

/* 中国市场：红涨绿跌 */
const UP = '#ff3b30';
const DOWN = '#34c759';
const NEUTRAL = '#8e8e93';

function App() {
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [theme, setTheme] = useState<'light'|'dark'>(() => (localStorage.getItem('theme') as 'light'|'dark') || 'dark');
  const [aShare, setAShare] = useState<StockQuote|null>(null);
  const [hkShare, setHkShare] = useState<StockQuote|null>(null);
  const [gold, setGold] = useState<CommodityPrice|null>(null);
  const [copperLME, setCopperLME] = useState<CommodityPrice|null>(null);
  const [copperSHFE, setCopperSHFE] = useState<CommodityPrice|null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [metrics, setMetrics] = useState<KeyMetrics|null>(null);
  const [flashA, setFlashA] = useState(false);
  const [flashHK, setFlashHK] = useState(false);
  const prevPriceA = useRef<number>(0);
  const prevPriceHK = useRef<number>(0);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [s, c, a, m] = await Promise.allSettled([
        stockAPI.getOverview(), commodityAPI.getOverview(),
        announcementAPI.getList('601899','cninfo',1,10), fundamentalAPI.getMetrics('601899'),
      ]);
      if (s.status==='fulfilled' && s.value.data.success) {
        const newA = s.value.data.data.a_share;
        const newHK = s.value.data.data.hk_share;
        if (newA && prevPriceA.current !== 0 && newA.price !== prevPriceA.current) setFlashA(true);
        if (newHK && prevPriceHK.current !== 0 && newHK.price !== prevPriceHK.current) setFlashHK(true);
        if (newA) prevPriceA.current = newA.price;
        if (newHK) prevPriceHK.current = newHK.price;
        setAShare(newA);
        setHkShare(newHK);
      }
      if (c.status==='fulfilled' && c.value.data.success) { setGold(c.value.data.data.gold); setCopperLME(c.value.data.data.copper_lme); setCopperSHFE(c.value.data.data.copper_shfe); }
      if (a.status==='fulfilled' && a.value.data.success) setAnnouncements(a.value.data.data);
      if (m.status==='fulfilled' && m.value.data.success) setMetrics(m.value.data.data);
      setLastUpdate(new Date());
    } catch { message.error('数据获取失败'); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const t = setInterval(fetchData, 15000); return () => clearInterval(t); }, [fetchData]);
  useEffect(() => { if (flashA) { const t = setTimeout(() => setFlashA(false), 600); return () => clearTimeout(t); } }, [flashA]);
  useEffect(() => { if (flashHK) { const t = setTimeout(() => setFlashHK(false), 600); return () => clearTimeout(t); } }, [flashHK]);

  return (
    <div className="layout">
      <nav className="nav">
        <div className="nav-inner">
          <a className="nav-brand" href="#">
            <div className="nav-logo"><StockOutlined /></div>
            <span className="nav-title">紫金矿业监控器</span>
          </a>
          <div className="nav-right">
            <span className="nav-time">{fmtTime(lastUpdate)}</span>
            <button className="theme-switch" onClick={() => setTheme(t => t==='dark'?'light':'dark')} aria-label="切换主题">
              <span className="theme-switch-icons"><SunSvg /><MoonSvg /></span>
            </button>
            <button className="btn btn-primary" onClick={fetchData} disabled={loading}>
              <ReloadOutlined spin={loading} /> 刷新
            </button>
          </div>
        </div>
      </nav>

      <main className="content">
        <div className="container">
          <section className="hero">
            <h1 className="hero-heading">紫金矿业<br/>实时行情监控</h1>
            <p className="hero-sub">A股 601899 · H股 02899 · 大宗商品 · 公告 · 基本面</p>
            <div className="hero-actions">
              <button className="btn btn-primary" onClick={fetchData}><LineChartOutlined /> 查看行情</button>
              <button className="btn btn-ghost"><FundOutlined /> 基本面分析</button>
            </div>
          </section>

          <div className="section-label">股票行情</div>
          <Row gutter={[16,16]}>
            <Col xs={24} lg={12}><StockCard data={aShare} loading={loading} flash={flashA} colorClass="card--blue" market="A" /></Col>
            <Col xs={24} lg={12}><StockCard data={hkShare} loading={loading} flash={flashHK} colorClass="card--orange" market="HK" /></Col>
          </Row>

          <div className="section-label">大宗商品</div>
          <Row gutter={[16,16]}>
            <Col xs={24} sm={8}><CommodityCard data={gold} type="gold" loading={loading} /></Col>
            <Col xs={24} sm={8}><CommodityCard data={copperLME} type="copper_lme" loading={loading} /></Col>
            <Col xs={24} sm={8}><CommodityCard data={copperSHFE} type="copper_shfe" loading={loading} /></Col>
          </Row>

          <div className="section-label">公司信息</div>
          <Row gutter={[16,16]}>
            <Col xs={24} lg={12}><AnnouncementCard data={announcements} loading={loading} /></Col>
            <Col xs={24} lg={12}><FundamentalCard metrics={metrics} loading={loading} /></Col>
          </Row>
        </div>
      </main>
    </div>
  );
}

function StockCard({ data, loading, flash, colorClass, market }: { data: StockQuote|null; loading: boolean; flash: boolean; colorClass: string; market: string }) {
  if (!data) return <div className="card"><div className="empty"><MinusOutlined style={{fontSize:24,opacity:0.3}}/>暂无数据</div></div>;
  const up = data.change_percent > 0;
  const zero = data.change_percent === 0;
  const color = zero ? NEUTRAL : up ? UP : DOWN;
  const arrow = zero ? <MinusOutlined/> : up ? <ArrowUpOutlined/> : <ArrowDownOutlined/>;

  return (
    <div className={`card ${colorClass}`}>
      <div className="card-body">
        <div className="stock-header">
          <div style={{display:'flex',alignItems:'center',gap:'0.5rem'}}>
            <span className="stock-name">{data.name}</span>
          </div>
          <span className="stock-code">{data.code}</span>
        </div>
        <div className="price-display">
          <div className={`price-value ${flash ? 'price-flash' : ''}`} style={{color}}>
            {market==='HK'?'$':'¥'}{data.price.toFixed(2)}
          </div>
          <div className="price-change">
            <span className="price-badge" style={{background:`${color}18`,color}}>{arrow} {Math.abs(data.change).toFixed(2)}</span>
            <span className="price-pct" style={{color}}>{zero?'0.00':(up?'+':'')}{data.change_percent.toFixed(2)}%</span>
          </div>
        </div>
        <div className="data-grid">
          {[
            ['今开', data.open.toFixed(2)],
            ['最高', data.high.toFixed(2), 'data-value--up'],
            ['昨收', data.pre_close.toFixed(2)],
            ['最低', data.low.toFixed(2), 'data-value--down'],
            ['成交量', fmt(data.volume)],
            ['成交额', fmt(data.amount)],
          ].map(([l,v,c]) => (
            <div className="data-cell" key={l}>
              <span className="data-label">{l}</span>
              <span className={`data-value ${c||''}`}>{v}</span>
            </div>
          ))}
        </div>
        {market==='A' && (data.pe_ratio>0 || data.pb_ratio>0) && (
          <div className="stock-footer">
            {data.pe_ratio>0 && <span className="pill">PE {data.pe_ratio.toFixed(1)}</span>}
            {data.pb_ratio>0 && <span className="pill">PB {data.pb_ratio.toFixed(2)}</span>}
          </div>
        )}
      </div>
    </div>
  );
}

function CommodityCard({ data, type, loading }: { data: CommodityPrice|null; type: string; loading: boolean }) {
  const cfg: Record<string,{title:string;icon:React.ReactNode;color:string;cls:string}> = {
    gold:       { title:'黄金',  icon:<GoldOutlined/>,        color:'#DAA520', cls:'card--gold' },
    copper_lme: { title:'LME铜', icon:<ThunderboltOutlined/>, color:'#f97316', cls:'card--orange' },
    copper_shfe:{ title:'沪铜',  icon:<FireOutlined/>,        color:'#ef4444', cls:'card--red' },
  };
  const c = cfg[type] || cfg.gold;
  if (!data) return <div className={`card ${c.cls}`}><div className="card-body commodity"><div className="commodity-icon" style={{color:c.color}}>{c.icon} {c.title}</div><div className="empty">暂无数据</div></div></div>;
  const up = data.change_percent > 0;
  const zero = data.change_percent === 0;
  const dColor = zero ? NEUTRAL : up ? UP : DOWN;

  return (
    <div className={`card ${c.cls}`}>
      <div className="card-body commodity">
        <div className="commodity-icon" style={{color:c.color}}>{c.icon} {c.title}</div>
        <div className="commodity-value" style={{color:c.color}}>{data.currency==='USD'?'$':'¥'}{data.price.toFixed(2)}</div>
        <div className="commodity-delta" style={{color:dColor}}>{zero?'0.00%':`${up?'+':''}${data.change_percent.toFixed(2)}%`}</div>
      </div>
    </div>
  );
}

function AnnouncementCard({ data, loading }: { data: Announcement[]; loading: boolean }) {
  const catColor = (c: string) => c.includes('年报')||c.includes('季报') ? '#3b82f6' : c.includes('分红') ? '#34c759' : c.includes('重大') ? '#ff3b30' : '#8b5cf6';
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
}

function FundamentalCard({ metrics, loading }: { metrics: KeyMetrics|null; loading: boolean }) {
  if (!metrics) return <div className="card"><div className="card-head"><FundOutlined style={{color:'var(--accent)'}}/> 基本面数据</div><div className="card-body"><div className="empty">暂无数据</div></div></div>;
  const fmtCap = (v: number) => !v ? '--' : v>=1e8 ? `${(v/1e8).toFixed(0)}亿` : v>=1e4 ? `${(v/1e4).toFixed(0)}万` : v.toLocaleString();
  const peColor = metrics.pe_ratio<=0 ? NEUTRAL : metrics.pe_ratio<15 ? UP : metrics.pe_ratio<30 ? '#DAA520' : DOWN;
  return (
    <div className="card">
      <div className="card-head"><FundOutlined style={{color:'var(--accent)'}}/> 基本面数据</div>
      <div className="card-body">
        <Row gutter={[12,12]}>
          <Col span={12}><div className="metric-card"><div className="metric-label">市盈率(PE)</div><div className="metric-value" style={{color:peColor}}>{metrics.pe_ratio>0?metrics.pe_ratio.toFixed(1):'--'}</div></div></Col>
          <Col span={12}><div className="metric-card"><div className="metric-label">市净率(PB)</div><div className="metric-value" style={{color:metrics.pb_ratio>1?'var(--accent)':'var(--color-up)'}}>{metrics.pb_ratio>0?metrics.pb_ratio.toFixed(2):'--'}</div></div></Col>
          <Col span={24}><div className="metric-card metric-card--highlight"><div className="metric-label"><DollarOutlined style={{marginRight:6}}/>总市值</div><div className="metric-value metric-value--lg">{fmtCap(metrics.total_market_cap)}</div></div></Col>
          <Col span={12}><div className="metric-card"><div className="metric-label">流通市值</div><div className="metric-value metric-value--sm">{fmtCap(metrics.circulating_market_cap)}</div></div></Col>
          <Col span={12}><div className="metric-card"><div className="metric-label">换手率</div><div className="metric-value metric-value--sm">{metrics.turnover_rate>0?`${metrics.turnover_rate.toFixed(2)}%`:'--'}</div></div></Col>
        </Row>
      </div>
    </div>
  );
}

export default App;
