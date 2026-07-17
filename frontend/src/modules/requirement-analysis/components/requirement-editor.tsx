/** Requirement text editor component.

Provides a text area for pasting requirements with source type
selection (plain text, Markdown, acceptance criteria).
*/

import { useEffect, useState } from "react";
import { AlertCircle, FileText, Braces, ListChecks, BookOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { InputSourceType } from "@/modules/requirement-analysis/types";
import { REQUIREMENT_PRESETS } from "@/modules/requirement-analysis/data/presets";

interface RequirementEditorProps {
  onSubmit: (content: string, sourceType: InputSourceType) => void;
  isSubmitting?: boolean;
  error?: string | null;
}

const SOURCE_OPTIONS: {
  value: InputSourceType;
  label: string;
  icon: React.ReactNode;
  description: string;
}[] = [
  {
    value: "plain_text",
    label: "Plain Text",
    icon: <FileText className="h-4 w-4" />,
    description: "Free-form requirements description",
  },
  {
    value: "markdown",
    label: "Markdown",
    icon: <Braces className="h-4 w-4" />,
    description: "Formatted with Markdown headings and lists",
  },
  {
    value: "acceptance_criteria",
    label: "Acceptance Criteria",
    icon: <ListChecks className="h-4 w-4" />,
    description: "Given/When/Then style scenarios",
  },
];

export function RequirementEditor({
  onSubmit,
  isSubmitting = false,
  error = null,
}: RequirementEditorProps) {
  const [content, setContent] = useState("");
  const [sourceType, setSourceType] = useState<InputSourceType>("plain_text");
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (isSubmitting) {
      setElapsed(0);
      const interval = setInterval(() => setElapsed((s) => s + 1), 1000);
      return () => clearInterval(interval);
    }
  }, [isSubmitting]);

  const handleSubmit = () => {
    if (!content.trim()) return;
    onSubmit(content.trim(), sourceType);
  };

  const canSubmit = content.trim().length > 0 && !isSubmitting;

  return (
    <div className="space-y-4">
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
            title={option.description}
          >
            {option.icon}
            <span className="font-medium">{option.label}</span>
          </button>
        ))}
      </div>

      {/* Preset selector */}
      <div>
        <p className="mb-2 text-xs font-medium text-muted-foreground">
          Try a real-world requirement
        </p>
        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
          {REQUIREMENT_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => {
                setContent(preset.content);
                setSourceType(preset.sourceType);
              }}
              className={cn(
                "flex items-center gap-2 rounded-lg border px-2.5 py-2 text-left text-xs transition-colors",
                content === preset.content
                  ? "border-primary/50 bg-primary/5"
                  : "border-border/60 hover:border-muted-foreground/30 hover:bg-muted/30",
              )}
              title={preset.description}
            >
              <BookOpen className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              <span className="truncate font-medium">{preset.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Text area */}
      <div className="relative">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={(e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
              e.preventDefault();
              handleSubmit();
            }
          }}
          placeholder={`Paste your requirements here...\n\nExample:\nThe system shall allow users to log in with email and password.\nUsers must be able to reset their password via email.\n...`}
          className="min-h-[200px] w-full resize-y rounded-lg border bg-background p-4 font-mono text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-ring"
          disabled={isSubmitting}
          rows={10}
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

      {/* Submit button */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          Requirements are analyzed by AI. Results are stored for future review.
        </p>
        <Button onClick={handleSubmit} disabled={!canSubmit}>
          {isSubmitting ? `Analyzing... (${elapsed}s)` : "Analyze Requirements"}
        </Button>
      </div>
    </div>
  );
}
