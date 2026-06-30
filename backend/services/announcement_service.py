"""
公告爬虫服务 - 东方财富 + 缓存
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import time

from core.http import get_session
from core.cache import CacheManager


class AnnouncementService:
    """公告爬虫服务"""

    def __init__(self):
        self.session = get_session()
        self._cache = CacheManager(max_size=50, default_ttl=600)

    def _get_cached(self, key: str) -> Optional[list]:
        return self._cache.get(key)

    def _set_cache(self, key: str, data: list):
        self._cache.set(key, data)

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

        except Exception as e:
            print(f"[announcement] Error fetching eastmoney announcements: {e}")
            return []

    async def get_cninfo_announcements(self, stock_code: str, page: int = 1, size: int = 20) -> List[Dict]:
        """从巨潮资讯网获取公告（通过东方财富）"""
        return await self.get_eastmoney_announcements(stock_code, page, size)

    async def get_hkex_announcements(self, stock_code: str) -> List[Dict]:
        """从港交所获取H股公告（简化实现）"""
        return []

    async def get_announcement_detail(self, art_code: str) -> Optional[Dict]:
        """获取公告详情（正文+PDF链接）"""
        cache_key = f'ann_detail_{art_code}'
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            url = "https://np-cnotice-stock.eastmoney.com/api/content/ann"
            params = {
                'art_code': art_code,
                'client_source': 'web',
                'f_node': '0',
                's_node': '0',
            }
            headers = {
                'Accept': 'application/json',
                'Referer': 'https://data.eastmoney.com/',
            }

            response = await asyncio.to_thread(self.session.get, url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            result = response.json()

            if not result.get('success'):
                return None

            data = result.get('data', {})
            if not data:
                return None

            detail = {
                'id': art_code,
                'title': data.get('notice_title', ''),
                'content': data.get('notice_content', ''),
                'publish_date': (data.get('notice_date', '') or '')[:10],
                'pdf_url': data.get('attach_url_web') or data.get('attach_url', ''),
                'page_count': data.get('page_size', 0),
                'source': '东方财富',
            }

            self._set_cache(cache_key, detail)
            return detail

        except Exception as e:
            print(f"[announcement] Failed to get detail for {art_code}: {e}")
            return None


announcement_service = AnnouncementService()
