export type Dashboard = {
  repositories: number;
  total_analyses: number;
  latest_analysis_id: string | null;
  latest_analysis_status: string | null;
  latest_analysis_at: string | null;
  findings_total: number;
  findings_by_severity: Record<string, number>;
  findings_by_source: Record<string, number>;
  security_findings: number;
  files_analyzed: number;
};
