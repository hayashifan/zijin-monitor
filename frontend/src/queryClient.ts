import { QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchInterval: (query) => {
        // 后台标签页暂停轮询
        if (typeof document !== 'undefined' && document.hidden) {
          return false;
        }
        return 15000;
      },
      retry: 2,
      staleTime: 10000,
    },
  },
});

export default queryClient;
