/** TanStack Query hooks for the API Test Generation module. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { ApiTestRequest } from "@/modules/api-test-generation/types";
import {
  generateApiTests,
  getApiTestSession,
  listApiTestSessions,
  deleteApiTestSession,
} from "@/modules/api-test-generation/services/api-test-generation";

const API_TEST_KEYS = {
  all: ["api-test-generation"] as const,
  sessions: (page: number) =>
    [...API_TEST_KEYS.all, "sessions", page] as const,
  session: (id: string) => [...API_TEST_KEYS.all, "session", id] as const,
};

/**
 * Submit an OpenAPI spec for test generation.
 * On success, invalidates the sessions list cache.
 */
export function useGenerateApiTests() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ApiTestRequest) => generateApiTests(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: API_TEST_KEYS.sessions(1) });
    },
  });
}

/**
 * Fetch a single generation session by ID.
 */
export function useApiTestSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: API_TEST_KEYS.session(sessionId ?? ""),
    queryFn: () => getApiTestSession(sessionId!),
    enabled: !!sessionId,
    retry: 1,
  });
}

/**
 * Fetch paginated list of generation sessions.
 */
export function useApiTestSessions(page: number = 1) {
  return useQuery({
    queryKey: API_TEST_KEYS.sessions(page),
    queryFn: () => listApiTestSessions(page),
    staleTime: 30_000,
  });
}

/**
 * Delete an API test generation session.
 * Invalidates both the session list and the specific session cache.
 */
export function useDeleteApiTestSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => deleteApiTestSession(sessionId),
    onSuccess: (_data, sessionId) => {
      queryClient.invalidateQueries({ queryKey: API_TEST_KEYS.sessions(1) });
      queryClient.removeQueries({ queryKey: API_TEST_KEYS.session(sessionId) });
    },
  });
}
