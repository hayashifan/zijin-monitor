"""
巨潮公告爬虫 - 复用BaseCrawler模式
"""
import requests
from datetime import datetime
from typing import List, Dict, Any

from crawlers.base import BaseCrawler


class CninfoCrawler(BaseCrawler):
    """巨潮资讯网公告爬虫"""
    
    def __init__(self):
        super().__init__(
            name="cninfo",
            failure_threshold=3,
            reset_timeout=600,  # 10分钟
            retries=2,
            retry_delay=2.0,
        )
        self.base_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    
    async def do_fetch(self) -> List[Dict[str, Any]]:
        """获取紫金矿业公告"""
        try:
            # 紫金矿业的股票代码
            stock_code = "601899"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            data = {
                'stock': stock_code,
                'tabName': 'fulltext',
                'pageNum': 1,
                'pageSize': 20,
                'column': 'sse',  # 上海证券交易所
                'category': '',
                'plate': '',
                'seDate': ''
            }
            
            response = requests.post(self.base_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            items = []
            for item in result.get('announcements', []):
                # 构造公告数据
                announcement = {
                    'id': str(item.get('announcementId', '')),
                    'title': item.get('announcementTitle', ''),
                    'url': f"http://www.cninfo.com.cn/new/disclosure/detail?stockCode={stock_code}&announcementId={item.get('announcementId')}",
                    'published_at': datetime.fromtimestamp(
                        item.get('announcementTime', 0) / 1000
                    ).isoformat() if item.get('announcementTime') else datetime.now().isoformat(),
                    'source': '巨潮资讯网',
                    'category': item.get('announcementType', ''),
                    'stock_code': stock_code,
                }
                items.append(announcement)
            
            print(f"[{self.name}] Fetched {len(items)} announcements")
            return items
            
        except Exception as e:
            print(f"[{self.name}] Failed to fetch announcements: {e}")
            raise


class SinaHkCrawler(BaseCrawler):
    """新浪H股行情爬虫"""
    
    def __init__(self):
        super().__init__(
            name="sina_hk",
            failure_threshold=3,
            reset_timeout=300,
            retries=2,
            retry_delay=1.0,
        )
    
    async def do_fetch(self) -> List[Dict[str, Any]]:
        """获取H股行情"""
        try:
            stock_code = "02899"
            url = f"https://hq.sinajs.cn/list=hk{stock_code}"
            
            headers = {
                'Referer': 'https://finance.sina.com.cn',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            content = response.text
            if '="' not in content:
                return []
            
            data_str = content.split('="')[1].rstrip('";')
            data_parts = data_str.split(',')
            
            if len(data_parts) < 15:
                return []
            
            item = {
                'code': stock_code,
                'market': 'HK',
                'name': data_parts[1],
                'price': float(data_parts[6]) if data_parts[6] else 0,
                'change': float(data_parts[7]) if data_parts[7] else 0,
                'change_percent': float(data_parts[8]) if data_parts[8] else 0,
                'open': float(data_parts[2]) if data_parts[2] else 0,
                'high': float(data_parts[4]) if data_parts[4] else 0,
                'low': float(data_parts[5]) if data_parts[5] else 0,
                'pre_close': float(data_parts[3]) if data_parts[3] else 0,
                'volume': int(float(data_parts[12])) if data_parts[12] else 0,
                'amount': float(data_parts[11]) if data_parts[11] else 0,
                'update_time': datetime.now().isoformat(),
            }
            
            return [item]
            
        except Exception as e:
            print(f"[{self.name}] Failed to fetch HK quote: {e}")
            raise
