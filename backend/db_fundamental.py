"""公司基本面数据表操作"""
from core.db import get_database


async def save_company_fundamental(fundamental_data: dict):
    db = get_database()
    conn = await db.get_connection()
    await conn.execute("""
        INSERT OR REPLACE INTO company_fundamental
        (stock_code, report_date, report_type, revenue, net_profit,
         gross_margin, net_margin, roe, roic, eps, bvps,
         dividend_yield, total_assets, total_liabilities)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fundamental_data.get('stock_code'),
        fundamental_data.get('report_date'),
        fundamental_data.get('report_type'),
        fundamental_data.get('revenue'),
        fundamental_data.get('net_profit'),
        fundamental_data.get('gross_margin'),
        fundamental_data.get('net_margin'),
        fundamental_data.get('roe'),
        fundamental_data.get('roic'),
        fundamental_data.get('eps'),
        fundamental_data.get('bvps'),
        fundamental_data.get('dividend_yield'),
        fundamental_data.get('total_assets'),
        fundamental_data.get('total_liabilities')
    ))
    await conn.commit()
