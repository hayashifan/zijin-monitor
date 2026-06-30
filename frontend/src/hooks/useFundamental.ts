import { useQuery } from '@tanstack/react-query';
import { fundamentalAPI } from '../services/api';
import type { FinancialOverview } from '../types';

export function useFundamentalOverview(code: string = '601899') {
  return useQuery({
    queryKey: ['fundamental', 'overview', code],
    queryFn: async () => {
      const res = await fundamentalAPI.getOverview(code);
      if (res.data?.success) return res.data.data as FinancialOverview;
      return null;
    },
    staleTime: 60000, // 基本面数据 60s 内不重新请求
  });
}
