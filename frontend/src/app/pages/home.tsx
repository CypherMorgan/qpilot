import { useNavigate } from "react-router-dom";
import { useHealth } from "@/hooks/use-health";
import { LoadingState } from "@/components/loading-state";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Activity, ArrowRight, Server, Database, Cpu } from "lucide-react";
import { ROUTES } from "@/lib/constants";

export function HomePage() {
  const navigate = useNavigate();
  const { data: health, isLoading, isError, error, refetch } = useHealth();

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-muted-foreground">
          Welcome to QPilot — your AI-powered quality engineering platform.
        </p>
      </div>

      {/* Health status card */}
      <section>
        <h2 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          System Status
        </h2>

        {isLoading && <LoadingState message="Checking backend connection..." />}

        {isError && (
          <EmptyState
            icon={<Server className="h-12 w-12 text-destructive" />}
            title="Backend Unavailable"
            description={
              (error as { message?: string })?.message ??
              "Could not connect to the backend server."
            }
            action={
              <Button variant="outline" onClick={() => refetch()}>
                <Activity className="mr-2 h-4 w-4" />
                Retry connection
              </Button>
            }
          />
        )}

        {health && (
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Server className="h-4 w-4" />
                <span>Status</span>
              </div>
              <p className="mt-2 text-lg font-semibold text-emerald-500">
                {health.status}
              </p>
            </div>

            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Database className="h-4 w-4" />
                <span>Database</span>
              </div>
              <p className="mt-2 text-lg font-semibold">
                {health.checks.database.status}
              </p>
              <p className="text-xs text-muted-foreground">
                {health.checks.database.latency_ms}ms latency
              </p>
            </div>

            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Cpu className="h-4 w-4" />
                <span>Version</span>
              </div>
              <p className="mt-2 text-lg font-semibold font-mono">
                {health.app_version}
              </p>
            </div>
          </div>
        )}
      </section>

      {/* Coming soon modules */}
      <section>
        <h2 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Modules
        </h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <button
            type="button"
            onClick={() => navigate(ROUTES.REQUIREMENT_ANALYSIS)}
            className="group relative w-full rounded-lg border bg-card p-5 text-left transition-colors hover:border-muted-foreground/25"
          >
            <ModuleCard
              title="Requirement Analysis"
              description="Transform requirements into structured test cases"
              status="Live"
            />
          </button>
          <button
            type="button"
            onClick={() => navigate(ROUTES.API_TEST_GENERATION)}
            className="group relative w-full rounded-lg border bg-card p-5 text-left transition-colors hover:border-muted-foreground/25"
          >
            <ModuleCard
              title="API Test Generation"
              description="Generate PyTest suites from OpenAPI specs"
              status="Live"
            />
          </button>
          <button
            type="button"
            onClick={() => navigate(ROUTES.FAILURE_ANALYSIS)}
            className="group relative w-full rounded-lg border bg-card p-5 text-left transition-colors hover:border-muted-foreground/25"
          >
            <ModuleCard
              title="Failure Analysis"
              description="Analyze failure artifacts with AI-powered root cause detection"
              status="Live"
            />
          </button>
        </div>
      </section>
    </div>
  );
}

function ModuleCard({
  title,
  description,
  status,
}: {
  title: string;
  description: string;
  status: string;
}) {
  return (
    <div className="group relative rounded-lg border bg-card p-5 transition-colors hover:border-muted-foreground/25">
      <div className="flex items-start justify-between">
        <h3 className="font-semibold">{title}</h3>
        <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
          {status}
        </span>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      <div className="mt-4 flex items-center gap-1 text-sm font-medium text-muted-foreground group-hover:text-foreground">
        <span>Get started</span>
        <ArrowRight className="h-3 w-3" />
      </div>
    </div>
  );
}
