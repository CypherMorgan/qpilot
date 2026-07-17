/** Reusable search & filter bar for session history pages. */

import { Search, X } from "lucide-react";

interface SessionSearchProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  statusFilter: string;
  onStatusFilterChange: (value: string) => void;
  total: number;
  filtered: number;
}

const STATUS_OPTIONS = [
  { value: "all", label: "All" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "processing", label: "Processing" },
];

export function SessionSearch({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  total,
  filtered,
}: SessionSearchProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Search input */}
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/50" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search by title or summary..."
          className="w-full rounded-lg border bg-background py-2 pl-9 pr-8 text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-ring"
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange("")}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-muted-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Status filter */}
      <div className="flex gap-1.5">
        {STATUS_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onStatusFilterChange(opt.value)}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
              statusFilter === opt.value
                ? "border-primary bg-primary/5 text-primary"
                : "border-border/60 text-muted-foreground hover:border-muted-foreground/30"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Count */}
      <p className="text-xs text-muted-foreground whitespace-nowrap">
        {filtered === total
          ? `${total} session${total !== 1 ? "s" : ""}`
          : `${filtered} of ${total} session${total !== 1 ? "s" : ""}`}
      </p>
    </div>
  );
}
