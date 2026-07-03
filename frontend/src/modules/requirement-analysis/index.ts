/** Requirement Analysis module public API.

Export all public components, hooks, services, and types.
*/

// Types
export type * from "@/modules/requirement-analysis/types";

// Components
export { RequirementEditor } from "@/modules/requirement-analysis/components/requirement-editor";
export { AnalysisResults } from "@/modules/requirement-analysis/components/analysis-results";
export { SectionCard } from "@/components/section-card";
export { ExportActions } from "@/modules/requirement-analysis/components/export-actions";

// Content renderers
export {
  FunctionalTestCases,
  NegativeTestCases,
  BoundaryTestCases,
  EdgeCasesList,
  AssumptionsList,
  RisksList,
  MissingRequirementsList,
  QuestionsList,
  AutomationCandidatesTable,
  PriorityAssessmentBlock,
} from "@/modules/requirement-analysis/components/section-content";

// Pages
export { RequirementAnalysisPage } from "@/modules/requirement-analysis/pages/analysis-page";
export { SessionDetailPage } from "@/modules/requirement-analysis/pages/session-detail-page";

// Hooks
export {
  useAnalyzeRequirements,
  useAnalysisSession,
  useAnalysisSessions,
} from "@/modules/requirement-analysis/hooks/use-requirement-analysis";

// Services
export {
  analyzeRequirements,
  getAnalysisSession,
  listAnalysisSessions,
} from "@/modules/requirement-analysis/services/requirement-analysis";
