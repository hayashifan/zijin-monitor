"""
公告爬虫服务 - 东方财富 + 缓存
"""
import requests
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import time


class AnnouncementService:
    """公告爬虫服务"""

    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 600  # 10分钟缓存

    def _get_cached(self, key: str) -> Optional[list]:
        if key in self._cache:
            data, ts = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return data
        return None

    def _set_cache(self, key: str, data: list):
        self._cache[key] = (data, time.time())
        if len(self._cache) > 50:
            now = time.time()
            expired = [k for k, (_, ts) in self._cache.items() if now - ts > self._cache_ttl * 2]
            for k in expired:
                del self._cache[k]

    async def get_eastmoney_announcements(self, stock_code: str, page: int = 1, size: int = 20) -> List[Dict]:
        """从东方财富获取公告"""
        cache_key = f'eastmoney_ann_{stock_code}_{page}_{size}'

        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
            params = {
                'sr': '-1',
                'page_size': str(size),
                'page_index': str(page),
                'ann_type': 'A',
                'client_source': 'web',
                'stock_list': stock_code,
                'f_node': '0',
                's_node': '0',
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Referer': f'https://data.eastmoney.com/notices/detail/{stock_code}.html',
            }

            response = await asyncio.to_thread(self.session.get, url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            result = response.json()

            announcements = []
            for item in result.get('data', {}).get('list', []):
                try:
                    notice_date = item.get('notice_date', '')
                    pub_date = notice_date[:10] if notice_date else ''

                    ann_id = item.get('art_code', '')
                    if ann_id:
                        item_url = f"https://data.eastmoney.com/notices/detail/{stock_code}/{ann_id}.html"
                    else:
                        item_url = f"https://data.eastmoney.com/notices/detail/{stock_code}.html"

                    columns = item.get('columns', [])
                    category = columns[0].get('column_name', '') if columns else ''

                    announcements.append({
                        'id': str(ann_id) or str(item.get('art_code', '')),
                        'title': item.get('title', ''),
                        'publish_date': pub_date,
                        'url': item_url,
                        'source': '东方财富',
                        'category': category or '公告',
                    })
                except Exception as e:
                    print(f"[announcement] Parse item error: {e}")
                    continue

            if announcements:
                self._set_cache(cache_key, announcements)

            return announcements

        except requests.exceptions.RequestException as e:
            print(f"[announcement] Network error: {e}")
            return []
        except Exception as e:
            print(f"[announcement] Error fetching eastmoney announcements: {e}")
            return []

    async def get_cninfo_announcements(self, stock_code: str, page: int = 1, size: int = 20) -> List[Dict]:
        """从巨潮资讯网获取公告（通过东方财富）"""
        return await self.get_eastmoney_announcements(stock_code, page, size)

    async def get_hkex_announcements(self, stock_code: str) -> List[Dict]:
        """从港交所获取H股公告（简化实现）"""
        return []


announcement_service = AnnouncementService()
