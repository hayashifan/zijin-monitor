import { useQuery } from '@tanstack/react-query';
import { quantAPI } from '../services/api';
import type { QuantReport } from '../types';

export function useQuantReport() {
  return useQuery({
    queryKey: ['quant', 'latest'],
    queryFn: async () => {
      const res = await quantAPI.getLatest();
      if (res.data?.success) return res.data.data as QuantReport;
      return null;
    },
    refetchInterval: 60000, // 量化报告 60s 刷新
  });
}
