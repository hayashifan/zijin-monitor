/**
 * 券商研报 Hooks
 */
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const api = axios.create({ timeout: 10000 });

interface AnalystOpinion {
  id: number;
  broker: string;
  analyst: string;
  rating: string;
  target_price: number | null;
  report_title: string;
  report_date: string;
}

/** 获取研报列表 */
export function useAnalystReports(stockCode: string = '601899', days: number = 90) {
  return useQuery<AnalystOpinion[]>({
    queryKey: ['analystReports', stockCode, days],
    queryFn: async () => {
      const { data } = await api.get('/api/analyst/list', { params: { stock_code: stockCode, days } });
      return data.data;
    },
    staleTime: 300000, // 5分钟
  });
}
