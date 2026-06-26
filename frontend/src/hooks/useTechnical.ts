import { useQuery } from '@tanstack/react-query';
import { technicalAPI } from '../services/api';
import type { TechnicalIndicators } from '../types';

export function useTechnicalIndicators(code: string = '601899', market: string = 'A', days: number = 120) {
  return useQuery({
    queryKey: ['technical', code, market, days],
    queryFn: async () => {
      const res = await technicalAPI.getIndicators(code, market, days);
      if (res.data?.success) return res.data.data as TechnicalIndicators;
      return null;
    },
    staleTime: 60000,
  });
}
