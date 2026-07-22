/**
 * ProtectedRoute — wraps routes that require authentication.
 * Redirects to /login if the user is not authenticated.
 * In demo mode (backend unreachable), allows access without auth.
 */

import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";

export function ProtectedRoute() {
  const { isAuthenticated, isLoading, isDemoMode } = useAuth();

  if (isLoading && !isDemoMode) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  // In demo mode, allow full access without authentication
  if (isDemoMode) {
    return <Outlet />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
