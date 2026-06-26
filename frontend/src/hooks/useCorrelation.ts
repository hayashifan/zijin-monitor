import { useQuery } from '@tanstack/react-query';
import { correlationAPI } from '../services/api';
import type { CommodityCorrelationMap, QuantCorrelationData } from '../types';

export function useCommodityCorrelation(types: string = 'gold,copper_lme,copper_shfe', days: number = 60) {
  return useQuery({
    queryKey: ['correlation', 'commodity', types, days],
    queryFn: async () => {
      const res = await correlationAPI.getCommodity(types, days);
      if (res.data?.success) return res.data.data as CommodityCorrelationMap;
      return null;
    },
    staleTime: 120000, // 关联性分析 2 分钟内不重新请求
  });
}

export function useQuantCorrelation(days: number = 90) {
  return useQuery({
    queryKey: ['correlation', 'quant', days],
    queryFn: async () => {
      const res = await correlationAPI.getQuant(days);
      if (res.data?.success) return res.data.data as QuantCorrelationData;
      return null;
    },
    staleTime: 120000,
  });
}
