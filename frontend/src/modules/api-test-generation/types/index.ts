/** TypeScript types for the API Test Generation module.

These mirror the backend Pydantic models in
``app/modules/api_test_generation/models.py``.
*/

// ── Input ─────────────────────────────────────────────────────────

export interface ApiTestRequest {
  spec: string;
  spec_format?: "yaml" | "json";
  title?: string;
  paths?: string[];
  context?: string;
}

// ── Domain models ─────────────────────────────────────────────────

export interface GeneratedFile {
  filename: string;
  path: string;
  size: number;
}

export interface EndpointGenInfo {
  path: string;
  method: string;
  tests_generated: number;
}

// ── Root response ─────────────────────────────────────────────────

export type AnalysisStatus = "processing" | "completed" | "failed";

export interface ApiTestResult {
  session_id: string;
  status: AnalysisStatus;
  spec_title: string;
  spec_version: string;
  endpoint_count: number;
  files: GeneratedFile[];
  endpoints: EndpointGenInfo[];
  download_url: string;
  provider: string | null;
  model: string | null;
  total_tokens: number;
  latency_ms: number;
}

// ── List item ─────────────────────────────────────────────────────

export interface ApiTestSessionListItem {
  session_id: string;
  title: string | null;
  status: string;
  provider: string | null;
  total_tokens: number;
  created_at: string;
  updated_at: string;
  spec_title: string | null;
  endpoint_count: number | null;
}
