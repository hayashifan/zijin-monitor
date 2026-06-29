import { useQuery } from '@tanstack/react-query';
import { fundamentalScoreAPI } from '../services/api';

interface ScoreDetail {
  name: string;
  value: string;
  score: number;
  max: number;
  status: string;
}

interface ScoreDimension {
  score: number;
  max: number;
  details: ScoreDetail[];
}

export interface FundamentalScoreData {
  total: number;
  max: number;
  grade: string;
  dimensions: {
    earning: ScoreDimension;
    safety: ScoreDimension;
    moat: ScoreDimension;
    sector: ScoreDimension;
  };
  summary: string;
}

export function useFundamentalScore(code: string = '601899') {
  return useQuery({
    queryKey: ['fundamental-score', code],
    queryFn: async () => {
      const res = await fundamentalScoreAPI.getScore(code);
      if (res.data?.success) return res.data.data as FundamentalScoreData;
      return null;
    },
    staleTime: 300000, // 5 分钟
  });
}
