/** Section card component for displaying analysis result sections.

Wraps each analysis section in a consistent card with a title,
icon, and content area. Used by all analysis modules.
*/

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SectionCardProps {
  /** Section title displayed in the header */
  title: string;
  /** Optional icon element */
  icon?: ReactNode;
  /** Card content */
  children: ReactNode;
  /** Optional count badge (e.g., "5 items") */
  count?: number;
  /** Empty state message when children is null/empty */
  emptyMessage?: string;
  /** Additional CSS classes */
  className?: string;
  /** Visual variant for the section */
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

const VARIANT_STYLES: Record<string, string> = {
  default: "border-border",
  success: "border-emerald-500/30 bg-emerald-500/5",
  warning: "border-amber-500/30 bg-amber-500/5",
  danger: "border-red-500/30 bg-red-500/5",
  info: "border-blue-500/30 bg-blue-500/5",
};

const VARIANT_HEADER: Record<string, string> = {
  default: "text-muted-foreground",
  success: "text-emerald-600 dark:text-emerald-400",
  warning: "text-amber-600 dark:text-amber-400",
  danger: "text-red-600 dark:text-red-400",
  info: "text-blue-600 dark:text-blue-400",
};

export function SectionCard({
  title,
  icon,
  children,
  count,
  emptyMessage,
  className,
  variant = "default",
}: SectionCardProps) {
  const hasContent = count !== undefined ? count > 0 : true;

  return (
    <div
      className={cn(
        "rounded-lg border bg-card",
        VARIANT_STYLES[variant],
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className={cn("flex items-center gap-2 text-sm font-semibold", VARIANT_HEADER[variant])}>
          {icon && <span className="shrink-0">{icon}</span>}
          <span>{title}</span>
          {count !== undefined && (
            <span className="ml-1 rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
              {count}
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-3">
        {hasContent ? (
          children
        ) : (
          <p className="py-4 text-center text-sm italic text-muted-foreground">
            {emptyMessage || "No items in this section."}
          </p>
        )}
      </div>
    </div>
  );
}
