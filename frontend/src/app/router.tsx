import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { RootLayout } from "@/layouts/root-layout";
import { ErrorBoundary } from "@/components/error-boundary";
import { HomePage } from "@/app/pages/home";
import { SettingsPage } from "@/app/pages/settings";
import { NotFoundPage } from "@/app/pages/not-found";
import { RequirementAnalysisPage } from "@/modules/requirement-analysis/pages/analysis-page";
import { SessionDetailPage } from "@/modules/requirement-analysis/pages/session-detail-page";
import { ApiTestGenerationPage } from "@/modules/api-test-generation/pages/generation-page";
import { ApiTestSessionDetailPage } from "@/modules/api-test-generation/pages/session-detail-page";

const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    errorElement: (
      <ErrorBoundary>
        <RootLayout />
      </ErrorBoundary>
    ),
    children: [
      { index: true, element: <HomePage /> },
      { path: "settings", element: <SettingsPage /> },
      // Requirement Analysis module
      { path: "requirements/analyze", element: <RequirementAnalysisPage /> },
      { path: "requirements/sessions/:sessionId", element: <SessionDetailPage /> },
      // API Test Generation module
      { path: "api-tests/analyze", element: <ApiTestGenerationPage /> },
      { path: "api-tests/sessions/:sessionId", element: <ApiTestSessionDetailPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
