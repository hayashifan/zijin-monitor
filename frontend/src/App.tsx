import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Row, Col, message } from 'antd';
import ReactECharts from 'echarts-for-react';
import {
  ReloadOutlined, StockOutlined, LineChartOutlined,
  FundOutlined, ArrowUpOutlined, ArrowDownOutlined, MinusOutlined,
  GoldOutlined, ThunderboltOutlined, FireOutlined,
  FileTextOutlined, LinkOutlined, CalendarOutlined, BankOutlined,
  DollarOutlined,
} from '@ant-design/icons';
import { stockAPI, commodityAPI, announcementAPI, fundamentalAPI, quantAPI } from './services/api';
import { StockQuote, CommodityPrice, Announcement, KeyMetrics, QuantReport } from './types';
import './App.css';

const SunSvg = () => <svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>;
const MoonSvg = () => <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>;

const fmt = (v: number) => v >= 1e8 ? `${(v/1e8).toFixed(1)}亿` : v >= 1e4 ? `${(v/1e4).toFixed(1)}万` : v.toLocaleString();
const fmtTime = (d: Date) => d.toLocaleTimeString('zh-CN', { hour:'2-digit', minute:'2-digit', second:'2-digit' });

/* 中国市场：红涨绿跌 */
const UP = '#ff4d4f';
const DOWN = '#52c41a';
const NEUTRAL = '#8e8e93';

interface KlineItem {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

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
  const [metrics, setMetrics] = useState<KeyMetrics|null>(null);
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
        announcementAPI.getList('601899','cninfo',1,10), fundamentalAPI.getMetrics('601899'),
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
            <Col xs={24} lg={12}><FundamentalCard metrics={metrics} loading={loading} /></Col>
          </Row>
        </div>
      </main>
    </div>
  );
}

function KlineChart({ data, theme, period }: { data: KlineItem[]; theme: string; period: number }) {
  if (!data || data.length === 0) {
    return <div className="card"><div className="card-body"><div className="empty"><LineChartOutlined style={{fontSize:24,opacity:0.3}}/>暂无K线数据</div></div></div>;
  }
  const dates = data.map(d => d.date);
  const ohlc = data.map(d => [d.open, d.close, d.low, d.high]);
  const volumes = data.map(d => d.volume);
  const isDark = theme === 'dark';
  const option = {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: isDark ? '#1e1e2e' : '#fff',
      borderColor: isDark ? '#333' : '#e5e5e5',
      textStyle: { color: isDark ? '#e0e0e0' : '#333', fontSize: 12 },
      appendToBody: true,
      extraCssText: 'max-width: 280px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);',
    },
    grid: [
      { left: '8%', right: '3%', top: '8%', height: '55%' },
      { left: '8%', right: '3%', top: '70%', height: '20%' },
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10 }, boundaryGap: true },
      { type: 'category', data: dates, gridIndex: 1, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { show: false }, boundaryGap: true },
    ],
    yAxis: [
      { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: isDark ? '#2a2a3a' : '#f0f0f0' } }, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10 } },
      { scale: true, gridIndex: 1, splitNumber: 2, splitLine: { lineStyle: { color: isDark ? '#2a2a3a' : '#f0f0f0' } }, axisLine: { lineStyle: { color: isDark ? '#444' : '#ccc' } }, axisLabel: { color: isDark ? '#888' : '#666', fontSize: 10, formatter: (v: number) => v >= 1e8 ? `${(v/1e8).toFixed(0)}亿` : `${(v/1e4).toFixed(0)}万` } },
    ],
    dataZoom: [{ type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 }],
    series: [
      { name: 'K线', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0, data: ohlc, itemStyle: { color: UP, color0: DOWN, borderColor: UP, borderColor0: DOWN } },
      { name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumes.map((v, i) => ({ value: v, itemStyle: { color: data[i].close >= data[i].open ? `${UP}88` : `${DOWN}88` } })) },
      { name: 'MA5', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: data.map((_, i) => { if (i < 4) return undefined; return +(data.slice(i-4, i+1).reduce((s, d) => s + d.close, 0) / 5).toFixed(2); }), smooth: true, lineStyle: { width: 1, color: '#f59e0b' }, symbol: 'none' },
      { name: 'MA10', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: data.map((_, i) => { if (i < 9) return undefined; return +(data.slice(i-9, i+1).reduce((s, d) => s + d.close, 0) / 10).toFixed(2); }), smooth: true, lineStyle: { width: 1, color: '#3b82f6' }, symbol: 'none' },
    ],
  };
  return (
    <div className="card kline-card">
      <div className="card-body" style={{padding:'0.5rem'}}>
        <ReactECharts key={period} option={option} style={{height: 360}} notMerge={true} />
      </div>
    </div>
  );
}

