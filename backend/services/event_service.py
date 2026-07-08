"""
事件服务 — 公告智能分类 + 券商研报归因 + 事件-股价关联 + 社交情绪
核心理念：EchoPai式的事件驱动，每条公告都是一个信号
"""
import json
import logging
import re
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from core.cache import CacheManager
import config

logger = logging.getLogger(__name__)

_cache = CacheManager(max_size=100, default_ttl=3600)

# ── 事件类型定义 ──
EVENT_TYPES = {
    'production': {'label': '产量变动', 'icon': '⚒️', 'color': '#52c41a'},
    'financial': {'label': '财务事件', 'icon': '💰', 'color': '#DAA520'},
    'personnel': {'label': '人事变动', 'icon': '👤', 'color': '#1890ff'},
    'safety': {'label': '安全环保', 'icon': '⚠️', 'color': '#ff4d4f'},
    'ma': {'label': '并购重组', 'icon': '🤝', 'color': '#722ed1'},
    'esg': {'label': 'ESG', 'icon': '🌱', 'color': '#13c2c2'},
    'operation': {'label': '运营动态', 'icon': '🏭', 'color': '#faad14'},
    'dividend': {'label': '分红派息', 'icon': '📊', 'color': '#eb2f96'},
    'regulation': {'label': '监管合规', 'icon': '📋', 'color': '#8c8c8c'},
    'other': {'label': '其他', 'icon': '📌', 'color': '#595959'},
}

IMPACT_LEVELS = {
    'positive': {'label': '利好', 'color': '#ff4d4f'},
    'negative': {'label': '利空', 'color': '#52c41a'},
    'neutral': {'label': '中性', 'color': '#8c8c8c'},
}


