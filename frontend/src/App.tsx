import { Providers } from "@/app/providers";
import { AppRouter } from "@/app/router";

/**
 * Root application component.
 *
 * Responsibilities:
 * 1. Wrap the entire app in Providers (TanStack Query, Theme, Tooltip)
 * 2. Render the router
 *
 * This component should remain minimal — logic lives in ./app/ and ./layouts/.
 */
function App() {
  return (
    <Providers>
      <AppRouter />
    </Providers>
  );
}

export default App;