function StockCard({ data, loading, flash, colorClass, market }: { data: StockQuote|null; loading: boolean; flash: boolean; colorClass: string; market: string }) {
  if (!data) return <div className="card"><div className="empty"><MinusOutlined style={{fontSize:24,opacity:0.3}}/>暂无数据</div></div>;
  const up = data.change_percent > 0;
  const zero = data.change_percent === 0;
  const color = zero ? NEUTRAL : up ? UP : DOWN;
  const arrow = zero ? <MinusOutlined/> : up ? <ArrowUpOutlined/> : <ArrowDownOutlined/>;
  const label = data.market_label || market;

  return (
    <div className={`card ${colorClass}`}>
      <div className="card-body">
        <div className="stock-header">
          <div style={{display:'flex',alignItems:'center',gap:'0.5rem'}}>
            <span className="stock-name">{data.name}</span>
            <span className="market-badge">{label}</span>
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

function QuantCard({ data, loading }: { data: QuantReport|null; loading: boolean }) {
  if (!data) return (
    <div className="card">
      <div className="card-head"><LineChartOutlined style={{color:'var(--accent)'}}/> 量化分析</div>
      <div className="card-body"><div className="empty">暂无量化报告（运行 python main.py analyze 生成）</div></div>
    </div>
  );

  const bt = data.backtest;
  const cv = data.cross_validation;
  const checks = data.validation_checks;
  const fmtPct = (v: number) => `${(v * 100).toFixed(2)}%`;
  const fmtTime = (ts: string) => ts ? new Date(ts).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) : '--';

  // ── 生成操作建议 ──
  const passedCount = Object.values(checks).filter(Boolean).length;
  const totalChecks = Object.values(checks).length;

  // 信号判定：综合夏普、AUC、验证通过数
  let signal: string;
  let signalColor: string;
  let signalIcon: string;
  if (bt.sharpe_ratio >= 1.5 && cv.mean_auc >= 0.55 && passedCount >= 4) {
    signal = '强烈看多'; signalColor = UP; signalIcon = '⬆⬆';
  } else if (bt.sharpe_ratio >= 1.1 && cv.mean_auc >= 0.52 && passedCount >= 3) {
    signal = '看多'; signalColor = UP; signalIcon = '⬆';
  } else if (bt.sharpe_ratio >= 0.5 && cv.mean_auc >= 0.50) {
    signal = '中性观望'; signalColor = NEUTRAL; signalIcon = '➡';
  } else if (bt.sharpe_ratio >= 0) {
    signal = '谨慎'; signalColor = '#DAA520'; signalIcon = '⬇';
  } else {
    signal = '看空'; signalColor = DOWN; signalIcon = '⬇⬇';
  }

  // 置信度
  let confidence: string;
  let confColor: string;
  if (cv.mean_auc >= 0.58 && passedCount >= 4) {
    confidence = '高'; confColor = UP;
  } else if (cv.mean_auc >= 0.52 && passedCount >= 3) {
    confidence = '中'; confColor = '#DAA520';
  } else {
    confidence = '低'; confColor = DOWN;
  }

  // 仓位建议
  let position: string;
  if (signal.includes('强烈')) position = '可重仓（≤60%）';
  else if (signal === '看多') position = '标准仓位（≤40%）';
  else if (signal === '中性观望') position = '轻仓试探（≤20%）';
  else position = '空仓等待';

  // 持有期建议
  const holdDays = bt.max_holding_days > 0 ? bt.max_holding_days : 5;
  const holdText = holdDays <= 3 ? '短线' : holdDays <= 10 ? '波段' : '中线';

  // 风险提示
  const warnings: string[] = [];
  if (bt.max_drawdown < -0.20) warnings.push(`回撤偏大（${fmtPct(bt.max_drawdown)}），严格止损`);
  if (bt.win_rate < 0.45) warnings.push(`胜率偏低（${fmtPct(bt.win_rate)}），依赖盈亏比补偿`);
  if (cv.mean_auc < 0.52) warnings.push(`AUC 仅 ${cv.mean_auc.toFixed(3)}，预测能力弱`);
  if (data.valid_factors < 3) warnings.push(`有效因子仅 ${data.valid_factors} 个，模型可能欠拟合`);
  if (data.data_points < 60) warnings.push(`样本仅 ${data.data_points} 天，统计显著性不足`);

  return (
    <div className="card">
      <div className="card-head" style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <span><LineChartOutlined style={{color:'var(--accent)',marginRight:6}}/> 量化分析</span>
        <span className="list-date">{fmtTime(data.timestamp)}</span>
      </div>
      <div className="card-body">
        <Row gutter={[12,12]}>
          {/* ── 操作建议（置顶） ── */}
          <Col span={24}>
            <div style={{
              background: `${signalColor}10`,
              border: `1px solid ${signalColor}30`,
              borderRadius: 8,
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}>
              <div style={{fontSize: '1.8rem', lineHeight: 1}}>{signalIcon}</div>
              <div style={{flex: 1}}>
                <div style={{fontSize: '1.1rem', fontWeight: 700, color: signalColor}}>
                  信号：{signal}
                </div>
                <div style={{fontSize: '0.8rem', opacity: 0.7, marginTop: 2}}>
                  置信度 {confidence} · 建议 {holdText} · {position}
                </div>
              </div>
              <div style={{
                background: `${confColor}18`,
                color: confColor,
                padding: '4px 10px',
                borderRadius: 6,
                fontSize: '0.75rem',
                fontWeight: 600,
              }}>
                置信 {confidence}
              </div>
            </div>
          </Col>

          {/* ── 核心指标（4格） ── */}
          <Col span={6}>
            <div className="metric-card metric-card--highlight">
              <div className="metric-label">夏普比率</div>
              <div className="metric-value metric-value--lg" style={{color: bt.sharpe_ratio > 1.1 ? UP : NEUTRAL}}>
                {bt.sharpe_ratio.toFixed(2)}
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div className="metric-card">
              <div className="metric-label">年化收益</div>
              <div className="metric-value" style={{color: bt.strategy_annual_return > 0 ? UP : DOWN}}>
                {fmtPct(bt.strategy_annual_return)}
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div className="metric-card">
              <div className="metric-label">最大回撤</div>
              <div className="metric-value" style={{color: DOWN}}>{fmtPct(bt.max_drawdown)}</div>
            </div>
          </Col>
          <Col span={6}>
            <div className="metric-card">
              <div className="metric-label">胜率/盈亏比</div>
              <div className="metric-value" style={{fontSize:'0.9rem'}}>
                {fmtPct(bt.win_rate)} / {bt.profit_loss_ratio.toFixed(2)}
              </div>
            </div>
          </Col>

          {/* ── 验证清单 ── */}
          <Col span={24}>
            <div style={{display:'flex',gap:'0.5rem',flexWrap:'wrap'}}>
              {Object.entries(checks).map(([k, v]) => (
                <span key={k} className="pill" style={{
                  background: v ? `${UP}15` : `${DOWN}15`,
                  color: v ? UP : DOWN,
                  fontSize: '0.7rem',
                }}>
                  {v ? '✓' : '✗'} {k}
                </span>
              ))}
            </div>
          </Col>

          {/* ── 风险提示 ── */}
          {warnings.length > 0 && (
            <Col span={24}>
              <div style={{
                background: '#DAA52008',
                border: '1px solid #DAA52020',
                borderRadius: 6,
                padding: '8px 12px',
                fontSize: '0.75rem',
                color: '#DAA520',
              }}>
                ⚠ {warnings.join('；')}
              </div>
            </Col>
          )}

          {/* ── 详细数据（折叠） ── */}
          <Col span={24}>
            <details style={{fontSize: '0.75rem', opacity: 0.6}}>
              <summary style={{cursor: 'pointer'}}>详细数据</summary>
              <div style={{marginTop: 8, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 16px'}}>
                <span>模型: {data.model.toUpperCase()}</span>
                <span>因子: {data.total_factors} 个（{data.valid_factors} 有效）</span>
                <span>CV 准确率: {fmtPct(cv.mean_accuracy)}</span>
                <span>CV AUC: {cv.mean_auc.toFixed(3)}</span>
                <span>信息比率: {bt.information_ratio.toFixed(2)}</span>
                <span>交易次数: {bt.n_trades} / {bt.n_days} 天</span>
                <span>持仓比例: {fmtPct(bt.holding_ratio)}</span>
                <span>交易成本: {(bt.transaction_cost * 1000).toFixed(1)}‰</span>
                {data.top_factors.length > 0 && (
                  <span style={{gridColumn: '1 / -1'}}>Top 因子: {data.top_factors.slice(0, 5).join(' · ')}</span>
                )}
              </div>
            </details>
          </Col>
        </Row>
      </div>
    </div>
  );
}

export default App;
