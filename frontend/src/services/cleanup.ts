/** Cleanup API service — session retention / expired session cleanup. */

import { apiClient } from "@/services/api-client";

interface CleanupResponse {
  deleted: number;
  retention_days: number;
}

/**
 * Delete all analysis sessions older than the configured retention period.
 *
 * Returns the number of deleted sessions and the current retention setting.
 */
export async function deleteExpiredSessions(): Promise<CleanupResponse> {
  const response = await apiClient.delete<{
    data: CleanupResponse;
  }>("/cleanup/expired");
  return response.data.data;
}
