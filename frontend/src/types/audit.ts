export type AuditStatus =
  | "PASS"
  | "FAIL"
  | "INSUFFICIENT_EVIDENCE"
  | "UNKNOWN";

export type Severity =
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL"
  | "REVIEW"
  | "UNKNOWN";

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
  actual_distance_miles?: number | null;
  contract_rate_per_mile?: number | null;
  calculation?: string | null;
  explanation: string;
}

export interface RateCheck {
  status: string;
  actual_distance: number;
  contract_rate_per_mile: number;
  expected_transportation: number;
  billed_transportation: number;
  variance: number;
}

export interface FuelSurchargeCheck {
  status: string;
  contract_rate: number;
  expected_fuel: number;
  billed_fuel: number;
  variance: number;
}

export interface AccessorialCheck {
  status: string;
  expected: number;
  billed: number;
  variance: number;
}

export interface DetentionCheck {
  status: string;
  detention_minutes: number;
  free_minutes: number;
  expected: number;
  billed: number;
  variance: number;
}

export interface AuditChecks {
  rate?: RateCheck;
  fuel_surcharge?: FuelSurchargeCheck;
  accessorial?: AccessorialCheck;
  detention?: DetentionCheck;
  [key: string]: unknown;
}

export interface Evidence {
  contract_source: string | null;
  shipment_source: string | null;
  load_source: string | null;
  delivery_source: string | null;
}

export interface MatchingResult {
  match_status: string;
  confidence: string;
  match_method: string;
  shipment_id?: string | null;
  load_id?: string | null;
  trip_id?: string | null;
  customer_id?: string | null;
  route_id?: string | null;
  contract_id?: string | null;
  reason?: string | null;
  candidate_count?: number;
  unmatched_identifiers?: Record<string, string | null>;
  [key: string]: unknown;
}

export interface ExtractionResult {
  document_type: string;
  confidence: number | null;
  needs_review: boolean;
  missing_fields: string[];
  review_reasons: string[];
}

export interface InvoiceLineItem {
  description: string;
  quantity?: number | null;
  unit?: string | null;
  unit_price?: number | null;
  amount?: number | null;
  category?: string | null;
}

export interface Invoice {
  invoice_number: string;
  invoice_date: string;
  shipment_reference: string | null;
  load_reference: string | null;
  customer_id: string | null;
  po_number: string | null;
  bol_number: string | null;
  pro_number?: string | null;
  carrier_name?: string | null;
  carrier_reference?: string | null;
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
  transportation_charge: number | null;
  fuel_charge: number | null;
  accessorial_charge: number | null;
  detention_charge: number | null;
  permits_charge: number | null;
  escorts_charge: number | null;
  special_handling_charge: number | null;
  subtotal?: number | null;
  tax?: number | null;
  grand_total: number | null;
  currency: string | null;
  payment_terms?: string | null;
  additional_charges?: unknown[];
  line_items?: InvoiceLineItem[];
  additional_references?: unknown[];
  raw_fields?: Record<string, unknown>;
  extraction_metadata?: Record<string, unknown>;
}

export interface MlAnalysis {
  risk: string | null;
  anomaly_score: number | null;
}

export interface AuditResult {
  invoice_id: string;
  shipment_id: string;
  load_id: string;
  contract_id: string;
  status: AuditStatus;
  severity: Severity;
  extraction: ExtractionResult;
  financial_summary: FinancialSummary;
  findings: Finding[];
  checks: AuditChecks;
  evidence: Evidence;
  ml: MlAnalysis;
  matching: MatchingResult;
  invoice: Invoice;
}

export type AuditResponse = AuditResult;