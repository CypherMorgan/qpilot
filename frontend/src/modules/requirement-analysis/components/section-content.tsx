/** Content renderers for each analysis section type.

Provides specialized rendering for test cases, risks, edge cases,
assumptions, and other structured data from the analysis result.
*/

import { cn } from "@/lib/utils";
import type {
  FunctionalTestCase,
  NegativeTestCase,
  BoundaryTestCase,
  EdgeCase,
  Risk,
  AutomationCandidate,
  PriorityAssessment,
  MissingRequirement,
} from "@/modules/requirement-analysis/types";

// ── Priority / Severity badges ────────────────────────────────────

const PRIORITY_COLORS: Record<string, string> = {
  critical:
    "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  high: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  medium:
    "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  low: "bg-slate-100 text-slate-600 dark:bg-slate-800/30 dark:text-slate-400",
};

function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span
      className={cn(
        "inline-block rounded-full px-2 py-0.5 text-xs font-medium",
        PRIORITY_COLORS[priority] ?? PRIORITY_COLORS.medium,
      )}
    >
      {priority}
    </span>
  );
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  high: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  medium: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  low: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
};

function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span
      className={cn(
        "inline-block rounded-full px-2 py-0.5 text-xs font-medium",
        SEVERITY_COLORS[severity] ?? SEVERITY_COLORS.medium,
      )}
    >
      {severity}
    </span>
  );
}

// ── Test case renderer (shared by functional, negative, boundary) ─

