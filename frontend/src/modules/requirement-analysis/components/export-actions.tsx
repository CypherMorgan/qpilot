/** Export actions for copying or downloading analysis results. */

import { useState } from "react";
import { Copy, Download, Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { RequirementAnalysisResult } from "@/modules/requirement-analysis/types";

interface ExportActionsProps {
  result: RequirementAnalysisResult;
}

/**
 * Copy the analysis result to clipboard in the specified format.
 */
async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

/**
 * Format result as Markdown (approximate — client-side rendering).
 */
function formatAsMarkdown(result: RequirementAnalysisResult): string {
  const lines: string[] = [];
  lines.push("# Requirement Analysis Report");
  lines.push("");
  lines.push(`**Input summary:** ${result.input_summary}`);
  lines.push("");
  lines.push("---");
  lines.push("");

  // Each section
  lines.push("## Functional Test Cases");
  for (const tc of result.functional_tests) {
    lines.push(`### ${tc.id}: ${tc.title}`);
    lines.push(`- **Priority:** ${tc.priority}`);
    lines.push(`- ${tc.description}`);
    lines.push("");
  }

  lines.push("## Negative Test Cases");
  for (const tc of result.negative_tests) {
    lines.push(`### ${tc.id}: ${tc.title}`);
    lines.push(`- **Priority:** ${tc.priority}`);
    lines.push(`- ${tc.description}`);
    lines.push("");
  }

  lines.push("## Risks");
  for (const r of result.risks) {
    lines.push(`- **${r.id}:** ${r.description} (Severity: ${r.severity}, Likelihood: ${r.likelihood})`);
  }

  return lines.join("\n");
}

export function ExportActions({ result }: ExportActionsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (format: "json" | "markdown") => {
    const text =
      format === "json"
        ? JSON.stringify(result, null, 2)
        : formatAsMarkdown(result);
    const success = await copyToClipboard(text);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = (format: "json" | "markdown") => {
    const text =
      format === "json"
        ? JSON.stringify(result, null, 2)
        : formatAsMarkdown(result);
    const blob = new Blob([text], {
      type: format === "json" ? "application/json" : "text/markdown",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `requirement-analysis.${format === "json" ? "json" : "md"}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          {copied ? (
            <>
              <Check className="mr-2 h-4 w-4" />
              Copied
            </>
          ) : (
            <>
              <Download className="mr-2 h-4 w-4" />
              Export
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleCopy("json")}>
          <Copy className="mr-2 h-4 w-4" />
          Copy as JSON
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleCopy("markdown")}>
          <Copy className="mr-2 h-4 w-4" />
          Copy as Markdown
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleDownload("json")}>
          <Download className="mr-2 h-4 w-4" />
          Download JSON
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleDownload("markdown")}>
          <Download className="mr-2 h-4 w-4" />
          Download Markdown
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
