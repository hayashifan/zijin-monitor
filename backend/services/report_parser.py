"""
年报解析服务 — PDF下载 + DeepSeek提取矿山产量/板块财务/ESG数据
数据源：巨潮资讯网 → PDF → DeepSeek LLM → 结构化JSON → DB
"""
import json
import logging
import os
import asyncio
import tempfile
from datetime import datetime
from typing import Optional, List, Dict

import requests
from core.http import get_sync
from core.cache import CacheManager
import config
from services.stock_registry import StockRegistry

logger = logging.getLogger(__name__)

# 缓存
_cache = CacheManager(max_size=50, default_ttl=86400)

# PDF存储目录
PDF_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'annual_reports')
os.makedirs(PDF_DIR, exist_ok=True)


def _call_deepseek(prompt: str, max_tokens: int = 4096) -> Optional[str]:
    """调用DeepSeek API"""
    api_key = config.DEEPSEEK_API_KEY
    if not api_key:
        logger.warning("report_parser.deepseek_api_key_not_configured")
        return None

    try:
        resp = requests.post(
            f"{config.DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.DEEPSEEK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("report_parser.deepseek_call_failed error=%s", e)
        return None


def _extract_json(text: str) -> Optional[dict]:
    """从LLM响应中提取JSON"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取```json ... ```块
    import re
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试提取第一个 [ 或 { 开始的JSON
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

    return None


class ReportParser:
    """年报解析服务"""

    def download_annual_report(self, stock_code: str = config.DEFAULT_STOCK, year: int = 2025) -> Optional[str]:
        """从巨潮下载年报PDF"""
        cache_key = f"report_pdf_{stock_code}_{year}"
        cached = _cache.get(cache_key)
        if cached:
            return cached

        pdf_path = os.path.join(PDF_DIR, f"{stock_code}_{year}_annual.pdf")
        if os.path.exists(pdf_path):
            _cache.set(cache_key, pdf_path, ttl=86400)
            return pdf_path

        try:
            # 巨潮全文搜索API
            company_name = StockRegistry.get_or_default(stock_code).name or stock_code
            search_url = "http://www.cninfo.com.cn/new/fulltextSearch/full"
            search_params = {
                'searchkey': f'{company_name} {year}年年度报告',
                'sdate': f'{year + 1}-01-01',
                'edate': f'{year + 1}-12-31',
                'isfulltext': 'false',
                'sortName': 'pubdate',
                'sortType': 'desc',
                'pageNum': 1,
                'pageSize': 10,
            }
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.cninfo.com.cn',
            })
            resp = session.get(search_url, params=search_params, timeout=15)
            data = resp.json()

            results = data.get('announcements', [])
            if not results:
                logger.info("report_parser.cninfo_search_no_results")
                return None

            # 查找年报（非摘要）
            for ann in results:
                title = ann.get('announcementTitle', '').replace('<em>', '').replace('</em>', '')
                if '年度报告' in title and '摘要' not in title:
                    adjunct_url = ann.get('adjunctUrl', '')
                    if adjunct_url:
                        pdf_url = f"http://static.cninfo.com.cn/{adjunct_url}"
                        pdf_resp = session.get(pdf_url, timeout=60)
                        if pdf_resp.status_code == 200 and len(pdf_resp.content) > 10000:
                            with open(pdf_path, 'wb') as f:
                                f.write(pdf_resp.content)
                            _cache.set(cache_key, pdf_path, ttl=86400)
                            logger.info("report_parser.annual_report_downloaded path=%s", pdf_path)
                            return pdf_path

            logger.info("report_parser.annual_report_not_found year=%d", year)
            return None

        except Exception as e:
            logger.warning("report_parser.download_annual_report_failed error=%s", e)
            return None

    def extract_text_from_pdf(self, pdf_path: str, max_pages: int = 100) -> str:
        """从PDF提取文本（前N页）"""
        try:
            import fitz  # pymupdf
            doc = fitz.open(pdf_path)
            text_parts = []
            for i, page in enumerate(doc):
                if i >= max_pages:
                    break
                text_parts.append(page.get_text())
            doc.close()
            return '\n'.join(text_parts)
        except ImportError:
            # 备用：用pdfminer
            try:
                from pdfminer.high_level import extract_text
                return extract_text(pdf_path, maxpages=max_pages)
            except ImportError:
                logger.warning("report_parser.pdf_library_missing")
                return ""

    def parse_production_data(self, report_text: str, year: int = 2025, stock_code: str = config.DEFAULT_STOCK) -> List[dict]:
        """用DeepSeek从年报文本中提取矿山产量数据"""
        company_name = StockRegistry.get_or_default(stock_code).name or "该公司"
        # 搜索产量相关段落（更宽泛的关键词）
        keywords = ['矿产金', '矿产铜', '矿产锌', '产量', '金矿', '铜矿', '紫金山',
                     '卡莫阿', '科卢韦齐', '玉龙', '巨龙', '陇南', '宝力格', '内维什',
                     '奥拉多', '罗斯贝尔', '波格拉', '武里蒂卡', '丘卡卢', '阿瑞那',
                     '选矿', '采矿', '精矿', '金属量', '矿端']
        lines = report_text.split('\n')
        relevant = []
        seen = set()
        for i, line in enumerate(lines):
            if any(kw in line for kw in keywords):
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                for j in range(start, end):
                    if j not in seen:
                        seen.add(j)
                        relevant.append(lines[j])

        # 如果关键词搜索结果太少，用全文前30000字
        context = '\n'.join(relevant) if len(relevant) > 20 else report_text[:30000]

        prompt = f"""你是矿业财报数据提取专家。以下内容来自{company_name}{year}年年报。

请提取所有矿山的产量数据，严格按以下JSON格式输出（不要输出其他内容）：
```json
[{{
  "mine_name": "矿山名称",
  "product": "金/铜/锌/银/钴",
  "mine_output": 矿端产量数字,
  "smelter_output": 冶炼端产量数字,
  "unit": "吨/万吨",
  "plan_output": 计划产量数字,
  "completion_rate": 完成率百分比数字,
  "ore_treated": 处理矿量数字(万吨),
  "grade": 入选品位百分比数字,
  "recovery": 回收率百分比数字
}}]
```
如果某字段在文中未提及，填null。只输出JSON，不要解释。

年报内容：
{context}"""

        result = _call_deepseek(prompt, max_tokens=4096)
        if not result:
            return []

        parsed = _extract_json(result)
        if isinstance(parsed, list):
            return parsed
        return []

    def parse_segment_finance(self, report_text: str, year: int = 2025, stock_code: str = config.DEFAULT_STOCK) -> List[dict]:
        """用DeepSeek从年报文本中提取板块财务数据"""
        company_name = StockRegistry.get_or_default(stock_code).name or "该公司"
        keywords = ['分产品', '分行业', '营业收入', '营业成本', '毛利率', '金产品', '铜产品', '锌产品']
        lines = report_text.split('\n')
        relevant_lines = []
        capturing = False
        capture_count = 0

        for line in lines:
            if any(kw in line for kw in keywords):
                capturing = True
                capture_count = 0
            if capturing:
                relevant_lines.append(line)
                capture_count += 1
                if capture_count > 300:
                    capturing = False

        context = '\n'.join(relevant_lines) if relevant_lines else report_text[:15000]

        prompt = f"""你是矿业财报数据提取专家。以下内容来自{company_name}{year}年年报。

请提取各产品板块的财务数据，严格按以下JSON格式输出：
```json
[{{
  "segment": "金/铜/锌/其他",
  "revenue": 营业收入(亿元),
  "cost": 营业成本(亿元),
  "gross_profit": 毛利(亿元),
  "gross_margin": 毛利率百分比,
  "c1_cost": C1现金成本数字,
  "aisc": AISC数字,
  "cost_unit": "美元/盎司 或 美元/磅 或 null"
}}]
```
如果某字段在文中未提及，填null。只输出JSON，不要解释。

年报内容：
{context}"""

        result = _call_deepseek(prompt, max_tokens=2048)
        if not result:
            return []

        parsed = _extract_json(result)
        if isinstance(parsed, list):
            return parsed
        return []

    def parse_esg_data(self, report_text: str, year: int = 2025, stock_code: str = config.DEFAULT_STOCK) -> dict:
        """用DeepSeek从年报/ESG报告中提取ESG数据"""
        company_name = StockRegistry.get_or_default(stock_code).name or "该公司"
        keywords = ['安全', '环保', 'LTIFR', '碳排放', '水循环', '能耗', '社区', '绿化']
        lines = report_text.split('\n')
        relevant_lines = []
        capturing = False
        capture_count = 0

        for line in lines:
            if any(kw in line for kw in keywords):
                capturing = True
                capture_count = 0
            if capturing:
                relevant_lines.append(line)
                capture_count += 1
                if capture_count > 200:
                    capturing = False

        context = '\n'.join(relevant_lines) if relevant_lines else report_text[:10000]

        prompt = f"""你是矿业ESG数据提取专家。以下内容来自{company_name}{year}年年报或ESG报告。

请提取ESG相关数据，严格按以下JSON格式输出：
```json
{{
  "ltifr": 百万工时损工率,
  "trifr": 可记录伤害率,
  "carbon_intensity": 碳排放强度(吨CO2/吨矿),
  "water_recycle_rate": 水循环利用率百分比,
  "energy_intensity": 综合能耗(吨标煤/吨矿),
  "community_investment": 社区投资(万元),
  "local_employment_rate": 本地化雇佣率百分比,
  "greening_area": 绿化面积(公顷),
  "land_reclamation_rate": 土地复垦率百分比,
  "env_incidents": 环境事件数
}}
```
如果某字段在文中未提及，填null。只输出JSON，不要解释。

报告内容：
{context}"""

        result = _call_deepseek(prompt, max_tokens=1024)
        if not result:
            return {}

        parsed = _extract_json(result)
        if isinstance(parsed, dict):
            return parsed
        return {}

    async def parse_annual_report(self, stock_code: str = config.DEFAULT_STOCK, year: int = 2025) -> dict:
        """完整解析流程：下载 → 提取文本 → LLM解析 → 返回结构化数据"""
        # 1. 下载PDF
        pdf_path = await asyncio.to_thread(self.download_annual_report, stock_code, year)
        if not pdf_path:
            return {"error": "年报下载失败"}

        # 2. 提取文本
        text = await asyncio.to_thread(self.extract_text_from_pdf, pdf_path)
        if not text:
            return {"error": "PDF文本提取失败"}

        logger.info("report_parser.annual_report_text_length length=%d", len(text))

        # 3. 并行解析三个维度
        production_task = asyncio.to_thread(self.parse_production_data, text, year, stock_code)
        finance_task = asyncio.to_thread(self.parse_segment_finance, text, year, stock_code)
        esg_task = asyncio.to_thread(self.parse_esg_data, text, year, stock_code)

        production, finance, esg = await asyncio.gather(
            production_task, finance_task, esg_task
        )

        return {
            "year": year,
            "stock_code": stock_code,
            "text_length": len(text),
            "production": production,
            "segment_finance": finance,
            "esg": esg,
            "parsed_at": datetime.now().isoformat(),
        }


# 单例
report_parser = ReportParser()
