/** Failure Analysis Module — barrel exports. */

export type {
  AnalysisRequest,
  AnalysisResponse,
  AnalysisSessionListItem,
  FailureAnalysisResult,
  FailureCategory,
  FailureSeverity,
  FixPriority,
  InputSourceType,
  RootCause,
  StackFrame,
  SuggestedFix,
  AffectedComponent,
  TestFailure,
} from "./types";

export { FailureInput } from "./components/failure-input";
export { AnalysisSummary } from "./components/analysis-summary";
export { FailureAnalysisPage } from "./pages/analysis-page";
export { FailureSessionDetailPage } from "./pages/session-detail-page";
export {
  useAnalyzeFailure,
  useFailureSession,
  useFailureSessions,
} from "./hooks/use-failure-analysis";
export {
  analyzeFailure,
  getFailureSession,
  listFailureSessions,
} from "./services/failure-analysis";
