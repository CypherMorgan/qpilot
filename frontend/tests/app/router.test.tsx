import { describe, it, expect } from "vitest";
import { renderWithProviders } from "@/../tests/test-utils";
import { useLocation } from "react-router-dom";

/**
 * Helper that renders the current route path inside the test providers.
 */
function RoutePathDisplay() {
  const location = useLocation();
  return <div data-testid="route-path">{location.pathname}</div>;
}

describe("Router", () => {
  it("renders at / route", () => {
    const { getByTestId } = renderWithProviders(<RoutePathDisplay />, {
      initialEntries: ["/"],
    });
    expect(getByTestId("route-path")).toHaveTextContent("/");
  });

  it("renders at /settings route", () => {
    const { getByTestId } = renderWithProviders(<RoutePathDisplay />, {
      initialEntries: ["/settings"],
    });
    expect(getByTestId("route-path")).toHaveTextContent("/settings");
  });

  it("renders at unknown routes", () => {
    const { getByTestId } = renderWithProviders(<RoutePathDisplay />, {
      initialEntries: ["/nonexistent"],
    });
    expect(getByTestId("route-path")).toHaveTextContent("/nonexistent");
  });
});
