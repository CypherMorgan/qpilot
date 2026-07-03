import { cn } from "@/lib/utils";
import { Inbox } from "lucide-react";
import type { ReactNode } from "react";

interface EmptyStateProps {
  /** Icon component to display */
  icon?: ReactNode;
  /** Primary message */
  title: string;
  /** Secondary description */
  description?: string;
  /** Optional action button */
  action?: ReactNode;
  className?: string;
}

/**
 * Empty state display for pages, lists, and sections with no data.
 * Inspired by Linear/GitHub empty state patterns.
 */
export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[300px] flex-col items-center justify-center gap-4 rounded-lg border border-dashed p-8 text-center",
        className,
      )}
    >
      <div className="text-muted-foreground">
        {icon ?? <Inbox className="h-12 w-12" />}
      </div>
      <div>
        <h3 className="text-base font-semibold">{title}</h3>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
