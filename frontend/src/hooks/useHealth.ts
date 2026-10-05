import { useEffect, useState } from "react";

import { fetchHealth } from "../services/api";
import type { HealthResponse } from "../types/health";

export function useHealth() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((requestError: unknown) => {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to reach the API",
        );
      });
  }, []);

  return { health, error };
}
