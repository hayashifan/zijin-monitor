import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Row, Col, message } from 'antd';
import {
  ReloadOutlined, StockOutlined, LineChartOutlined,
  FundOutlined,
} from '@ant-design/icons';
import { stockAPI, commodityAPI, announcementAPI, fundamentalAPI, quantAPI } from './services/api';
import { StockQuote, CommodityPrice, Announcement, FinancialOverview, QuantReport } from './types';
import { fmtTime } from './components/constants';
import KlineChart, { KlineItem } from './components/KlineChart';
import StockCard from './components/StockCard';
import CommodityCard from './components/CommodityCard';
import AnnouncementCard from './components/AnnouncementCard';
import FundamentalCard from './components/FundamentalCard';
import QuantCard from './components/QuantCard';
import './App.css';

const SunSvg = () => <svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>;
const MoonSvg = () => <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>;

function App() {
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [theme, setTheme] = useState<'light'|'dark'>(() => {
    const t = localStorage.getItem('theme');
    return t === 'light' || t === 'dark' ? t : 'dark';
  });
  const [aShare, setAShare] = useState<StockQuote|null>(null);
  const [hkShare, setHkShare] = useState<StockQuote|null>(null);
  const [gold, setGold] = useState<CommodityPrice|null>(null);
  const [copperLME, setCopperLME] = useState<CommodityPrice|null>(null);
  const [copperSHFE, setCopperSHFE] = useState<CommodityPrice|null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [metrics, setMetrics] = useState<FinancialOverview|null>(null);
  const [quantReport, setQuantReport] = useState<QuantReport|null>(null);
  const [klineData, setKlineData] = useState<KlineItem[]>([]);
  const [klinePeriod, setKlinePeriod] = useState<number>(30);
  const [flashA, setFlashA] = useState(false);
  const [flashHK, setFlashHK] = useState(false);
  const prevPriceA = useRef<number>(0);
  const prevPriceHK = useRef<number>(0);

  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [s, c, a, m, k, q] = await Promise.allSettled([
        stockAPI.getOverview(), commodityAPI.getOverview(),
        announcementAPI.getList('601899','cninfo',1,10), fundamentalAPI.getOverview('601899'),
        stockAPI.getHistory('601899','A',klinePeriod),
        quantAPI.getLatest(),
      ]);
      if (!mountedRef.current) return;
      if (s.status==='fulfilled' && s.value?.data?.success) {
        const newA = s.value.data.data?.a_share;
        const newHK = s.value.data.data?.hk_share;
        if (newA && prevPriceA.current !== 0 && newA.price !== prevPriceA.current) setFlashA(true);
        if (newHK && prevPriceHK.current !== 0 && newHK.price !== prevPriceHK.current) setFlashHK(true);
        if (newA) prevPriceA.current = newA.price;
        if (newHK) prevPriceHK.current = newHK.price;
        setAShare(newA ?? null);
        setHkShare(newHK ?? null);
      }
      if (c.status==='fulfilled' && c.value?.data?.success) { setGold(c.value.data.data?.gold ?? null); setCopperLME(c.value.data.data?.copper_lme ?? null); setCopperSHFE(c.value.data.data?.copper_shfe ?? null); }
      if (a.status==='fulfilled' && a.value?.data?.success) setAnnouncements(Array.isArray(a.value.data.data) ? a.value.data.data : []);
      if (m.status==='fulfilled' && m.value?.data?.success) setMetrics(m.value.data.data ?? null);
      if (k.status==='fulfilled' && k.value?.data?.success) {
        const rows: KlineItem[] = Array.isArray(k.value.data.data) ? k.value.data.data : [];
        // Append today's realtime data if last date < today
        // Skip if market is closed (price=0 or is_closed flag)
        if (rows.length > 0 && s.status==='fulfilled' && s.value?.data?.success) {
          const aShareData = s.value.data.data?.a_share;
          const today = new Date().toISOString().slice(0, 10);
          const lastDate = rows[rows.length - 1]?.date;
          if (aShareData && lastDate && lastDate < today && aShareData.price > 0 && !aShareData.is_closed) {
            rows.push({
              date: today,
              open: aShareData.open,
              high: aShareData.high,
              low: aShareData.low,
              close: aShareData.price,
              volume: aShareData.volume,
            });
          }
        }
        setKlineData(rows);
      }
      if (q.status==='fulfilled' && q.value?.data?.success) {
        setQuantReport(q.value.data.data ?? null);
      }
      setLastUpdate(new Date());
    } catch { if (mountedRef.current) message.error('数据获取失败'); } finally { if (mountedRef.current) setLoading(false); }
  }, [klinePeriod]);

  // Page Visibility API: pause polling when tab is hidden, resume + fetch immediately when visible
  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null;

    const startPolling = () => {
      if (timer) clearInterval(timer);
      timer = setInterval(fetchData, 15000);
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        if (timer) { clearInterval(timer); timer = null; }
      } else {
        fetchData(); // fetch immediately on tab becoming visible
        startPolling();
      }
    };

    fetchData(); // initial fetch
    startPolling();

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      if (timer) clearInterval(timer);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchData]);

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

          <div className="section-label" style={{display:'flex',alignItems:'center',gap:'1rem'}}>
            K线走势
            <div style={{display:'flex',gap:'0.25rem'}}>
              {[30,60,90].map(d => (
                <button key={d} className={`btn ${klinePeriod===d?'btn-primary':'btn-ghost'}`}
                  style={{padding:'2px 10px',fontSize:'0.75rem'}}
                  onClick={() => setKlinePeriod(d)}>{d}日</button>
              ))}
            </div>
          </div>
          <KlineChart data={klineData} theme={theme} period={klinePeriod} />

          <div className="section-label">量化分析</div>
          <Row gutter={[16,16]}>
            <Col xs={24}><QuantCard data={quantReport} loading={loading} /></Col>
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
            <Col xs={24} lg={12}><FundamentalCard data={metrics} loading={loading} /></Col>
          </Row>
        </div>
      </main>
    </div>
  );
}

export default App;
