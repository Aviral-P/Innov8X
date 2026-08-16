export interface DashboardSummary {
  total_invoices: number;
  failed_invoices: number;
  passed_invoices: number;
  total_overcharge: number;
  average_overcharge: number;
}

export interface BreakdownItem {
  name: string;
  count: number;
  amount: number;
}

export interface DashboardBreakdown {
  errors: BreakdownItem[];
  severity: BreakdownItem[];
}

export interface RecentAudit {
  invoice_id: string;
  shipment_id: string;
  load_id: string;
  status: string;
  severity: string;
  overcharge_amount: number;
}

export interface DashboardResponse {
  summary: DashboardSummary;
  breakdown: DashboardBreakdown;
  recent_audits: RecentAudit[];
}