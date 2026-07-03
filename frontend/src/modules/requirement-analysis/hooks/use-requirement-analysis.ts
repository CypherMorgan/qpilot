/** TanStack Query hooks for the Requirement Analysis module. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { AnalysisRequest } from "@/modules/requirement-analysis/types";
import {
  analyzeRequirements,
  getAnalysisSession,
  listAnalysisSessions,
} from "@/modules/requirement-analysis/services/requirement-analysis";

const ANALYSIS_KEYS = {
  all: ["requirement-analysis"] as const,
  sessions: (page: number) =>
    [...ANALYSIS_KEYS.all, "sessions", page] as const,
  session: (id: string) => [...ANALYSIS_KEYS.all, "session", id] as const,
};

/**
 * Submit requirements for analysis.
 * On success, invalidates the sessions list cache.
 */
export function useAnalyzeRequirements() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: AnalysisRequest) => analyzeRequirements(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ANALYSIS_KEYS.sessions(1) });
    },
  });
}

/**
 * Fetch a single analysis session by ID.
 */
export function useAnalysisSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: ANALYSIS_KEYS.session(sessionId ?? ""),
    queryFn: () => getAnalysisSession(sessionId!),
    enabled: !!sessionId,
    retry: 1,
  });
}

/**
 * Fetch paginated list of analysis sessions.
 */
export function useAnalysisSessions(page: number = 1) {
  return useQuery({
    queryKey: ANALYSIS_KEYS.sessions(page),
    queryFn: () => listAnalysisSessions(page),
    staleTime: 30_000,
  });
}
