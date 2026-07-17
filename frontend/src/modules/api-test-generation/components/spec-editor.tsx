/** OpenAPI spec editor component.

Provides a text area for pasting OpenAPI specs with format
selection (YAML or JSON) and optional configuration fields.
*/

import { useEffect, useState } from "react";
import { AlertCircle, FileCode, FileJson, BookOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { API_TEST_PRESETS } from "@/modules/api-test-generation/data/presets";

interface SpecEditorProps {
  onSubmit: (spec: string, specFormat: "yaml" | "json") => void;
  isSubmitting?: boolean;
  error?: string | null;
}

const FORMAT_OPTIONS: {
  value: "yaml" | "json";
  label: string;
  icon: React.ReactNode;
}[] = [
  {
    value: "yaml",
    label: "YAML",
    icon: <FileCode className="h-4 w-4" />,
  },
  {
    value: "json",
    label: "JSON",
    icon: <FileJson className="h-4 w-4" />,
  },
];

export function SpecEditor({
  onSubmit,
  isSubmitting = false,
  error = null,
}: SpecEditorProps) {
  const [spec, setSpec] = useState("");
  const [specFormat, setSpecFormat] = useState<"yaml" | "json">("yaml");
  const [title, setTitle] = useState("");
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (isSubmitting) {
      setElapsed(0);
      const interval = setInterval(() => setElapsed((s) => s + 1), 1000);
      return () => clearInterval(interval);
    }
  }, [isSubmitting]);

  const handleSubmit = () => {
    if (!spec.trim()) return;
    onSubmit(spec.trim(), specFormat);
  };

  const canSubmit = spec.trim().length > 0 && !isSubmitting;

  return (
    <div className="space-y-4">
      {/* Title (optional) */}
      <div>
        <label
          htmlFor="spec-title"
          className="mb-1.5 block text-sm font-medium text-muted-foreground"
        >
          Title <span className="text-muted-foreground/50">(optional)</span>
        </label>
        <input
          id="spec-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g., Pet Store API Tests"
          className="w-full rounded-lg border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-ring"
          disabled={isSubmitting}
        />
      </div>

      {/* Format selector */}
      <div className="flex flex-wrap gap-2">
        {FORMAT_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setSpecFormat(option.value)}
            className={cn(
              "flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors",
              specFormat === option.value
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
          Try a real-world API spec
        </p>
        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
          {API_TEST_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => {
                setSpec(preset.content);
                setSpecFormat(preset.specFormat);
                setTitle(preset.title);
              }}
              className={cn(
                "flex items-center gap-2 rounded-lg border px-2.5 py-2 text-left text-xs transition-colors",
                spec === preset.content
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

      {/* Spec text area */}
      <div className="relative">
        <textarea
          value={spec}
          onChange={(e) => setSpec(e.target.value)}
          onKeyDown={(e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
              e.preventDefault();
              handleSubmit();
            }
          }}
          placeholder={`Paste your OpenAPI spec here...\n\nopenapi: "3.0.0"\ninfo:\n  title: Pet Store\n  version: "1.0.0"\npaths:\n  /pets:\n    get:\n      summary: List all pets\n      ...`}
          className="min-h-[300px] w-full resize-y rounded-lg border bg-background p-4 font-mono text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-ring"
          disabled={isSubmitting}
          rows={15}
        />
        <div className="absolute bottom-3 right-3 text-xs text-muted-foreground">
          {spec.length.toLocaleString()} chars
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
          The OpenAPI spec is parsed and analyzed by AI. Generated test files
          can be downloaded as a ZIP archive.
        </p>
        <Button onClick={handleSubmit} disabled={!canSubmit}>
          {isSubmitting ? `Generating... (${elapsed}s)` : "Generate Tests"}
        </Button>
      </div>
    </div>
  );
}