def _call_deepseek(prompt: str, max_tokens: int = 1024) -> Optional[str]:
    """调用DeepSeek API"""
    api_key = config.DEEPSEEK_API_KEY
    if not api_key:
        return None
    try:
        resp = requests.post(
            f"{config.DEEPSEEK_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": config.DEEPSEEK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("event.deepseek_call_failed error=%s", e)
        return None


def _extract_json(text: str) -> Optional[dict]:
    """从LLM响应中提取JSON"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
    return None


class EventService:
    """事件服务"""

    def classify_event(self, title: str, content: str = "") -> dict:
        """用DeepSeek对公告进行事件分类"""
        # 先用关键词快速分类（省token）
        quick = self._quick_classify(title)
        if quick['confidence'] == 'high':
            return quick

        # 关键词不确定时用LLM
        context = f"标题：{title}"
        if content:
            context += f"\n内容摘要：{content[:500]}"

        prompt = f"""你是金融公告分类专家。请对以下公告进行分类。

{context}

按以下JSON格式输出：
```json
{{
  "event_type": "production/financial/personnel/safety/ma/esg/operation/dividend/regulation/other",
  "event_subtype": "具体子类型",
  "impact_level": "positive/negative/neutral",
  "sentiment": "positive/negative/neutral",
  "related_mine": "涉及矿山名称或null",
  "related_product": "涉及产品（金/铜/锌）或null",
  "summary": "一句话摘要",
  "key_metrics": {{"关键指标": "数值"}}
}}
```
只输出JSON，不要解释。"""

        result = _call_deepseek(prompt, max_tokens=512)
        if result:
            parsed = _extract_json(result)
            if parsed and 'event_type' in parsed:
                parsed['confidence'] = 'llm'
                return parsed

        return quick  # fallback到关键词分类

    def _quick_classify(self, title: str) -> dict:
        """关键词快速分类"""
        rules = [
            (r'产量|采矿|选矿|冶炼|精矿|矿产|投产|达产|扩产|增产', 'production', '产量变动'),
            (r'利润|营收|财务|业绩|盈利|亏损|分红|派息|股利', 'financial', '财务事件'),
            (r'董事|监事|高管|辞职|任命|变更|换届', 'personnel', '人事变动'),
            (r'安全|事故|伤亡|环保|排放|污染|整改|安监', 'safety', '安全环保'),
            (r'收购|并购|重组|合并|转让|出售|剥离', 'ma', '并购重组'),
            (r'ESG|可持续|碳中和|绿色|社会责任|社区', 'esg', 'ESG'),
            (r'经营|生产|运营|检修|停产|复产|开工', 'operation', '运营动态'),
            (r'分红|派息|权益分派', 'dividend', '分红派息'),
            (r'监管|处罚|违规|立案|调查|合规', 'regulation', '监管合规'),
        ]

        for pattern, event_type, subtype in rules:
            if re.search(pattern, title):
                # 判断影响方向
                if re.search(r'增长|增加|超预期|突破|创新高|大增|暴增', title):
                    impact = 'positive'
                elif re.search(r'下降|减少|下滑|亏损|事故|处罚|违规', title):
                    impact = 'negative'
                else:
                    impact = 'neutral'

                return {
                    'event_type': event_type,
                    'event_subtype': subtype,
                    'impact_level': impact,
                    'sentiment': impact,
                    'related_mine': None,
                    'related_product': None,
                    'summary': title,
                    'key_metrics': {},
                    'confidence': 'high',
                }

        return {
            'event_type': 'other',
            'event_subtype': '未分类',
            'impact_level': 'neutral',
            'sentiment': 'neutral',
            'related_mine': None,
            'related_product': None,
            'summary': title,
            'key_metrics': {},
            'confidence': 'low',
        }

    async def classify_and_store(self, stock_code: str, title: str,
                                  content: str = "", source_url: str = "",
                                  publish_date: str = None) -> dict:
        """分类并存储事件"""
        from core.db import get_database
        db = get_database()

        # 检查是否已存在（用标题+日期去重）
        if source_url:
            existing = await db.fetchone(
                "SELECT id FROM events WHERE stock_code = ? AND title = ? AND publish_date = ?",
                (stock_code, title, publish_date)
            )
            if existing:
                return {"status": "duplicate", "id": existing[0]}

        # 分类
        classification = await asyncio.to_thread(
            self.classify_event, title, content
        )

        # 存储
        try:
            await db.execute("""
                INSERT OR IGNORE INTO events
                (stock_code, event_type, event_subtype, title, summary, source_url,
                 publish_date, impact_level, sentiment, related_mine, related_product,
                 key_metrics, llm_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stock_code,
                classification.get('event_type', 'other'),
                classification.get('event_subtype'),
                title,
                classification.get('summary', title),
                source_url,
                publish_date,
                classification.get('impact_level', 'neutral'),
                classification.get('sentiment', 'neutral'),
                classification.get('related_mine'),
                classification.get('related_product'),
                json.dumps(classification.get('key_metrics', {}), ensure_ascii=False),
                json.dumps(classification, ensure_ascii=False),
            ))
            await db.commit()

            event_id = await db.fetchone(
                "SELECT id FROM events WHERE stock_code = ? AND source_url = ?",
                (stock_code, source_url)
            )

            return {
                "status": "created",
                "id": event_id[0] if event_id else None,
                "classification": classification,
            }
        except Exception as e:
            logger.warning("event.store_event_failed error=%s", e)
            return {"status": "error", "message": str(e)}

    async def get_events(self, stock_code: str = "601899",
                          event_type: str = None, days: int = 30,
                          limit: int = 50) -> List[dict]:
        """获取事件列表"""
        from core.db import get_database
        db = get_database()

        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        if event_type:
            rows = await db.fetchall("""
                SELECT * FROM events
                WHERE stock_code = ? AND event_type = ? AND publish_date >= ?
                ORDER BY publish_date DESC LIMIT ?
            """, (stock_code, event_type, cutoff, limit))
        else:
            rows = await db.fetchall("""
                SELECT * FROM events
                WHERE stock_code = ? AND publish_date >= ?
                ORDER BY publish_date DESC LIMIT ?
            """, (stock_code, cutoff, limit))

        return [dict(row) for row in rows] if rows else []

    async def get_event_stats(self, stock_code: str = "601899", days: int = 90) -> dict:
        """获取事件统计"""
        from core.db import get_database
        db = get_database()

        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        rows = await db.fetchall("""
            SELECT event_type, COUNT(*) as cnt,
                   SUM(CASE WHEN impact_level = 'positive' THEN 1 ELSE 0 END) as positive_cnt,
                   SUM(CASE WHEN impact_level = 'negative' THEN 1 ELSE 0 END) as negative_cnt
            FROM events
            WHERE stock_code = ? AND publish_date >= ?
            GROUP BY event_type
            ORDER BY cnt DESC
        """, (stock_code, cutoff))

        stats = {}
        for row in (rows or []):
            r = dict(row) if not isinstance(row, dict) else row
            stats[r['event_type']] = {
                'count': r['cnt'],
                'positive': r['positive_cnt'],
                'negative': r['negative_cnt'],
            }

        return stats

    async def batch_classify_announcements(self, stock_code: str = "601899") -> dict:
        """批量分类已有公告"""
        from core.db import get_database
        db = get_database()

        # 获取未分类的公告
        rows = await db.fetchall("""
            SELECT a.title, a.url, a.publish_date, a.summary
            FROM announcement a
            WHERE a.stock_code = ?
            AND NOT EXISTS (
                SELECT 1 FROM events e
                WHERE e.stock_code = a.stock_code
                AND e.title = a.title
                AND e.publish_date = a.publish_date
            )
            ORDER BY a.publish_date DESC
            LIMIT 20
        """, (stock_code,))

        if not rows:
            return {"processed": 0, "message": "没有未分类的公告"}

        results = []
        for row in rows:
            r = dict(row) if not isinstance(row, dict) else row
            title = r.get('title', '')
            url = r.get('url', '')
            pub_date = r.get('publish_date', '')
            summary = r.get('summary', '')
            result = await self.classify_and_store(
                stock_code=stock_code,
                title=title,
                content=summary or "",
                source_url=url,
                publish_date=pub_date,
            )
            results.append(result)

        return {
            "processed": len(results),
            "created": sum(1 for r in results if r.get('status') == 'created'),
            "duplicates": sum(1 for r in results if r.get('status') == 'duplicate'),
        }


import asyncio

# 单例
event_service = EventService()
