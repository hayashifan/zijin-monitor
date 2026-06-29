import { useQuery } from '@tanstack/react-query';
import { commodityAPI } from '../services/api';
import type { CommodityPrice, CommodityOverview, GoldVolatility } from '../types';

export function useCommodityOverview() {
  return useQuery({
    queryKey: ['commodity', 'overview'],
    queryFn: async () => {
      const res = await commodityAPI.getOverview();
      if (res.data?.success) return res.data.data as CommodityOverview;
      throw new Error(res.data?.message || 'Failed to fetch commodity overview');
    },
    staleTime: 15000,
  });
}

export function useCommodityHistory(type: string, days: number = 30) {
  return useQuery({
    queryKey: ['commodity', 'history', type, days],
    queryFn: async () => {
      const res = await commodityAPI.getHistory(type, days);
      if (res.data?.success) return res.data.data;
      throw new Error(res.data?.message || 'Failed to fetch commodity history');
    },
    staleTime: 60000,
  });
}

export function useGoldVolatility() {
  return useQuery({
    queryKey: ['commodity', 'gold-volatility'],
    queryFn: async () => {
      const res = await commodityAPI.getGoldVolatility();
      if (res.data?.success) return res.data.data as GoldVolatility;
      throw new Error(res.data?.message || 'Failed to fetch gold volatility');
    },
    staleTime: 60000,
  });
}
