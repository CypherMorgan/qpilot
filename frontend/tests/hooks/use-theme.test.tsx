import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider, useTheme } from "@/hooks/use-theme";

function TestConsumer() {
  const { theme, toggleTheme, setTheme } = useTheme();
  return (
    <div>
      <p data-testid="theme">{theme}</p>
      <button data-testid="toggle" onClick={toggleTheme}>
        Toggle
      </button>
      <button data-testid="set-light" onClick={() => setTheme("light")}>
        Light
      </button>
      <button data-testid="set-dark" onClick={() => setTheme("dark")}>
        Dark
      </button>
    </div>
  );
}

describe("ThemeProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
  });

  it("provides default theme", () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    const themeEl = screen.getByTestId("theme");
    expect(["light", "dark"]).toContain(themeEl.textContent);
  });

  it("toggles theme on button click", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );

    const themeEl = screen.getByTestId("theme");
    const initialTheme = themeEl.textContent;

    await user.click(screen.getByTestId("toggle"));
    const toggledTheme = themeEl.textContent;
    expect(toggledTheme).not.toBe(initialTheme);
  });

  it("sets theme explicitly", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );

    await user.click(screen.getByTestId("set-dark"));
    expect(screen.getByTestId("theme")).toHaveTextContent("dark");

    await user.click(screen.getByTestId("set-light"));
    expect(screen.getByTestId("theme")).toHaveTextContent("light");
  });
});
