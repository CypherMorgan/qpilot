import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useHealth } from "@/hooks/use-health";

vi.mock("@/services/health", () => ({
  getHealthStatus: vi.fn(),
}));

function TestHealthComponent() {
  const { data, isLoading, isError } = useHealth();

  if (isLoading) return <p>Loading...</p>;
  if (isError) return <p>Error loading health</p>;
  if (data) return <p>Status: {data.status}</p>;
  return <p>No data</p>;
}

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("useHealth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    const { getByText } = renderWithQuery(<TestHealthComponent />);
    expect(getByText("Loading...")).toBeInTheDocument();
  });
});
