import { useQuery } from '@tanstack/react-query';
import { announcementAPI } from '../services/api';
import type { Announcement } from '../types';

export function useAnnouncements(code: string = '601899') {
  return useQuery({
    queryKey: ['announcements', code],
    queryFn: async () => {
      const res = await announcementAPI.getList(code, 'cninfo', 1, 10);
      if (res.data?.success) return (Array.isArray(res.data.data) ? res.data.data : []) as Announcement[];
      return [];
    },
  });
}
