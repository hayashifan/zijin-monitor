import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Row, Col } from 'antd';
import {
  ReloadOutlined, LineChartOutlined, FundOutlined,
  DownOutlined, UpOutlined,
} from '@ant-design/icons';
import { useStockOverview, useStockHistory } from './hooks/useStock';
import { useCommodityOverview, useGoldVolatility } from './hooks/useCommodity';
import { useAnnouncements } from './hooks/useAnnouncement';
import { useFundamentalOverview } from './hooks/useFundamental';
import { useFundamentalScore } from './hooks/useFundamentalScore';
import { useQuantReport } from './hooks/useQuant';
import { useTechnicalIndicators } from './hooks/useTechnical';
import { useReportList, useQuarterlyComparison, useReportAlerts } from './hooks/useReport';
import { KlineItem } from './components/KlineChart';
import { fmtTime } from './components/constants';
import KlineChart from './components/KlineChart';
import StockCard from './components/StockCard';
import CommodityCard from './components/CommodityCard';
import CommodityHistoryChart from './components/CommodityHistoryChart';
import AnnouncementCard from './components/AnnouncementCard';
import FundamentalCard from './components/FundamentalCard';
import FundamentalScoreCard from './components/FundamentalScoreCard';
import QuantCard from './components/QuantCard';
import CorrelationCard from './components/CorrelationCard';
import GoldVolatilityCard from './components/GoldVolatilityCard';
import GoldHoverCard from './components/GoldHoverCard';
import QuarterlyComparison from './components/QuarterlyComparison';
import ReportTimeline from './components/ReportTimeline';
import './App.css';

const SunSvg = () => <svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>;
const MoonSvg = () => <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>;

