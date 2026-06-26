import { useQuery } from '@tanstack/react-query';
import { commodityAPI } from '../services/api';
import type { CommodityOverview, GoldVolatility } from '../types';

export function useCommodityOverview() {
  return useQuery({
    queryKey: ['commodity', 'overview'],
    queryFn: async () => {
      const res = await commodityAPI.getOverview();
      if (res.data?.success) return res.data.data as CommodityOverview;
      return null;
    },
  });
}

export function useGoldVolatility() {
  return useQuery({
    queryKey: ['commodity', 'gold-volatility'],
    queryFn: async () => {
      const res = await commodityAPI.getGoldVolatility();
      if (res.data?.success) return res.data.data as GoldVolatility;
      return null;
    },
    refetchInterval: 60000, // 波动率 60s 刷新一次
  });
}

export function useCommodityHistory(type: string, days: number = 30) {
  return useQuery({
    queryKey: ['commodity', 'history', type, days],
    queryFn: async () => {
      const res = await commodityAPI.getHistory(type, days);
      if (res.data?.success) return res.data.data ?? [];
      return [];
    },
    staleTime: 60000, // 历史数据 60s 内不重新请求
  });
}
