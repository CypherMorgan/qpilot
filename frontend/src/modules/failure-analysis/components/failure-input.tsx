/** Failure input editor component.

Provides a text area for pasting CI/CD logs, stack traces, or error
output with source type selection and optional configuration fields.
*/

import { useState } from "react";
import { AlertCircle, Bug, FileText, Terminal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { InputSourceType } from "@/modules/failure-analysis/types";

interface FailureInputProps {
  onSubmit: (content: string, sourceType: InputSourceType) => void;
  isSubmitting?: boolean;
  error?: string | null;
}

const SOURCE_OPTIONS: {
  value: InputSourceType;
  label: string;
  icon: React.ReactNode;
}[] = [
  {
    value: "plain_text",
    label: "Plain Text",
    icon: <FileText className="h-4 w-4" />,
  },
  {
    value: "ci_log",
    label: "CI Log",
    icon: <Terminal className="h-4 w-4" />,
  },
  {
    value: "stack_trace",
    label: "Stack Trace",
    icon: <Bug className="h-4 w-4" />,
  },
];

export function FailureInput({
  onSubmit,
  isSubmitting = false,
  error = null,
}: FailureInputProps) {
  const [content, setContent] = useState("");
  const [sourceType, setSourceType] = useState<InputSourceType>("plain_text");
  const [title, setTitle] = useState("");

  const handleSubmit = () => {
    if (!content.trim()) return;
    onSubmit(content.trim(), sourceType);
  };

  const canSubmit = content.trim().length > 0 && !isSubmitting;

  return (
    <div className="space-y-4">
      {/* Title (optional) */}
      <div>
        <label
          htmlFor="failure-title"
          className="mb-1.5 block text-sm font-medium text-muted-foreground"
        >
          Title <span className="text-muted-foreground/50">(optional)</span>
        </label>
        <input
          id="failure-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g., CI Pipeline Failure — 2026-07-10"
          className="w-full rounded-lg border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-ring"
          disabled={isSubmitting}
        />
      </div>

      {/* Source type selector */}
      <div className="flex flex-wrap gap-2">
        {SOURCE_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setSourceType(option.value)}
            className={cn(
              "flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors",
              sourceType === option.value
                ? "border-primary bg-primary/5 text-primary"
                : "border-border hover:border-muted-foreground/30",
            )}
          >
            {option.icon}
            <span className="font-medium">{option.label}</span>
          </button>
        ))}
      </div>

      {/* Failure content text area */}
      <div className="relative">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={`Paste CI/CD logs, stack traces, or error output here...\n\nFAILED tests/integration/test_auth.py::test_login_success\nAssertionError: assert False\n  +  where False = <built-in method startswith of str object at 0x...>('eyJ')`}
          className="min-h-[300px] w-full resize-y rounded-lg border bg-background p-4 font-mono text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-ring"
          disabled={isSubmitting}
          rows={15}
        />
        <div className="absolute bottom-3 right-3 text-xs text-muted-foreground">
          {content.length.toLocaleString()} chars
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/5 p-3 text-sm text-destructive">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Submit */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          The failure output is analyzed by AI to identify root causes,
          suggest fixes, and assess impact.
        </p>
        <Button onClick={handleSubmit} disabled={!canSubmit}>
          {isSubmitting ? "Analyzing..." : "Analyze Failure"}
        </Button>
      </div>
    </div>
  );
}
