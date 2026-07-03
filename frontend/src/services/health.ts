import { apiClient } from "@/services/api-client";
import type { ApiSuccessResponse, HealthResponse } from "@/types/api";

/**
 * Fetch backend health status.
 */
export async function getHealthStatus(): Promise<HealthResponse> {
  const response = await apiClient.get<
    ApiSuccessResponse<HealthResponse>
  >("/health");
  return response.data.data;
}
