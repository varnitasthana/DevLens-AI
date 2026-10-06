export type Finding = {
  id: string;
  file: string;
  line: number;
  column: number;
  rule: string;
  category: string;
  severity: string;
  message: string;
  source: string;
  evidence: string | null;
  remediation: string | null;
};

export type Analysis = {
  id: string;
  repository_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  files_analyzed: number;
  analyzer_source: string;
  findings: Finding[];
};
