import { QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchInterval: 15000,
      retry: 2,
      staleTime: 10000,
    },
  },
});

export default queryClient;
