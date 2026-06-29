"""定期报告数据表操作"""
import json
from datetime import datetime
from typing import Optional, List, Dict
from core.db import get_database


async def save_report(report_data: dict):
    """保存定期报告（UPSERT）"""
    db = get_database()
    conn = await db.get_connection()
    await conn.execute("""
        INSERT OR REPLACE INTO annual_report
        (stock_code, report_type, report_date, title, pdf_url,
         publish_date, summary_llm, key_metrics, alert_flags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_data.get('stock_code'),
        report_data.get('report_type'),
        report_data.get('report_date'),
        report_data.get('title'),
        report_data.get('pdf_url'),
        report_data.get('publish_date'),
        report_data.get('summary_llm'),
        json.dumps(report_data.get('key_metrics'), ensure_ascii=False) if report_data.get('key_metrics') else None,
        json.dumps(report_data.get('alert_flags'), ensure_ascii=False) if report_data.get('alert_flags') else None,
    ))
    await conn.commit()


async def save_reports_batch(reports: List[dict]):
    """批量保存定期报告"""
    if not reports:
        return
    db = get_database()
    conn = await db.get_connection()
    rows = []
    for r in reports:
        rows.append((
            r.get('stock_code'),
            r.get('report_type'),
            r.get('report_date'),
            r.get('title'),
            r.get('pdf_url'),
            r.get('publish_date'),
            r.get('summary_llm'),
            json.dumps(r.get('key_metrics'), ensure_ascii=False) if r.get('key_metrics') else None,
            json.dumps(r.get('alert_flags'), ensure_ascii=False) if r.get('alert_flags') else None,
        ))
    await conn.executemany("""
        INSERT OR REPLACE INTO annual_report
        (stock_code, report_type, report_date, title, pdf_url,
         publish_date, summary_llm, key_metrics, alert_flags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    await conn.commit()


async def get_reports(stock_code: str, limit: int = 20) -> List[dict]:
    """获取定期报告列表"""
    db = get_database()
    conn = await db.get_connection()
    cursor = await conn.execute("""
        SELECT * FROM annual_report
        WHERE stock_code = ?
        ORDER BY report_date DESC
        LIMIT ?
    """, (stock_code, limit))
    rows = await cursor.fetchall()
    results = []
    for row in rows:
        d = dict(row)
        if d.get('key_metrics'):
            d['key_metrics'] = json.loads(d['key_metrics'])
        if d.get('alert_flags'):
            d['alert_flags'] = json.loads(d['alert_flags'])
        results.append(d)
    return results


async def get_report_detail(stock_code: str, report_date: str) -> Optional[dict]:
    """获取单期报告详情"""
    db = get_database()
    conn = await db.get_connection()
    cursor = await conn.execute("""
        SELECT * FROM annual_report
        WHERE stock_code = ? AND report_date = ?
        ORDER BY report_type DESC
        LIMIT 1
    """, (stock_code, report_date))
    row = await cursor.fetchone()
    if not row:
        return None
    d = dict(row)
    if d.get('key_metrics'):
        d['key_metrics'] = json.loads(d['key_metrics'])
    if d.get('alert_flags'):
        d['alert_flags'] = json.loads(d['alert_flags'])
    return d


async def update_llm_summary(stock_code: str, report_date: str, summary: str):
    """更新 LLM 摘要"""
    db = get_database()
    conn = await db.get_connection()
    await conn.execute("""
        UPDATE annual_report SET summary_llm = ?
        WHERE stock_code = ? AND report_date = ?
    """, (summary, stock_code, report_date))
    await conn.commit()


async def update_alert_flags(stock_code: str, report_date: str, alerts: List[str]):
    """更新预警标记"""
    db = get_database()
    conn = await db.get_connection()
    await conn.execute("""
        UPDATE annual_report SET alert_flags = ?
        WHERE stock_code = ? AND report_date = ?
    """, (json.dumps(alerts, ensure_ascii=False), stock_code, report_date))
    await conn.commit()
