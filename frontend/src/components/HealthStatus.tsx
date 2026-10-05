import type { HealthResponse } from "../types/health";

type HealthStatusProps = {
  health: HealthResponse | null;
  error: string | null;
};

export function HealthStatus({ health, error }: HealthStatusProps) {
  if (error) return <p className="status status-error">{error}</p>;
  if (!health) return <p className="status">Connecting to the API...</p>;
  return (
    <p className="status status-ok">
      API healthy: {health.service} ({health.environment})
    </p>
  );
}
