/** Typed API service functions for the Requirement Analysis module. */

import { apiClient } from "@/services/api-client";
import type { ApiSuccessResponse } from "@/types/api";
import type {
  AnalysisRequest,
  AnalysisResponse,
  AnalysisSessionListItem,
} from "@/modules/requirement-analysis/types";

/**
 * Submit requirements text for AI-powered analysis.
 */
export async function analyzeRequirements(
  request: AnalysisRequest,
): Promise<AnalysisResponse> {
  const response = await apiClient.post<
    ApiSuccessResponse<AnalysisResponse>
  >("/requirements/analyze", request);
  return response.data.data;
}

/**
 * Retrieve a completed analysis session by ID.
 */
export async function getAnalysisSession(
  sessionId: string,
): Promise<AnalysisResponse> {
  const response = await apiClient.get<
    ApiSuccessResponse<AnalysisResponse>
  >(`/requirements/sessions/${sessionId}`);
  return response.data.data;
}

/**
 * List past requirement analysis sessions with pagination.
 */
export async function listAnalysisSessions(
  page: number = 1,
  pageSize: number = 20,
): Promise<{ items: AnalysisSessionListItem[]; total: number }> {
  const response = await apiClient.get<{
    data: AnalysisSessionListItem[];
    meta: { pagination: { total: number; page: number; page_size: number; has_more: boolean } };
  }>("/requirements/sessions", {
    params: { page, page_size: pageSize },
  });
  return {
    items: response.data.data,
    total: response.data.meta.pagination.total,
  };
}

/**
 * Delete a requirement analysis session by ID.
 */
export async function deleteRequirementSession(
  sessionId: string,
): Promise<void> {
  await apiClient.delete(`/requirements/sessions/${sessionId}`);
}
