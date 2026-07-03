import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  /** Optional message to display below the spinner */
  message?: string;
  /** Size variant */
  size?: "sm" | "default" | "lg";
  /** Full-page centered layout */
  fullPage?: boolean;
  className?: string;
}

export function LoadingState({
  message,
  size = "default",
  fullPage = false,
  className,
}: LoadingStateProps) {
  const sizeMap = {
    sm: "h-4 w-4",
    default: "h-8 w-8",
    lg: "h-12 w-12",
  };

  const content = (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3",
        fullPage ? "min-h-[60vh]" : "py-8",
        className,
      )}
    >
      <Loader2
        className={cn("animate-spin text-muted-foreground", sizeMap[size])}
      />
      {message && (
        <p className="text-sm text-muted-foreground">{message}</p>
      )}
    </div>
  );

  return content;
}
