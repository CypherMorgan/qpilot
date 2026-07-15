import { Moon, Sun, ExternalLink, Trash2, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { useState } from "react";

import { useTheme } from "@/hooks/use-theme";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { APP_NAME, APP_VERSION } from "@/lib/constants";
import { deleteExpiredSessions } from "@/services/cleanup";

export function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [cleanupResult, setCleanupResult] = useState<{
    deleted: number;
    retention_days: number;
  } | null>(null);
  const [cleanupPending, setCleanupPending] = useState(false);
  const [cleanupError, setCleanupError] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleCleanup = async () => {
    setCleanupPending(true);
    setCleanupError(null);
    setCleanupResult(null);
    setConfirmOpen(false);
    try {
      const result = await deleteExpiredSessions();
      setCleanupResult(result);
    } catch (err) {
      setCleanupError(
        (err as { message?: string })?.message ?? "Cleanup failed",
      );
    } finally {
      setCleanupPending(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="mt-1 text-muted-foreground">
          Configure your {APP_NAME} preferences.
        </p>
      </div>

      <Separator />

      {/* Appearance */}
      <section>
        <h2 className="text-base font-semibold">Appearance</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Customize the look and feel of {APP_NAME}.
        </p>

        <div className="mt-4 flex gap-2">
          <Button
            variant={theme === "light" ? "default" : "outline"}
            size="sm"
            onClick={() => setTheme("light")}
            className="gap-2"
          >
            <Sun className="h-4 w-4" />
            Light
          </Button>
          <Button
            variant={theme === "dark" ? "default" : "outline"}
            size="sm"
            onClick={() => setTheme("dark")}
            className="gap-2"
          >
            <Moon className="h-4 w-4" />
            Dark
          </Button>
        </div>
      </section>

      <Separator />

      {/* Data Retention */}
      <section>
        <h2 className="text-base font-semibold">Data Retention</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Old analysis sessions are automatically eligible for cleanup after the
          configured retention period. Set{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">
            SESSION_RETENTION_DAYS
          </code>{" "}
          in your server environment to change the retention period (default: 90
          days).
        </p>

        <div className="mt-4">
          <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <Trash2 className="h-4 w-4" />
                Clean Up Old Sessions
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Clean up old sessions?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete all analysis sessions older than
                  the configured retention period. This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleCleanup}>
                  Clean Up
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>

          {cleanupPending && (
            <p className="mt-2 flex items-center gap-1.5 text-sm text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Cleaning up expired sessions...
            </p>
          )}

          {cleanupResult && (
            <p className="mt-2 text-sm text-emerald-600 dark:text-emerald-400">
              {cleanupResult.deleted} expired session
              {cleanupResult.deleted !== 1 ? "s" : ""} deleted (retention:{" "}
              {cleanupResult.retention_days} days)
            </p>
          )}

          {cleanupError && (
            <p className="mt-2 text-sm text-destructive">{cleanupError}</p>
          )}
        </div>
      </section>

      <Separator />

      {/* About */}
      <section>
        <h2 className="text-base font-semibold">About</h2>
        <div className="mt-2 space-y-1 text-sm text-muted-foreground">
          <p>{APP_NAME} v{APP_VERSION}</p>
          <p>AI-Powered Quality Engineering Platform</p>
          <Link
            to="/changelog"
            className="mt-2 inline-flex items-center gap-1 text-primary hover:underline"
          >
            What's New
            <ExternalLink className="h-3 w-3" />
          </Link>
        </div>
      </section>
    </div>
  );
}
