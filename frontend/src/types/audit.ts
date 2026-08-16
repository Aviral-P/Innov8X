export type AuditStatus = "PASS" | "FAIL";

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface FinancialSummary {
  billed_amount: number;
  expected_amount: number;
  overcharge_amount: number;
}

export interface Finding {
  type: string;
  title: string;
  billed_amount: number;
  expected_amount: number;
  variance: number;
  actual_distance_miles?: number;
  contract_rate_per_mile?: number;
  calculation?: string;
  explanation: string;
}

export interface RateCheck {
  status: AuditStatus;
  actual_distance: number;
  contract_rate_per_mile: number;
  expected_transportation: number;
  billed_transportation: number;
  variance: number;
}

export interface FuelSurchargeCheck {
  status: AuditStatus;
  contract_rate: number;
  expected_fuel: number;
  billed_fuel: number;
  variance: number;
}

export interface AccessorialCheck {
  status: AuditStatus;
  expected: number;
  billed: number;
  variance: number;
}

export interface DetentionCheck {
  status: AuditStatus;
  detention_minutes: number;
  free_minutes: number;
  expected: number;
  billed: number;
  variance: number;
}

export interface AuditChecks {
  rate: RateCheck;
  fuel_surcharge: FuelSurchargeCheck;
  accessorial: AccessorialCheck;
  detention: DetentionCheck;
}

export interface Evidence {
  contract_source: string;
  shipment_source: string;
  load_source: string;
  delivery_source: string;
}

export interface MatchingResult {
  match_status: string;
  confidence: string;
  match_method: string;
  shipment_id: string;
  load_id: string;
  trip_id: string;
  customer_id: string;
  route_id: string;
}

export interface Invoice {
  invoice_number: string;
  invoice_date: string;
  shipment_reference: string | null;
  load_reference: string | null;
  customer_id: string | null;
  po_number: string | null;
  bol_number: string | null;
  operator_name: string | null;
  truck_number: string | null;
  pickup_address: string | null;
  pickup_contact: string | null;
  destination_address: string | null;
  destination_contact: string | null;
  loaded_mileage_start: number | null;
  loaded_mileage_end: number | null;
  loaded_mileage_total: number | null;
  empty_mileage_start: number | null;
  empty_mileage_end: number | null;
  empty_mileage_total: number | null;
  transportation_charge: number;
  fuel_charge: number;
  accessorial_charge: number;
  detention_charge: number;
  permits_charge: number | null;
  escorts_charge: number | null;
  special_handling_charge: number | null;
  grand_total: number;
  currency: string | null;
}

export interface MlAnalysis {
  risk: number | null;
  anomaly_score: number | null;
}

export interface AuditResult {
  invoice_id: string;
  shipment_id: string;
  load_id: string;
  contract_id: string;
  status: AuditStatus;
  severity: Severity;
  financial_summary: FinancialSummary;
  findings: Finding[];
  checks: AuditChecks;
  evidence: Evidence;
  ml: MlAnalysis;
  matching: MatchingResult;
  invoice: Invoice;
}

export interface AuditResponse extends AuditResult {
  message: string | null;
}