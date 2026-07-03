/** TypeScript types for the Requirement Analysis module.

These mirror the backend Pydantic models in
``app/modules/requirement_analysis/models.py``.
*/

// ── Enums ─────────────────────────────────────────────────────────

export type PriorityLevel = "critical" | "high" | "medium" | "low";

export type RiskSeverity = "critical" | "high" | "medium" | "low";

export type AutomationFeasibility =
  | "easy"
  | "moderate"
  | "difficult"
  | "not_feasible";

export type InputSourceType = "plain_text" | "markdown" | "acceptance_criteria";

export type AnalysisStatus = "pending" | "processing" | "completed" | "failed";

// ── Input ─────────────────────────────────────────────────────────

export interface AnalysisRequest {
  content: string;
  source_type?: InputSourceType;
  title?: string;
  context?: string;
  output_format?: "json" | "markdown" | "both";
}

// ── Shared models ─────────────────────────────────────────────────

export interface TestCase {
  id: string;
  title: string;
  description: string;
  preconditions: string[];
  steps: string[];
  expected_result: string;
  priority: PriorityLevel;
  tags: string[];
}

export interface FunctionalTestCase extends TestCase {
  // Same as TestCase
}

export interface NegativeTestCase extends TestCase {
  // Same as TestCase
}

export interface BoundaryTestCase extends TestCase {
  boundary_value: string;
}

export interface EdgeCase {
  id: string;
  title: string;
  description: string;
  impact: string;
  recommendation: string | null;
}

export interface Risk {
  id: string;
  description: string;
  severity: RiskSeverity;
  likelihood: string;
  mitigation: string | null;
}

export interface AutomationCandidate {
  id: string;
  test_case_id: string;
  feasibility: AutomationFeasibility;
  effort_estimate: string;
  value_reason: string;
}

export interface PriorityAssessment {
  overall_priority: PriorityLevel;
  critical_path_items: string[];
  quick_wins: string[];
  reasoning: string;
}

export interface MissingRequirement {
  id: string;
  topic: string;
  description: string;
  importance: PriorityLevel;
}

// ── Root output model ─────────────────────────────────────────────

export interface RequirementAnalysisResult {
  input_summary: string;
  analysis_timestamp: string;
  functional_tests: FunctionalTestCase[];
  negative_tests: NegativeTestCase[];
  boundary_tests: BoundaryTestCase[];
  edge_cases: EdgeCase[];
  assumptions: string[];
  risks: Risk[];
  missing_requirements: MissingRequirement[];
  suggested_questions: string[];
  automation_candidates: AutomationCandidate[];
  priority_assessment: PriorityAssessment;
}

// ── API response ──────────────────────────────────────────────────

export interface AnalysisResponse {
  session_id: string;
  status: AnalysisStatus;
  result: RequirementAnalysisResult;
  provider: string | null;
  model: string | null;
  total_tokens: number;
  latency_ms: number;
}

export interface AnalysisSessionListItem {
  session_id: string;
  title: string | null;
  source_type: string | null;
  status: string;
  provider: string | null;
  total_tokens: number;
  created_at: string;
  updated_at: string;
  input_summary: string | null;
}
