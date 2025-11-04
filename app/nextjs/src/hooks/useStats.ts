import { useQuery } from '@tanstack/react-query';
import { AdminApiService } from '../services/api/adminApi';

export const useStats = () => {
  return useQuery({
    queryKey: ['stats'],
    queryFn: AdminApiService.getIndexStats,
    staleTime: 30000, // 30 seconds
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};
