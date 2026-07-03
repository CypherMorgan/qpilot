/** Generation results display.

Renders the complete generation result with file listing, endpoint
summary, and metadata in a structured layout.
*/

import { FileCode, Route } from "lucide-react";

import { SectionCard } from "@/components/section-card";
import { ExportActions } from "@/modules/api-test-generation/components/export-actions";
import type { ApiTestResult, GeneratedFile, EndpointGenInfo } from "@/modules/api-test-generation/types";

interface GenerationResultsProps {
  result: ApiTestResult;
}

function FileList({ files }: { files: GeneratedFile[] }) {
  return (
    <div className="divide-y">
      {files.map((file) => (
        <div
          key={file.path}
          className="flex items-center justify-between py-2 text-sm"
        >
          <div className="flex items-center gap-2">
            <FileCode className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="font-mono">{file.filename}</span>
          </div>
          <span className="text-xs text-muted-foreground">
            {(file.size / 1024).toFixed(1)} KB
          </span>
        </div>
      ))}
    </div>
  );
}

function EndpointList({ endpoints }: { endpoints: EndpointGenInfo[] }) {
  return (
    <div className="divide-y">
      {endpoints.map((ep) => (
        <div
          key={`${ep.method}-${ep.path}`}
          className="flex items-center justify-between py-2 text-sm"
        >
          <div className="flex items-center gap-2">
            <span
              className={`
                inline-flex items-center rounded px-1.5 py-0.5 text-xs font-semibold uppercase
                ${ep.method === "get" ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300" : ""}
                ${ep.method === "post" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300" : ""}
                ${ep.method === "put" ? "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300" : ""}
                ${ep.method === "patch" ? "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300" : ""}
                ${ep.method === "delete" ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300" : ""}
              `}
            >
              {ep.method}
            </span>
            <span className="font-mono text-muted-foreground">{ep.path}</span>
          </div>
          <span className="text-xs text-muted-foreground">
            {ep.tests_generated} test{ep.tests_generated !== 1 ? "s" : ""}
          </span>
        </div>
      ))}
    </div>
  );
}

export function GenerationResults({ result }: GenerationResultsProps) {
  return (
    <div className="space-y-6">
      {/* Summary bar */}
      <div className="rounded-lg border bg-card p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-lg font-semibold">Generation Complete</p>
            <p className="text-sm text-muted-foreground">
              {result.spec_title}
              {result.spec_version && ` v${result.spec_version}`}
            </p>
          </div>
          <ExportActions downloadUrl={result.download_url} />
        </div>
        <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground">
          {result.provider && (
            <span>
              Provider: <span className="font-medium">{result.provider}</span>
            </span>
          )}
          {result.model && (
            <span>
              Model: <span className="font-medium">{result.model}</span>
            </span>
          )}
          {result.total_tokens > 0 && (
            <span>
              Tokens:{" "}
              <span className="font-medium">
                {result.total_tokens.toLocaleString()}
              </span>
            </span>
          )}
          {result.latency_ms > 0 && (
            <span>
              Latency:{" "}
              <span className="font-medium">{result.latency_ms}ms</span>
            </span>
          )}
        </div>
      </div>

      {/* Section cards */}
      <div className="grid gap-6">
        {/* Generated Files */}
        <SectionCard
          title="Generated Files"
          icon={<FileCode className="h-4 w-4" />}
          count={result.files.length}
          variant="success"
          emptyMessage="No files were generated."
        >
          <FileList files={result.files} />
        </SectionCard>

        {/* Endpoints Covered */}
        <SectionCard
          title="Endpoints"
          icon={<Route className="h-4 w-4" />}
          count={result.endpoints.length}
          variant="info"
          emptyMessage="No endpoints in the spec."
        >
          <EndpointList endpoints={result.endpoints} />
        </SectionCard>
      </div>
    </div>
  );
}
