import { useQuery } from '@tanstack/react-query';
import { stockAPI } from '../services/api';
import type { StockQuote } from '../types';

interface StockOverview {
  a_share: StockQuote | null;
  hk_share: StockQuote | null;
}

export function useStockOverview() {
  return useQuery({
    queryKey: ['stock', 'overview'],
    queryFn: async () => {
      const res = await stockAPI.getOverview();
      if (res.data?.success) return res.data.data as StockOverview;
      return null;
    },
  });
}

export function useStockHistory(code: string = '601899', market: string = 'A', days: number = 30) {
  return useQuery({
    queryKey: ['stock', 'history', code, market, days],
    queryFn: async () => {
      const res = await stockAPI.getHistory(code, market, days);
      if (res.data?.success) return res.data.data ?? [];
      return [];
    },
  });
}
