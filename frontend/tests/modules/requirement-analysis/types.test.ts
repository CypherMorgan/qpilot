/** Tests for Requirement Analysis TypeScript types and model validation. */

import { describe, it, expect } from "vitest";
import type {
  AnalysisRequest,
  FunctionalTestCase,
  RequirementAnalysisResult,
  Risk,
  PriorityAssessment,
} from "@/modules/requirement-analysis/types";

describe("AnalysisRequest type", () => {
  it("should accept a valid request object", () => {
    const request: AnalysisRequest = {
      content: "The system shall allow users to log in.",
    };
    expect(request.content).toBeTruthy();
    expect(request.source_type).toBeUndefined();
  });

  it("should accept optional fields", () => {
    const request: AnalysisRequest = {
      content: "Test",
      source_type: "markdown",
      title: "Login",
      output_format: "both",
    };
    expect(request.source_type).toBe("markdown");
    expect(request.title).toBe("Login");
  });
});

describe("RequirementAnalysisResult type", () => {
  const sampleResult: RequirementAnalysisResult = {
    input_summary: "Test requirements.",
    analysis_timestamp: "2026-07-01T12:00:00Z",
    functional_tests: [
      {
        id: "TC-FUNC-001",
        title: "Successful login",
        description: "Verify login works",
        preconditions: ["User exists"],
        steps: ["Enter email", "Enter password", "Click login"],
        expected_result: "User is logged in",
        priority: "high",
        tags: ["login"],
      },
    ],
    negative_tests: [],
    boundary_tests: [],
    edge_cases: [],
    assumptions: ["Passwords are hashed."],
    risks: [
      {
        id: "RSK-001",
        description: "Brute force attack",
        severity: "high",
        likelihood: "medium",
        mitigation: "Rate limit",
      },
    ],
    missing_requirements: [],
    suggested_questions: ["What is the token expiry?"],
    automation_candidates: [],
    priority_assessment: {
      overall_priority: "high",
      critical_path_items: ["TC-FUNC-001"],
      quick_wins: [],
      reasoning: "Core flow.",
    },
  };

  it("should have a valid structure", () => {
    expect(sampleResult.input_summary).toBe("Test requirements.");
    expect(sampleResult.functional_tests).toHaveLength(1);
    expect(sampleResult.risks).toHaveLength(1);
    expect(sampleResult.priority_assessment.overall_priority).toBe("high");
  });

  it("should handle empty arrays", () => {
    expect(sampleResult.negative_tests).toEqual([]);
    expect(sampleResult.boundary_tests).toEqual([]);
  });

  it("should serialize to JSON correctly", () => {
    const json = JSON.stringify(sampleResult);
    const parsed = JSON.parse(json);
    expect(parsed.input_summary).toBe("Test requirements.");
    expect(parsed.functional_tests[0].id).toBe("TC-FUNC-001");
  });
});

describe("FunctionalTestCase type", () => {
  it("should enforce required fields", () => {
    const tc: FunctionalTestCase = {
      id: "TC-FUNC-001",
      title: "Test",
      description: "Desc",
      preconditions: [],
      steps: ["Step 1"],
      expected_result: "Result",
      priority: "medium",
      tags: [],
    };
    expect(tc.steps).toHaveLength(1);
    expect(tc.priority).toBe("medium");
  });
});
