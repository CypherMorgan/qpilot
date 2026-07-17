/** Failure input editor component.

Provides a text area for pasting CI/CD logs, stack traces, or error
output with source type selection and optional configuration fields.

Now a controlled component — state lives in the parent so the submit
button can be placed at the bottom of the page (below file upload).
*/

import { Bug, FileText, Hammer, Package, Terminal, Timer, Wifi } from "lucide-react";

import { cn } from "@/lib/utils";
import type { InputSourceType } from "@/modules/failure-analysis/types";
import { FAILURE_PRESETS } from "@/modules/failure-analysis/data/presets";

interface FailureInputProps {
  content: string;
  onContentChange: (content: string) => void;
  sourceType: InputSourceType;
  onSourceTypeChange: (sourceType: InputSourceType) => void;
  title: string;
  onTitleChange: (title: string) => void;
  onSubmit?: () => void;
  disabled?: boolean;
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

const PRESET_ICONS: Record<string, React.ReactNode> = {
  assertion_error: <Bug className="h-4 w-4" />,
  timeout: <Timer className="h-4 w-4" />,
  dependency: <Package className="h-4 w-4" />,
  environment: <Terminal className="h-4 w-4" />,
  configuration: <Wifi className="h-4 w-4" />,
  compilation: <Hammer className="h-4 w-4" />,
};

export function FailureInput({
  content,
  onContentChange,
  sourceType,
  onSourceTypeChange,
  title,
  onTitleChange,
  disabled = false,
  onSubmit,
}: FailureInputProps) {
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
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder="e.g., CI Pipeline Failure — 2026-07-10"
          className="w-full rounded-lg border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-ring"
          disabled={disabled}
        />
      </div>

      {/* Source type selector */}
      <div className="flex flex-wrap gap-2">
        {SOURCE_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onSourceTypeChange(option.value)}
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

      {/* Preset selector */}
      <div>
        <p className="mb-2 text-xs font-medium text-muted-foreground">
          Try an example failure
        </p>
        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-4">
          {FAILURE_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => {
                onContentChange(preset.content);
                onSourceTypeChange(preset.sourceType);
                onTitleChange(preset.title);
              }}
              className={cn(
                "flex items-center gap-2 rounded-lg border px-2.5 py-2 text-left text-xs transition-colors",
                content === preset.content
                  ? "border-primary/50 bg-primary/5"
                  : "border-border/60 hover:border-muted-foreground/30 hover:bg-muted/30",
              )}
            >
              <span className="shrink-0 text-muted-foreground">
                {PRESET_ICONS[preset.category] ?? <Bug className="h-3.5 w-3.5" />}
              </span>
              <span className="truncate font-medium">{preset.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Failure content text area */}
      <div className="relative">
        <textarea
          value={content}
          onChange={(e) => onContentChange(e.target.value)}
          onKeyDown={(e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
              e.preventDefault();
              onSubmit?.();
            }
          }}
          placeholder={`Paste CI/CD logs, stack traces, or error output here...\n\nFAILED tests/integration/test_auth.py::test_login_success\nAssertionError: assert False\n  +  where False = <built-in method startswith of str object at 0x...>('eyJ')`}
          className="min-h-[300px] w-full resize-y rounded-lg border bg-background p-4 font-mono text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-ring"
          disabled={disabled}
          rows={15}
        />
        <div className="absolute bottom-3 right-3 text-xs text-muted-foreground">
          {content.length.toLocaleString()} chars
        </div>
      </div>
    </div>
  );
}