function TestCaseCard({
  testCase,
}: {
  testCase: FunctionalTestCase | NegativeTestCase | BoundaryTestCase;
}) {
  return (
    <div className="rounded-md border bg-card/50 p-3 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="font-mono text-xs text-muted-foreground">
            {testCase.id}
          </span>
          <h4 className="mt-0.5 font-medium">{testCase.title}</h4>
        </div>
        <PriorityBadge priority={testCase.priority} />
      </div>

      <p className="mt-2 text-muted-foreground">{testCase.description}</p>

      {"boundary_value" in testCase && testCase.boundary_value && (
        <p className="mt-2 text-xs text-muted-foreground">
          <strong>Boundary value:</strong>{" "}
          <code className="rounded bg-muted px-1 py-0.5">
            {testCase.boundary_value}
          </code>
        </p>
      )}

      {testCase.preconditions.length > 0 && (
        <div className="mt-2">
          <p className="text-xs font-medium text-muted-foreground">
            Preconditions:
          </p>
          <ul className="mt-1 list-inside list-disc text-xs text-muted-foreground">
            {testCase.preconditions.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-2">
        <p className="text-xs font-medium text-muted-foreground">Steps:</p>
        <ol className="mt-1 list-inside list-decimal text-xs text-muted-foreground">
          {testCase.steps.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ol>
      </div>

      <div className="mt-2 rounded-md bg-muted/50 p-2 text-xs">
        <strong>Expected:</strong> {testCase.expected_result}
      </div>

      {testCase.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {testCase.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Exported renderers ────────────────────────────────────────────

export function FunctionalTestCases({
  tests,
}: {
  tests: FunctionalTestCase[];
}) {
  return (
    <div className="space-y-3">
      {tests.map((tc) => (
        <TestCaseCard key={tc.id} testCase={tc} />
      ))}
    </div>
  );
}

export function NegativeTestCases({ tests }: { tests: NegativeTestCase[] }) {
  return (
    <div className="space-y-3">
      {tests.map((tc) => (
        <TestCaseCard key={tc.id} testCase={tc} />
      ))}
    </div>
  );
}

export function BoundaryTestCases({ tests }: { tests: BoundaryTestCase[] }) {
  return (
    <div className="space-y-3">
      {tests.map((tc) => (
        <TestCaseCard key={tc.id} testCase={tc} />
      ))}
    </div>
  );
}

export function EdgeCasesList({ cases }: { cases: EdgeCase[] }) {
  return (
    <div className="space-y-3">
      {cases.map((ec) => (
        <div key={ec.id} className="rounded-md border bg-card/50 p-3 text-sm">
          <span className="font-mono text-xs text-muted-foreground">
            {ec.id}
          </span>
          <h4 className="mt-0.5 font-medium">{ec.title}</h4>
          <p className="mt-1 text-muted-foreground">{ec.description}</p>
          <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted-foreground">
            <span>
              <strong>Impact:</strong> {ec.impact}
            </span>
            {ec.recommendation && (
              <span>
                <strong>Recommendation:</strong> {ec.recommendation}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export function AssumptionsList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-1 text-sm">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/50" />
          <span className="text-muted-foreground">{item}</span>
        </li>
      ))}
    </ul>
  );
}

export function RisksList({ risks }: { risks: Risk[] }) {
  return (
    <div className="space-y-3">
      {risks.map((risk) => (
        <div
          key={risk.id}
          className="rounded-md border bg-card/50 p-3 text-sm"
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <span className="font-mono text-xs text-muted-foreground">
                {risk.id}
              </span>
              <h4 className="mt-0.5 font-medium">{risk.description}</h4>
            </div>
            <SeverityBadge severity={risk.severity} />
          </div>
          <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted-foreground">
            <span>
              <strong>Likelihood:</strong> {risk.likelihood}
            </span>
            {risk.mitigation && (
              <span>
                <strong>Mitigation:</strong> {risk.mitigation}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export function MissingRequirementsList({
  items,
}: {
  items: MissingRequirement[];
}) {
  return (
    <div className="space-y-3">
      {items.map((mr) => (
        <div
          key={mr.id}
          className="rounded-md border border-amber-500/20 bg-amber-500/5 p-3 text-sm"
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <span className="font-mono text-xs text-muted-foreground">
                {mr.id}
              </span>
              <h4 className="mt-0.5 font-medium">{mr.topic}</h4>
            </div>
            <PriorityBadge priority={mr.importance} />
          </div>
          <p className="mt-1 text-muted-foreground">{mr.description}</p>
        </div>
      ))}
    </div>
  );
}

export function QuestionsList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-2 text-sm">
      {items.map((q, i) => (
        <li key={i} className="flex items-start gap-2 text-muted-foreground">
          <span className="mt-0.5 shrink-0 font-medium text-foreground">
            Q{i + 1}:
          </span>
          <span>{q}</span>
        </li>
      ))}
    </ul>
  );
}

export function AutomationCandidatesTable({
  candidates,
}: {
  candidates: AutomationCandidate[];
}) {
  if (candidates.length === 0) {
    return (
      <p className="py-4 text-center text-sm italic text-muted-foreground">
        No automation candidates identified.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-xs text-muted-foreground">
            <th className="pb-2 font-medium">ID</th>
            <th className="pb-2 font-medium">Test Case</th>
            <th className="pb-2 font-medium">Feasibility</th>
            <th className="pb-2 font-medium">Effort</th>
            <th className="pb-2 font-medium">Value</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((ac) => (
            <tr key={ac.id} className="border-b last:border-0">
              <td className="py-2 font-mono text-xs">{ac.id}</td>
              <td className="py-2">{ac.test_case_id}</td>
              <td className="py-2">
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-xs font-medium",
                    ac.feasibility === "easy" && "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
                    ac.feasibility === "moderate" && "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
                    ac.feasibility === "difficult" && "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
                    ac.feasibility === "not_feasible" && "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
                  )}
                >
                  {ac.feasibility}
                </span>
              </td>
              <td className="py-2 text-muted-foreground">
                {ac.effort_estimate}
              </td>
              <td className="py-2 text-muted-foreground">{ac.value_reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PriorityAssessmentBlock({
  assessment,
}: {
  assessment: PriorityAssessment;
}) {
  return (
    <div className="space-y-4 text-sm">
      <div className="flex items-center gap-2">
        <span className="text-muted-foreground">Overall priority:</span>
        <PriorityBadge priority={assessment.overall_priority} />
      </div>

      <div>
        <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Critical Path Items
        </p>
        {assessment.critical_path_items.length > 0 ? (
          <ul className="space-y-1">
            {assessment.critical_path_items.map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" />
                <span className="font-medium">{item}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs italic text-muted-foreground">None identified.</p>
        )}
      </div>

      <div>
        <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Quick Wins
        </p>
        {assessment.quick_wins.length > 0 ? (
          <ul className="space-y-1">
            {assessment.quick_wins.map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs italic text-muted-foreground">None identified.</p>
        )}
      </div>

      <div className="rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
        <strong className="text-foreground">Reasoning:</strong>{" "}
        {assessment.reasoning}
      </div>
    </div>
  );
}
