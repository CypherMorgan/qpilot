import { useQuery } from "@tanstack/react-query";

import { getHealthStatus } from "@/services/health";

const HEALTH_QUERY_KEY = ["health"] as const;

/**
 * TanStack Query hook for backend health check.
 * Polls every 30s for connection monitoring.
 */
export function useHealth() {
  return useQuery({
    queryKey: HEALTH_QUERY_KEY,
    queryFn: getHealthStatus,
    refetchInterval: 30_000,
    staleTime: 10_000,
    retry: 2,
  });
}
