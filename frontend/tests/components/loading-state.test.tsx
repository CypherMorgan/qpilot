import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LoadingState } from "@/components/loading-state";

describe("LoadingState", () => {
  it("renders a spinner", () => {
    const { container } = render(<LoadingState />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("renders an optional message", () => {
    render(<LoadingState message="Loading data..." />);
    expect(screen.getByText("Loading data...")).toBeInTheDocument();
  });

  it("applies fullPage layout when specified", () => {
    const { container } = render(<LoadingState fullPage />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("min-h-[60vh]");
  });
});
