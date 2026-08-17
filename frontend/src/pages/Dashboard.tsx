import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  CircleDollarSign,
  FileText,
  RefreshCw,
  XCircle,
} from "lucide-react";

import type { AuditResponse } from "../types/audit";

const STORAGE_KEY = "innov8x_audits";

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function loadAudits(): AuditResponse[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);

    if (!stored) {
      return [];
    }

    return JSON.parse(stored) as AuditResponse[];
  } catch {
    return [];
  }
}

function Dashboard() {
  const [audits, setAudits] = useState<AuditResponse[]>(loadAudits);

  function refreshDashboard() {
    setAudits(loadAudits());
  }

  useEffect(() => {
    function handleAuditComplete() {
      refreshDashboard();
    }

    window.addEventListener("innov8x-audit-complete", handleAuditComplete);

    return () => {
      window.removeEventListener("innov8x-audit-complete", handleAuditComplete);
    };
  }, []);

  const totalInvoices = audits.length;

  const failedInvoices = audits.filter(
    (audit) => audit.status === "FAIL",
  ).length;

  const passedInvoices = audits.filter(
    (audit) => audit.status === "PASS",
  ).length;

  const totalOvercharge = audits.reduce(
    (sum, audit) => sum + (audit.financial_summary?.overcharge_amount ?? 0),
    0,
  );

  const averageOvercharge =
    failedInvoices > 0 ? totalOvercharge / failedInvoices : 0;

  const errorBreakdown = new Map<string, { count: number; amount: number }>();

  const severityBreakdown = new Map<
    string,
    { count: number; amount: number }
  >();

  audits.forEach((audit) => {
    audit.findings.forEach((finding) => {
      const existing = errorBreakdown.get(finding.type);

      errorBreakdown.set(finding.type, {
        count: (existing?.count ?? 0) + 1,
        amount: (existing?.amount ?? 0) + Math.max(finding.variance, 0),
      });
    });

    const severity = audit.severity;

    const existingSeverity = severityBreakdown.get(severity);

    severityBreakdown.set(severity, {
      count: (existingSeverity?.count ?? 0) + 1,
      amount:
        (existingSeverity?.amount ?? 0) +
        Math.max(audit.financial_summary?.overcharge_amount ?? 0, 0),
    });
  });

  const errors = Array.from(errorBreakdown.entries()).map(([name, value]) => ({
    name,
    ...value,
  }));

  const severity = Array.from(severityBreakdown.entries()).map(
    ([name, value]) => ({
      name,
      ...value,
    }),
  );

  const recentAudits = [...audits].reverse().slice(0, 10);

  return (
    <div className="space-y-8">
      {/* HEADER */}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Management Overview
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
            Audit Intelligence
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Evidence-backed visibility across your freight invoice portfolio.
          </p>
        </div>

        <button
          type="button"
          onClick={refreshDashboard}
          className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* KPI CARDS */}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Invoices Audited"
          value={totalInvoices.toLocaleString()}
          subtitle="Total invoices analyzed"
          icon={<FileText className="h-5 w-5" />}
        />

        <MetricCard
          title="Failed Audits"
          value={failedInvoices.toLocaleString()}
          subtitle={`${passedInvoices.toLocaleString()} passed`}
          icon={<AlertTriangle className="h-5 w-5" />}
          danger
        />

        <MetricCard
          title="Financial Exposure"
          value={formatCurrency(totalOvercharge)}
          subtitle="Potential overcharge detected"
          icon={<CircleDollarSign className="h-5 w-5" />}
        />

        <MetricCard
          title="Average Overcharge"
          value={formatCurrency(averageOvercharge)}
          subtitle="Per failed invoice"
          icon={<CircleDollarSign className="h-5 w-5" />}
        />
      </div>

      {/* BREAKDOWNS */}

      <div className="grid gap-6 lg:grid-cols-2">
        <BreakdownCard title="Error Breakdown" items={errors} />

        <BreakdownCard title="Severity Breakdown" items={severity} />
      </div>

      {/* RECENT AUDITS */}

      <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-6 py-5">
          <h2 className="font-bold text-slate-950">Recent Audits</h2>

          <p className="mt-1 text-sm text-slate-500">
            Latest invoices processed by the audit engine.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-180 text-left">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Invoice
                </th>

                <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Shipment
                </th>

                <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Status
                </th>

                <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Severity
                </th>

                <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Exposure
                </th>
              </tr>
            </thead>

            <tbody>
              {recentAudits.map((audit) => (
                <tr
                  key={audit.invoice_id}
                  className="border-b border-slate-100 last:border-0"
                >
                  <td className="px-6 py-4">
                    <p className="font-semibold text-slate-900">
                      {audit.invoice_id}
                    </p>

                    <p className="text-xs text-slate-500">{audit.load_id}</p>
                  </td>

                  <td className="px-6 py-4 text-sm text-slate-600">
                    {audit.shipment_id}
                  </td>

                  <td className="px-6 py-4">
                    <StatusBadge status={audit.status} />
                  </td>

                  <td className="px-6 py-4">
                    <SeverityBadge severity={audit.severity} />
                  </td>

                  <td className="px-6 py-4 text-right font-semibold text-slate-900">
                    {formatCurrency(
                      audit.financial_summary?.overcharge_amount ?? 0,
                    )}
                  </td>
                </tr>
              ))}

              {recentAudits.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-10 text-center">
                    <FileText className="mx-auto h-8 w-8 text-slate-300" />

                    <p className="mt-3 text-sm font-medium text-slate-600">
                      No audits available.
                    </p>

                    <p className="mt-1 text-xs text-slate-400">
                      Run your first invoice audit to populate the dashboard.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

/* ============================================================
   METRIC CARD
============================================================ */

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  danger?: boolean;
}

function MetricCard({
  title,
  value,
  subtitle,
  icon,
  danger = false,
}: MetricCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div
        className={`flex h-10 w-10 items-center justify-center rounded-xl ${
          danger ? "bg-red-50 text-red-600" : "bg-slate-100 text-slate-700"
        }`}
      >
        {icon}
      </div>

      <p className="mt-5 text-sm text-slate-500">{title}</p>

      <p className="mt-1 text-2xl font-bold text-slate-950">{value}</p>

      <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
    </div>
  );
}

