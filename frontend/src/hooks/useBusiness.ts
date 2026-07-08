/**
 * 业务动向 Hooks (v2.5)
 */
import { useQuery } from '@tanstack/react-query';
import { businessAPI } from '../services/api';
import type { MineInfo, ProductionPlan, SegmentFinance, ESGData, PriceSensitivity } from '../types';

/** 获取矿山列表 */
export function useMines() {
  return useQuery<MineInfo[]>({
    queryKey: ['mines'],
    queryFn: async () => {
      const { data } = await businessAPI.getMines();
      return data.data;
    },
    staleTime: 86400 * 1000,
  });
}

/** 获取产量计划 */
export function useProduction(year?: number) {
  return useQuery<ProductionPlan[]>({
    queryKey: ['production', year],
    queryFn: async () => {
      const { data } = await businessAPI.getProduction(year);
      return data.data;
    },
    staleTime: 3600 * 1000,
  });
}

/** 获取板块财务 */
export function useSegmentFinance(reportDate?: string) {
  return useQuery<SegmentFinance[]>({
    queryKey: ['segmentFinance', reportDate],
    queryFn: async () => {
      const { data } = await businessAPI.getFinance(reportDate);
      return data.data;
    },
    staleTime: 3600 * 1000,
  });
}

/** 获取ESG数据 */
export function useESG(year?: number) {
  return useQuery<ESGData[]>({
    queryKey: ['esg', year],
    queryFn: async () => {
      const { data } = await businessAPI.getESG(year);
      return data.data;
    },
    staleTime: 86400 * 1000,
  });
}

/** 获取价格敏感性 */
export function usePriceSensitivity(year?: number) {
  return useQuery<PriceSensitivity[]>({
    queryKey: ['priceSensitivity', year],
    queryFn: async () => {
      const { data } = await businessAPI.getSensitivity(year);
      return data.data;
    },
    staleTime: 86400 * 1000,
  });
}
