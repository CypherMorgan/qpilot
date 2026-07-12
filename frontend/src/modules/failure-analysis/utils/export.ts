/** Client-side export utilities for Failure Analysis results.

Provides formatting (Markdown, JSON), clipboard copy, and file
download functions — no backend round-trip needed.
*/

import type { FailureAnalysisResult } from "@/modules/failure-analysis/types";

// ── Markdown formatting ──────────────────────────────────────────

export function formatAsMarkdown(result: FailureAnalysisResult): string {
  const lines: string[] = [];

  lines.push("# Automation Failure Analysis Report");
  lines.push("");
  lines.push(`**Input summary:** ${result.input_summary}`);
  lines.push(`**Analysis timestamp:** ${result.analysis_timestamp}`);
  lines.push("");
  lines.push("---");
  lines.push("");

  // Summary
  lines.push("## Summary");
  lines.push("");
  lines.push(result.summary);
  lines.push("");

  // Root Causes
  lines.push("## Root Causes");
  lines.push("");
  if (result.root_causes.length === 0) {
    lines.push("_No root causes identified._");
    lines.push("");
  }
  for (const rc of result.root_causes) {
    lines.push(`### ${rc.id}: ${rc.title}`);
    lines.push("");
    lines.push(rc.description);
    lines.push("");
    lines.push(`- **Category:** \`${rc.category}\``);
    lines.push(`- **Severity:** \`${rc.severity}\``);
    if (rc.failing_file) {
      lines.push(`- **Failing file:** \`${rc.failing_file}${rc.failing_line ? `:${rc.failing_line}` : ""}\``);
    }
    if (rc.error_message) {
      lines.push("");
      lines.push("**Error message:**");
      lines.push("```");
      lines.push(rc.error_message);
      lines.push("```");
    }
    if (rc.stack_trace && rc.stack_trace.length > 0) {
      lines.push("");
      lines.push("**Stack trace:**");
      for (const frame of rc.stack_trace) {
        const loc = `${frame.file}:${frame.line}${frame.function ? ` in ${frame.function}` : ""}`;
        lines.push(`- \`${loc}\``);
        if (frame.code) {
          lines.push(`  \`${frame.code}\``);
        }
      }
    }
    lines.push("");
  }

  // Suggested Fixes
  lines.push("## Suggested Fixes");
  lines.push("");
  if (result.suggested_fixes.length === 0) {
    lines.push("_No suggested fixes identified._");
    lines.push("");
  }
  for (const fix of result.suggested_fixes) {
    lines.push(`### ${fix.id}: ${fix.description}`);
    lines.push("");
    lines.push(`- **Root cause:** ${fix.root_cause_id}`);
    lines.push(`- **Priority:** \`${fix.priority}\``);
    if (fix.effort_estimate) {
      lines.push(`- **Effort:** ${fix.effort_estimate}`);
    }
    if (fix.related_files && fix.related_files.length > 0) {
      lines.push("- **Files to modify:**");
      for (const f of fix.related_files) {
        lines.push(`  - \`${f}\``);
      }
    }
    if (fix.code_example) {
      lines.push("");
      lines.push("**Code fix:**");
      lines.push("```");
      lines.push(fix.code_example);
      lines.push("```");
    }
    lines.push("");
  }

  // Affected Components
  lines.push("## Affected Components");
  lines.push("");
  if (result.affected_components.length === 0) {
    lines.push("_No affected components identified._");
    lines.push("");
  } else {
    lines.push("| ID | Component | Impact | Related Root Causes |");
    lines.push("|----|-----------|--------|---------------------|");
    for (const cmp of result.affected_components) {
      const related = cmp.related_root_causes?.length ? cmp.related_root_causes.join(", ") : "-";
      lines.push(`| ${cmp.id} | ${cmp.name} | ${cmp.impact} | ${related} |`);
    }
    lines.push("");
  }

  // Test Failures
  lines.push("## Test Failures");
  lines.push("");
  if (result.test_failures.length === 0) {
    lines.push("_No individual test failures listed._");
    lines.push("");
  }
  for (const tf of result.test_failures) {
    lines.push(`### ${tf.id}: ${tf.test_name}`);
    lines.push("");
    if (tf.test_file) {
      lines.push(`- **File:** \`${tf.test_file}\``);
    }
    if (tf.duration_seconds != null) {
      lines.push(`- **Duration:** ${tf.duration_seconds}s`);
    }
    if (tf.retry_count && tf.retry_count > 0) {
      lines.push(`- **Retries:** ${tf.retry_count}`);
    }
    if (tf.error_message) {
      lines.push("");
      lines.push("**Error:**");
      lines.push("```");
      lines.push(tf.error_message);
      lines.push("```");
    }
    lines.push("");
  }

  // Environment Details
  lines.push("## Environment Details");
  lines.push("");
  if (result.environment_details.length === 0) {
    lines.push("_No environment details recorded._");
    lines.push("");
  }
  for (let i = 0; i < result.environment_details.length; i++) {
    lines.push(`${i + 1}. ${result.environment_details[i]}`);
  }
  lines.push("");

  // Recommendations
  lines.push("## Recommendations");
  lines.push("");
  if (result.recommendations.length === 0) {
    lines.push("_No recommendations provided._");
    lines.push("");
  }
  for (let i = 0; i < result.recommendations.length; i++) {
    lines.push(`${i + 1}. ${result.recommendations[i]}`);
  }
  lines.push("");

  // Related Tests
  lines.push("## Related Tests");
  lines.push("");
  if (result.related_tests.length === 0) {
    lines.push("_No related tests identified._");
    lines.push("");
  }
  for (let i = 0; i < result.related_tests.length; i++) {
    lines.push(`${i + 1}. ${result.related_tests[i]}`);
  }
  lines.push("");

  return lines.join("\n");
}

// ── JSON formatting ──────────────────────────────────────────────

export function formatAsJson(result: FailureAnalysisResult): string {
  return JSON.stringify(result, null, 2);
}

// ── Download ──────────────────────────────────────────────────────

export function downloadAsFile(
  content: string,
  filename: string,
  mimeType: string = "text/markdown",
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

// ── Clipboard ─────────────────────────────────────────────────────

export async function copyToClipboard(text: string): Promise<void> {
  await navigator.clipboard.writeText(text);
}
