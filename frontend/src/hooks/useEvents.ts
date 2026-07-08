/**
 * 事件系统 Hooks
 */
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const api = axios.create({ timeout: 10000 });

interface Event {
  id: number;
  event_type: string;
  event_subtype: string;
  title: string;
  summary: string;
  impact_level: string;
  publish_date: string;
  related_mine: string | null;
  related_product: string | null;
}

/** 获取事件列表 */
export function useEvents(stockCode: string = '601899', days: number = 30) {
  return useQuery<Event[]>({
    queryKey: ['events', stockCode, days],
    queryFn: async () => {
      const { data } = await api.get('/api/events/list', { params: { stock_code: stockCode, days } });
      return data.data;
    },
    staleTime: 60000,
  });
}
