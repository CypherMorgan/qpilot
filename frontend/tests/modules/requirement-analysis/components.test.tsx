/** Tests for Requirement Analysis components. */

import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test-utils";

import { SectionCard } from "@/components/section-card";
import {
  FunctionalTestCases,
  RisksList,
  AssumptionsList,
  PriorityAssessmentBlock,
} from "@/modules/requirement-analysis/components/section-content";

describe("SectionCard", () => {
  it("renders with title and content", () => {
    renderWithProviders(
      <SectionCard title="Test Section">
        <p>Content here</p>
      </SectionCard>,
    );
    expect(screen.getByText("Test Section")).toBeTruthy();
    expect(screen.getByText("Content here")).toBeTruthy();
  });

  it("shows count badge when provided", () => {
    renderWithProviders(
      <SectionCard title="Tests" count={5}>
        <p>Items</p>
      </SectionCard>,
    );
    expect(screen.getByText("5")).toBeTruthy();
  });

  it("shows empty message when count is 0", () => {
    renderWithProviders(
      <SectionCard title="Tests" count={0} emptyMessage="Nothing here.">
        <p>Items</p>
      </SectionCard>,
    );
    expect(screen.getByText("Nothing here.")).toBeTruthy();
  });
});

describe("FunctionalTestCases", () => {
  const tests = [
    {
      id: "TC-FUNC-001",
      title: "Successful login",
      description: "Verify login works",
      preconditions: ["User exists"],
      steps: ["Enter email", "Enter password"],
      expected_result: "User is logged in",
      priority: "high" as const,
      tags: ["login"],
    },
  ];

  it("renders test case details", () => {
    renderWithProviders(<FunctionalTestCases tests={tests} />);
    expect(screen.getByText("TC-FUNC-001")).toBeTruthy();
    expect(screen.getByText("Successful login")).toBeTruthy();
    expect(screen.getByText("Verify login works")).toBeTruthy();
    expect(screen.getByText("User exists")).toBeTruthy();
    expect(screen.getByText("Enter email")).toBeTruthy();
    expect(screen.getByText("User is logged in")).toBeTruthy();
  });

  it("renders empty state gracefully", () => {
    const { container } = renderWithProviders(
      <FunctionalTestCases tests={[]} />,
    );
    expect(container.textContent).toBe("");
  });
});

describe("RisksList", () => {
  const risks = [
    {
      id: "RSK-001",
      description: "Brute force attack",
      severity: "high" as const,
      likelihood: "medium",
      mitigation: "Rate limit",
    },
  ];

  it("renders risk details", () => {
    renderWithProviders(<RisksList risks={risks} />);
    expect(screen.getByText("RSK-001")).toBeTruthy();
    expect(screen.getByText("Brute force attack")).toBeTruthy();
    expect(screen.getByText("Rate limit")).toBeTruthy();
  });
});

describe("AssumptionsList", () => {
  it("renders list of assumptions", () => {
    const items = ["Password is hashed", "Session expires in 24h"];
    renderWithProviders(<AssumptionsList items={items} />);
    expect(screen.getByText("Password is hashed")).toBeTruthy();
    expect(screen.getByText("Session expires in 24h")).toBeTruthy();
  });
});

describe("PriorityAssessmentBlock", () => {
  const assessment = {
    overall_priority: "high" as const,
    critical_path_items: ["TC-FUNC-001"],
    quick_wins: ["TC-NEG-001"],
    reasoning: "Login is the entry point.",
  };

  it("renders all assessment fields", () => {
    renderWithProviders(<PriorityAssessmentBlock assessment={assessment} />);
    expect(screen.getByText("high")).toBeTruthy();
    expect(screen.getByText("TC-FUNC-001")).toBeTruthy();
    expect(screen.getByText("TC-NEG-001")).toBeTruthy();
    expect(screen.getByText("Login is the entry point.")).toBeTruthy();
  });
});