function App() {
  // ── UI 状态 ──
  const [theme, setTheme] = useState<'light'|'dark'>(() => {
    const t = localStorage.getItem('theme');
    return t === 'light' || t === 'dark' ? t : 'dark';
  });
  const [klinePeriod, setKlinePeriod] = useState<number>(30);
  const [flashA, setFlashA] = useState(false);
  const [flashHK, setFlashHK] = useState(false);
  const [annExpanded, setAnnExpanded] = useState(false);
  const prevPriceA = useRef<number>(0);
  const prevPriceHK = useRef<number>(0);
  const companySectionRef = useRef<HTMLDivElement>(null);

  // ── 数据获取 ──
  const stockQuery = useStockOverview();
  const commodityQuery = useCommodityOverview();
  const announcementQuery = useAnnouncements('601899');
  const fundamentalQuery = useFundamentalOverview('601899');
  const fundamentalScoreQuery = useFundamentalScore('601899');
  const klineQuery = useStockHistory('601899', 'A', klinePeriod);
  const quantQuery = useQuantReport();
  const technicalQuery = useTechnicalIndicators('601899', 'A', 120);
  const goldVolQuery = useGoldVolatility();
  const reportListQuery = useReportList('601899');
  const quarterlyQuery = useQuarterlyComparison('601899', 8);
  const reportAlertsQuery = useReportAlerts('601899');

  // ── 提取数据 ──
  const stockData = stockQuery.data;
  const aShare = stockData?.a_share ?? null;
  const hkShare = stockData?.hk_share ?? null;
  const commodityData = commodityQuery.data;
  const gold = commodityData?.gold ?? null;
  const copperLME = commodityData?.copper_lme ?? null;
  const copperSHFE = commodityData?.copper_shfe ?? null;
  const announcements = announcementQuery.data ?? [];
  const metrics = fundamentalQuery.data ?? null;
  const fundamentalScore = fundamentalScoreQuery.data ?? null;
  const quantReport = quantQuery.data ?? null;
  const indicators = technicalQuery.data ?? null;
  const goldVolatility = goldVolQuery.data ?? null;
  const reportList = reportListQuery.data ?? [];
  const quarterlyData = quarterlyQuery.data ?? [];
  const reportAlerts = reportAlertsQuery.data ?? [];

  // ── Loading ──
  const isLoading = stockQuery.isLoading || commodityQuery.isLoading;

  // ── 最近更新时间 ──
  const lastUpdate = stockQuery.dataUpdatedAt
    ? new Date(stockQuery.dataUpdatedAt)
    : new Date();

  // ── Flash 动画 ──
  useEffect(() => {
    if (aShare && prevPriceA.current !== 0 && aShare.price !== prevPriceA.current) setFlashA(true);
    if (aShare) prevPriceA.current = aShare.price;
  }, [aShare]);
  useEffect(() => {
    if (hkShare && prevPriceHK.current !== 0 && hkShare.price !== prevPriceHK.current) setFlashHK(true);
    if (hkShare) prevPriceHK.current = hkShare.price;
  }, [hkShare]);
  useEffect(() => { if (flashA) { const t = setTimeout(() => setFlashA(false), 600); return () => clearTimeout(t); } }, [flashA]);
  useEffect(() => { if (flashHK) { const t = setTimeout(() => setFlashHK(false), 600); return () => clearTimeout(t); } }, [flashHK]);

  // ── 主题切换 ──
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  // ── K线数据合并实时 ──
  const klineData: KlineItem[] = (() => {
    const rows = Array.isArray(klineQuery.data) ? [...klineQuery.data] : [];
    if (rows.length > 0 && aShare) {
      const today = new Date().toISOString().slice(0, 10);
      const lastDate = rows[rows.length - 1]?.date;
      if (lastDate && lastDate < today && aShare.price > 0 && !aShare.is_closed) {
        rows.push({ date: today, open: aShare.open, high: aShare.high, low: aShare.low, close: aShare.price, volume: aShare.volume });
      }
    }
    return rows;
  })();

  // ── 刷新 ──
  const handleRefresh = useCallback(() => {
    stockQuery.refetch(); commodityQuery.refetch(); announcementQuery.refetch();
    fundamentalQuery.refetch(); klineQuery.refetch(); quantQuery.refetch();
    technicalQuery.refetch(); goldVolQuery.refetch();
    reportListQuery.refetch(); quarterlyQuery.refetch(); reportAlertsQuery.refetch();
    fundamentalScoreQuery.refetch();
  }, [stockQuery, commodityQuery, announcementQuery, fundamentalQuery, klineQuery, quantQuery, technicalQuery, goldVolQuery, reportListQuery, quarterlyQuery, reportAlertsQuery, fundamentalScoreQuery]);

  // ── 跳转到公司基本面 ──
  const scrollToCompany = useCallback(() => {
    companySectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, []);

  // ── 公告折叠 ──
  const ANN_DEFAULT = 5;
  const showAnn = annExpanded ? announcements : announcements.slice(0, ANN_DEFAULT);

  return (
    <div className="layout">
      <nav className="nav">
        <div className="nav-inner">
          <a className="nav-brand" href="#">
            <img src="/logo.svg" alt="Logo" className="nav-logo-img" />
            <span className="nav-title">紫金矿业监控器</span>
          </a>
          <div className="nav-right">
            <span className="nav-time">{fmtTime(lastUpdate)}</span>
            <button className="theme-switch" onClick={() => setTheme(t => t==='dark'?'light':'dark')} aria-label="切换主题">
              <span className="theme-switch-icons"><SunSvg /><MoonSvg /></span>
            </button>
            <button className="btn btn-primary" onClick={handleRefresh} disabled={isLoading}>
              <ReloadOutlined spin={isLoading} /> 刷新
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
              <button className="btn btn-primary" onClick={handleRefresh}><LineChartOutlined /> 查看行情</button>
              <button className="btn btn-ghost" onClick={scrollToCompany}><FundOutlined /> 基本面分析</button>
            </div>
          </section>

          <div className="section-label">股票行情</div>
          <Row gutter={[16,16]}>
            <Col xs={24} lg={12}><StockCard data={aShare} loading={isLoading} flash={flashA} colorClass="card--blue" market="A" /></Col>
            <Col xs={24} lg={12}><StockCard data={hkShare} loading={isLoading} flash={flashHK} colorClass="card--orange" market="HK" /></Col>
          </Row>

          <div className="section-label" style={{display:'flex',alignItems:'center',gap:'1rem'}}>
            K线走势
            <div style={{display:'flex',gap:'0.25rem'}}>
              {[30,60,90].map(d => (
                <button key={d} className={`btn ${klinePeriod===d?'btn-outline active':'btn-outline'}`}
                  style={{padding:'2px 10px',fontSize:'0.75rem'}}
                  onClick={() => setKlinePeriod(d)}>{d}日</button>
              ))}
            </div>
          </div>
          <KlineChart data={klineData} theme={theme} period={klinePeriod} indicators={indicators?.data ?? null} />

          <div className="section-label">量化与关联分析</div>
          <Row gutter={[16,16]}>
            <Col xs={24} lg={12}><QuantCard data={quantReport} loading={quantQuery.isLoading} /></Col>
            <Col xs={24} lg={12}><CorrelationCard theme={theme} /></Col>
          </Row>

          <div className="section-label">大宗商品</div>
          <Row gutter={[16,16]}>
            <Col xs={24} sm={8}><GoldHoverCard data={gold} loading={isLoading} volatility={goldVolatility} /></Col>
            <Col xs={24} sm={8}><CommodityCard data={copperLME} type="copper_lme" loading={isLoading} /></Col>
            <Col xs={24} sm={8}><CommodityCard data={copperSHFE} type="copper_shfe" loading={isLoading} /></Col>
          </Row>
          <details style={{ marginTop: '0.75rem' }}>
            <summary style={{ cursor: 'pointer', fontSize: '0.75rem', color: 'var(--text-tertiary)', padding: '0.25rem 0' }}>
              商品历史走势
            </summary>
            <CommodityHistoryChart theme={theme} />
          </details>

          {/* ── 公司基本面与财报分析（合并大板块）── */}
          <div ref={companySectionRef} className="section-label">公司基本面与财报分析</div>
          <Row gutter={[16,16]}>
            {/* 左列：评分 + 基本面 */}
            <Col xs={24} lg={8}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <FundamentalScoreCard data={fundamentalScore} loading={fundamentalScoreQuery.isLoading} />
                <FundamentalCard data={metrics} loading={fundamentalQuery.isLoading} />
              </div>
            </Col>
            {/* 右列：同比环比（含内联预警）+ 时间线 */}
            <Col xs={24} lg={16}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <QuarterlyComparison data={quarterlyData} alerts={reportAlerts} theme={theme} loading={quarterlyQuery.isLoading} />
                <ReportTimeline data={reportList} loading={reportListQuery.isLoading} />
              </div>
            </Col>
          </Row>

          {/* ── 最新公告（折叠，底部）── */}
          <div style={{ marginTop: '1rem' }}>
            <AnnouncementCard data={showAnn} loading={announcementQuery.isLoading} />
            {announcements.length > ANN_DEFAULT && (
              <button
                className="btn btn-outline"
                style={{ width: '100%', marginTop: 8, fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
                onClick={() => setAnnExpanded(v => !v)}
              >
                {annExpanded ? <><UpOutlined /> 收起</> : <><DownOutlined /> 展开全部 {announcements.length} 条公告</>}
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