/* ============================================================
   BREAKDOWN CARD
============================================================ */

interface BreakdownItem {
  name: string;
  count: number;
  amount: number;
}

interface BreakdownCardProps {
  title: string;
  items: BreakdownItem[];
}

function BreakdownCard({ title, items }: BreakdownCardProps) {
  const maxCount = Math.max(...items.map((item) => item.count), 1);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="font-bold text-slate-950">{title}</h2>

      <div className="mt-6 space-y-5">
        {items.map((item) => (
          <div key={item.name}>
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm font-medium capitalize text-slate-700">
                {item.name.replaceAll("_", " ")}
              </span>

              <span className="text-sm font-semibold text-slate-900">
                {item.count}
              </span>
            </div>

            <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-slate-900 transition-all"
                style={{
                  width: `${(item.count / maxCount) * 100}%`,
                }}
              />
            </div>

            {item.amount > 0 && (
              <p className="mt-1 text-xs text-slate-400">
                {formatCurrency(item.amount)}
              </p>
            )}
          </div>
        ))}

        {items.length === 0 && (
          <p className="text-sm text-slate-500">No breakdown data available.</p>
        )}
      </div>
    </section>
  );
}

/* ============================================================
   STATUS BADGE
============================================================ */

function StatusBadge({ status }: { status: string }) {
  const passed = status.toUpperCase() === "PASS";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${
        passed ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
      }`}
    >
      {passed ? (
        <CheckCircle2 className="h-3.5 w-3.5" />
      ) : (
        <XCircle className="h-3.5 w-3.5" />
      )}

      {status}
    </span>
  );
}

/* ============================================================
   SEVERITY BADGE
============================================================ */

function SeverityBadge({ severity }: { severity: string }) {
  const normalized = severity.toUpperCase();

  const classes =
    normalized === "CRITICAL" || normalized === "HIGH"
      ? "bg-red-100 text-red-700"
      : normalized === "MEDIUM" || normalized === "REVIEW"
        ? "bg-amber-100 text-amber-700"
        : normalized === "LOW"
          ? "bg-slate-100 text-slate-700"
          : "bg-slate-100 text-slate-700";

  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${classes}`}>
      {severity}
    </span>
  );
}

export default Dashboard;
