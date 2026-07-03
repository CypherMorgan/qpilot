/** Tests for Requirement Analysis service functions.

Uses mock API client to verify correct request/response handling.
*/

import { describe, it, expect, vi, beforeEach } from "vitest";

import { apiClient } from "@/services/api-client";

// Mock the apiClient
vi.mock("@/services/api-client", () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

import {
  analyzeRequirements,
  getAnalysisSession,
  listAnalysisSessions,
} from "@/modules/requirement-analysis/services/requirement-analysis";

describe("analyzeRequirements", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should POST to /requirements/analyze with request body", async () => {
    const mockResponse = {
      data: {
        data: {
          session_id: "abc-123",
          status: "completed",
          result: {
            input_summary: "Test",
            functional_tests: [],
            negative_tests: [],
            boundary_tests: [],
            edge_cases: [],
            assumptions: [],
            risks: [],
            missing_requirements: [],
            suggested_questions: [],
            automation_candidates: [],
            priority_assessment: {
              overall_priority: "medium",
              critical_path_items: [],
              quick_wins: [],
              reasoning: "Test",
            },
          },
          provider: "mock",
          model: "mock-model",
          total_tokens: 100,
          latency_ms: 50,
        },
      },
    };

    vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

    const result = await analyzeRequirements({
      content: "Test requirements.",
    });

    expect(apiClient.post).toHaveBeenCalledWith("/requirements/analyze", {
      content: "Test requirements.",
    });
    expect(result.session_id).toBe("abc-123");
    expect(result.status).toBe("completed");
  });
});

describe("getAnalysisSession", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should GET /requirements/sessions/{id}", async () => {
    const mockResponse = {
      data: {
        data: {
          session_id: "abc-123",
          status: "completed",
          result: {
            input_summary: "Test",
            functional_tests: [],
            negative_tests: [],
            boundary_tests: [],
            edge_cases: [],
            assumptions: [],
            risks: [],
            missing_requirements: [],
            suggested_questions: [],
            automation_candidates: [],
            priority_assessment: {
              overall_priority: "medium",
              critical_path_items: [],
              quick_wins: [],
              reasoning: "Test",
            },
          },
          provider: "mock",
          model: "mock-model",
          total_tokens: 100,
          latency_ms: 50,
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

    const result = await getAnalysisSession("abc-123");
    expect(apiClient.get).toHaveBeenCalledWith(
      "/requirements/sessions/abc-123",
    );
    expect(result.session_id).toBe("abc-123");
  });
});

describe("listAnalysisSessions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should GET /requirements/sessions with pagination params", async () => {
    const mockResponse = {
      data: {
        data: [],
        meta: {
          pagination: {
            total: 0,
            page: 1,
            page_size: 20,
            has_more: false,
          },
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

    const result = await listAnalysisSessions(1, 10);
    expect(apiClient.get).toHaveBeenCalledWith("/requirements/sessions", {
      params: { page: 1, page_size: 10 },
    });
    expect(result.items).toEqual([]);
    expect(result.total).toBe(0);
  });
});
