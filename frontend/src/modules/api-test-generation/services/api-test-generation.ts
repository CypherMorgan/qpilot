/** Typed API service functions for the API Test Generation module. */

import { apiClient } from "@/services/api-client";
import type { ApiSuccessResponse } from "@/types/api";
import type {
  ApiTestRequest,
  ApiTestResult,
  ApiTestSessionListItem,
} from "@/modules/api-test-generation/types";

/**
 * Submit an OpenAPI spec for AI-powered test generation.
 */
export async function generateApiTests(
  request: ApiTestRequest,
): Promise<ApiTestResult> {
  const response = await apiClient.post<
    ApiSuccessResponse<ApiTestResult>
  >("/openapi/analyze", request);
  return response.data.data;
}

/**
 * Retrieve a completed generation session by ID.
 */
export async function getApiTestSession(
  sessionId: string,
): Promise<ApiTestResult> {
  const response = await apiClient.get<
    ApiSuccessResponse<ApiTestResult>
  >(`/openapi/sessions/${sessionId}`);
  return response.data.data;
}

/**
 * List past API test generation sessions with pagination.
 */
export async function listApiTestSessions(
  page: number = 1,
  pageSize: number = 20,
): Promise<{ items: ApiTestSessionListItem[]; total: number }> {
  const response = await apiClient.get<{
    data: ApiTestSessionListItem[];
    meta: { pagination: { total: number; page: number; page_size: number; has_more: boolean } };
  }>("/openapi/sessions", {
    params: { page, page_size: pageSize },
  });
  return {
    items: response.data.data,
    total: response.data.meta.pagination.total,
  };
}

/**
 * Delete an API test generation session by ID.
 */
export async function deleteApiTestSession(
  sessionId: string,
): Promise<void> {
  await apiClient.delete(`/openapi/sessions/${sessionId}`);
}
