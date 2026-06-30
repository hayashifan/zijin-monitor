import { useQuery } from '@tanstack/react-query';
import { reportAPI } from '../services/api';
import type { AnnualReport, QuarterlyComparisonItem, ReportAlert } from '../types';

export function useReportList(code: string = '601899') {
  return useQuery({
    queryKey: ['report', 'list', code],
    queryFn: async () => {
      const res = await reportAPI.getList(code);
      if (res.data?.success) return res.data.data as AnnualReport[];
      return [];
    },
    staleTime: 300000, // 报告列表 5 分钟内不重新请求
  });
}

export function useReportDetail(code: string = '601899', date: string) {
  return useQuery({
    queryKey: ['report', 'detail', code, date],
    queryFn: async () => {
      const res = await reportAPI.getDetail(code, date);
      if (res.data?.success) return res.data.data as AnnualReport;
      return null;
    },
    enabled: !!date,
  });
}

export function useQuarterlyComparison(code: string = '601899', periods: number = 8) {
  return useQuery({
    queryKey: ['report', 'comparison', code, periods],
    queryFn: async () => {
      const res = await reportAPI.getComparison(code, periods);
      if (res.data?.success) return res.data.data as QuarterlyComparisonItem[];
      return [];
    },
    staleTime: 300000,
  });
}

export function useReportAlerts(code: string = '601899') {
  return useQuery({
    queryKey: ['report', 'alerts', code],
    queryFn: async () => {
      const res = await reportAPI.getAlerts(code);
      if (res.data?.success) return res.data.data as ReportAlert[];
      return [];
    },
    staleTime: 60000,
  });
}
