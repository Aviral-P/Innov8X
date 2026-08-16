import {
  AlertTriangle,
  CheckCircle2,
  CircleDollarSign,
  FileCheck2,
  FileText,
  MapPin,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import type { AuditResponse } from "../types/audit";

interface AuditResultProps {
  result: AuditResponse;
  onReset: () => void;
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function formatFindingType(value: string) {
  return value.replaceAll("_", " ");
}

function AuditResult({ result, onReset }: AuditResultProps) {
  const isFailed = result.status.toUpperCase() === "FAIL";

  const severityClass =
    {
      CRITICAL: "bg-red-100 text-red-700 border-red-200",
      HIGH: "bg-orange-100 text-orange-700 border-orange-200",
      MEDIUM: "bg-amber-100 text-amber-700 border-amber-200",
      LOW: "bg-blue-100 text-blue-700 border-blue-200",
    }[result.severity.toUpperCase()] ??
    "bg-slate-100 text-slate-700 border-slate-200";

  return (
    <div className="w-full max-w-6xl space-y-6">
      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
              <FileText className="h-4 w-4" />
              Invoice Audit
            </div>

            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
              {result.invoice_id}
            </h1>

            <p className="mt-2 text-sm text-slate-500">
              Shipment {result.shipment_id} · Load {result.load_id}
            </p>

            <p className="mt-1 text-xs text-slate-400">
              Contract {result.contract_id}
            </p>
          </div>

          <button
            type="button"
            onClick={onReset}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            Audit Another Invoice
          </button>
        </div>
      </section>

      {/* ================================================== */}
      {/* STATUS */}
      {/* ================================================== */}

      <section className="grid gap-4 md:grid-cols-3">
        {/* Audit status */}

        <div
          className={`rounded-2xl border p-6 ${
            isFailed
              ? "border-red-200 bg-red-50"
              : "border-emerald-200 bg-emerald-50"
          }`}
        >
          <div className="flex items-center gap-3">
            {isFailed ? (
              <XCircle className="h-6 w-6 text-red-600" />
            ) : (
              <CheckCircle2 className="h-6 w-6 text-emerald-600" />
            )}

            <span className="text-sm font-semibold text-slate-600">
              Audit Status
            </span>
          </div>

          <p
            className={`mt-4 text-3xl font-bold ${
              isFailed ? "text-red-700" : "text-emerald-700"
            }`}
          >
            {result.status}
          </p>
        </div>

        {/* Severity */}

        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-amber-600" />

            <span className="text-sm font-semibold text-slate-600">
              Severity
            </span>
          </div>

          <span
            className={`mt-4 inline-flex rounded-full border px-3 py-1.5 text-sm font-bold ${severityClass}`}
          >
            {result.severity}
          </span>
        </div>

        {/* Exposure */}

        <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
          <div className="flex items-center gap-3">
            <CircleDollarSign className="h-6 w-6 text-red-600" />

            <span className="text-sm font-semibold text-slate-600">
              Potential Overcharge
            </span>
          </div>

          <p className="mt-4 text-3xl font-bold text-red-700">
            {formatCurrency(result.financial_summary.overcharge_amount)}
          </p>
        </div>
      </section>

      {/* ================================================== */}
      {/* FINANCIAL SUMMARY */}
      {/* ================================================== */}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <CircleDollarSign className="h-5 w-5 text-slate-700" />

          <h2 className="text-lg font-bold text-slate-950">
            Financial Summary
          </h2>
        </div>

        <div className="grid gap-6 sm:grid-cols-3">
          <FinancialMetric
            label="Billed Amount"
            value={formatCurrency(result.financial_summary.billed_amount)}
          />

          <FinancialMetric
            label="Evidence-Supported Amount"
            value={formatCurrency(result.financial_summary.expected_amount)}
          />

          <FinancialMetric
            label="Variance"
            value={formatCurrency(result.financial_summary.overcharge_amount)}
            danger={result.financial_summary.overcharge_amount > 0}
          />
        </div>
      </section>

      {/* ================================================== */}
      {/* FINDINGS */}
      {/* ================================================== */}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <FileCheck2 className="h-5 w-5 text-slate-700" />

          <div>
            <h2 className="text-lg font-bold text-slate-950">Audit Findings</h2>

            <p className="mt-1 text-sm text-slate-500">
              Evidence-backed exceptions detected in the invoice.
            </p>
          </div>
        </div>

        {result.findings.length === 0 ? (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />

              <p className="font-semibold text-emerald-800">
                No audit findings detected.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {result.findings.map((finding, index) => (
              <div
                key={`${finding.type}-${index}`}
                className="rounded-xl border border-red-200 bg-red-50 p-5"
              >
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />

                  <div>
                    <p className="text-xs font-bold uppercase tracking-wide text-red-600">
                      {formatFindingType(finding.type)}
                    </p>

                    <h3 className="mt-1 text-lg font-bold text-slate-950">
                      {finding.title}
                    </h3>
                  </div>
                </div>

                {/* Financial comparison */}

                <div className="mt-5 grid gap-4 sm:grid-cols-3">
                  <FinancialMetric
                    label="Billed"
                    value={formatCurrency(finding.billed_amount)}
                  />

                  <FinancialMetric
                    label="Expected"
                    value={formatCurrency(finding.expected_amount)}
                  />

                  <FinancialMetric
                    label="Variance"
                    value={formatCurrency(finding.variance)}
                    danger={finding.variance > 0}
                  />
                </div>

                {/* Calculation */}

                {finding.calculation && (
                  <div className="mt-5 rounded-xl border border-slate-200 bg-white p-4">
                    <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                      Evidence Calculation
                    </p>

                    <p className="mt-2 font-mono text-sm text-slate-900">
                      {finding.calculation}
                    </p>
                  </div>
                )}

                {/* Additional finding data */}

                {(finding.actual_distance_miles !== undefined &&
                  finding.actual_distance_miles !== null) ||
                (finding.contract_rate_per_mile !== undefined &&
                  finding.contract_rate_per_mile !== null) ? (
                  <div className="mt-4 grid gap-4 sm:grid-cols-2">
                    {finding.actual_distance_miles !== undefined &&
                      finding.actual_distance_miles !== null && (
                        <div className="rounded-lg bg-white p-4">
                          <p className="text-xs text-slate-500">
                            Operational Distance
                          </p>

                          <p className="mt-1 font-bold text-slate-950">
                            {finding.actual_distance_miles.toLocaleString()}{" "}
                            miles
                          </p>
                        </div>
                      )}

                    {finding.contract_rate_per_mile !== undefined &&
                      finding.contract_rate_per_mile !== null && (
                        <div className="rounded-lg bg-white p-4">
                          <p className="text-xs text-slate-500">
                            Contract Rate
                          </p>

                          <p className="mt-1 font-bold text-slate-950">
                            ${finding.contract_rate_per_mile.toFixed(2)}
                            /mile
                          </p>
                        </div>
                      )}
                  </div>
                ) : null}

                {/* Explanation */}

                <div className="mt-5 border-t border-red-200 pt-5">
                  <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Explanation
                  </p>

                  <p className="mt-2 text-sm leading-6 text-slate-700">
                    {finding.explanation}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ================================================== */}
      {/* AUDIT CHECKS */}
      {/* ================================================== */}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <ShieldCheck className="h-5 w-5 text-slate-700" />

          <div>
            <h2 className="text-lg font-bold text-slate-950">Audit Checks</h2>

            <p className="mt-1 text-sm text-slate-500">
              Individual contractual and operational validations.
            </p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <CheckCard
            title="Contract Rate"
            status={result.checks.rate?.status ?? "UNKNOWN"}
            detail={
              result.checks.rate
                ? `${result.checks.rate.actual_distance} miles × $${result.checks.rate.contract_rate_per_mile}/mile`
                : "Rate validation unavailable"
            }
            variance={result.checks.rate?.variance ?? 0}
          />

          <CheckCard
            title="Fuel Surcharge"
            status={result.checks.fuel_surcharge?.status ?? "UNKNOWN"}
            detail={
              result.checks.fuel_surcharge
                ? `${result.checks.fuel_surcharge.contract_rate} contract rate`
                : "Fuel surcharge validation unavailable"
            }
            variance={result.checks.fuel_surcharge?.variance ?? 0}
          />

          <CheckCard
            title="Accessorial Charges"
            status={result.checks.accessorial?.status ?? "UNKNOWN"}
            detail="Operational accessorial evidence"
            variance={result.checks.accessorial?.variance ?? 0}
          />

          <CheckCard
            title="Detention"
            status={result.checks.detention?.status ?? "UNKNOWN"}
            detail={
              result.checks.detention
                ? `${result.checks.detention.detention_minutes} min detention / ${result.checks.detention.free_minutes} min free`
                : "Detention validation unavailable"
            }
            variance={result.checks.detention?.variance ?? 0}
          />
        </div>
      </section>

      {/* ================================================== */}
      {/* EVIDENCE */}
      {/* ================================================== */}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <MapPin className="h-5 w-5 text-slate-700" />

          <div>
            <h2 className="text-lg font-bold text-slate-950">
              Evidence Sources
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Operational and contractual sources supporting this audit.
            </p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <EvidenceItem
            label="Contract"
            source={result.evidence.contract_source}
          />

          <EvidenceItem
            label="Shipment"
            source={result.evidence.shipment_source}
          />

          <EvidenceItem label="Load" source={result.evidence.load_source} />

          <EvidenceItem
            label="Delivery"
            source={result.evidence.delivery_source}
          />
        </div>
      </section>

      {/* ================================================== */}
      {/* MATCHING */}
      {/* ================================================== */}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <ShieldCheck className="h-5 w-5 text-slate-700" />

          <div>
            <h2 className="text-lg font-bold text-slate-950">
              Evidence Matching
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              How the invoice was linked to operational evidence.
            </p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MatchingItem
            label="Match Status"
            value={result.matching.match_status ?? "Unknown"}
          />

          <MatchingItem
            label="Confidence"
            value={result.matching.confidence ?? "Unknown"}
          />

          <MatchingItem
            label="Match Method"
            value={result.matching.match_method ?? "Unknown"}
          />

          <MatchingItem
            label="Route"
            value={result.matching.route_id ?? "Unknown"}
          />
        </div>
      </section>

      {/* ================================================== */}
      {/* ML */}
      {/* ================================================== */}

      <section className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6">
        <div className="flex items-center gap-3">
          <ShieldCheck className="h-5 w-5 text-slate-500" />

          <div>
            <h2 className="text-lg font-bold text-slate-950">
              AI Risk Analysis
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Machine-learning risk scoring will be integrated here.
            </p>
          </div>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm text-slate-500">Risk Score</p>

            <p className="mt-2 text-3xl font-bold text-slate-400">
              {result.ml?.risk === null || result.ml?.risk === undefined
                ? "Pending"
                : result.ml.risk}
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm text-slate-500">Anomaly Score</p>

            <p className="mt-2 text-3xl font-bold text-slate-400">
              {result.ml?.anomaly_score === null ||
              result.ml?.anomaly_score === undefined
                ? "Pending"
                : result.ml.anomaly_score}
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

/* ======================================================== */
/* FINANCIAL METRIC                                         */
/* ======================================================== */

interface FinancialMetricProps {
  label: string;
  value: string;
  danger?: boolean;
}

function FinancialMetric({
  label,
  value,
  danger = false,
}: FinancialMetricProps) {
  return (
    <div>
      <p className="text-sm text-slate-500">{label}</p>

      <p
        className={`mt-1 text-2xl font-bold ${
          danger ? "text-red-600" : "text-slate-950"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

/* ======================================================== */
/* CHECK CARD                                                */
/* ======================================================== */

interface CheckCardProps {
  title: string;
  status: string;
  detail: string;
  variance: number;
}

function CheckCard({ title, status, detail, variance }: CheckCardProps) {
  const normalizedStatus = status.toUpperCase();

  const passed = normalizedStatus === "PASS";

  const failed = normalizedStatus === "FAIL";

  return (
    <div className="rounded-xl border border-slate-200 p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-semibold text-slate-900">{title}</h3>

        <span
          className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${
            passed
              ? "bg-emerald-100 text-emerald-700"
              : failed
                ? "bg-red-100 text-red-700"
                : "bg-slate-100 text-slate-600"
          }`}
        >
          {passed ? (
            <CheckCircle2 className="h-3.5 w-3.5" />
          ) : failed ? (
            <XCircle className="h-3.5 w-3.5" />
          ) : (
            <AlertTriangle className="h-3.5 w-3.5" />
          )}

          {normalizedStatus}
        </span>
      </div>

      <p className="mt-3 text-sm text-slate-500">{detail}</p>

      {variance !== 0 && (
        <p className="mt-3 text-sm font-semibold text-red-600">
          Variance: {formatCurrency(variance)}
        </p>
      )}
    </div>
  );
}

/* ======================================================== */
/* EVIDENCE ITEM                                             */
/* ======================================================== */

interface EvidenceItemProps {
  label: string;
  source?: string | null;
}

function EvidenceItem({ label, source }: EvidenceItemProps) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-200 p-4">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100">
          <FileText className="h-4 w-4 text-slate-600" />
        </div>

        <div>
          <p className="text-sm font-semibold text-slate-900">{label}</p>

          <p className="mt-0.5 text-xs text-slate-500">
            {source ?? "Source unavailable"}
          </p>
        </div>
      </div>

      <CheckCircle2
        className={`h-5 w-5 ${source ? "text-emerald-500" : "text-slate-300"}`}
      />
    </div>
  );
}

/* ======================================================== */
/* MATCHING ITEM                                            */
/* ======================================================== */

interface MatchingItemProps {
  label: string;
  value: string;
}

function MatchingItem({ label, value }: MatchingItemProps) {
  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-sm font-bold text-slate-950">{value}</p>
    </div>
  );
}

export default AuditResult;
