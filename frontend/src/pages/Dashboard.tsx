import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  CircleDollarSign,
  FileText,
  RefreshCw,
  XCircle,
} from "lucide-react";

import { getDashboard } from "../services/api";
import type {
  BreakdownItem,
  DashboardResponse,
} from "../types/dashboard";

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function Dashboard() {
  const [data, setData] =
    useState<DashboardResponse | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] =
    useState<string | null>(null);

  async function loadDashboard() {
    try {
      setLoading(true);
      setError(null);

      const result = await getDashboard();

      setData(result);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to load dashboard data. Make sure the backend is running.",
      );
    } finally {
      setLoading(false);
    }
  }

  /*
   * Initial dashboard load.
   *
   * We intentionally don't call loadDashboard() here because
   * loadDashboard() immediately changes loading state. Keeping
   * the initial fetch inside the async function below avoids
   * the React effect lint warning about synchronous state
   * updates inside an effect.
   */
  useEffect(() => {
    let cancelled = false;

    async function fetchInitialDashboard() {
      try {
        const result = await getDashboard();

        if (!cancelled) {
          setData(result);
        }
      } catch (err) {
        console.error(err);

        if (!cancelled) {
          setError(
            "Unable to load dashboard data. Make sure the backend is running.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void fetchInitialDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  /*
   * Loading state
   */
  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <RefreshCw className="mx-auto h-8 w-8 animate-spin text-slate-500" />

          <p className="mt-3 text-sm text-slate-500">
            Loading audit intelligence...
          </p>
        </div>
      </div>
    );
  }

  /*
   * Error state
   */
  if (error || !data) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
          <XCircle className="mx-auto h-8 w-8 text-red-600" />

          <p className="mt-3 text-sm text-red-700">
            {error ?? "Dashboard data unavailable."}
          </p>

          <button
            type="button"
            onClick={loadDashboard}
            className="mt-5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const {
    summary,
    breakdown,
    recent_audits,
  } = data;

  return (
    <div className="space-y-8">
      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

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
          onClick={loadDashboard}
          className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* ================================================== */}
      {/* KPI CARDS */}
      {/* ================================================== */}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Invoices Audited"
          value={summary.total_invoices.toLocaleString()}
          subtitle="Total invoices analyzed"
          icon={<FileText className="h-5 w-5" />}
        />

        <MetricCard
          title="Failed Audits"
          value={summary.failed_invoices.toLocaleString()}
          subtitle={`${summary.passed_invoices.toLocaleString()} passed`}
          icon={<AlertTriangle className="h-5 w-5" />}
          danger
        />

        <MetricCard
          title="Financial Exposure"
          value={formatCurrency(summary.total_overcharge)}
          subtitle="Potential overcharge detected"
          icon={<CircleDollarSign className="h-5 w-5" />}
        />

        <MetricCard
          title="Average Overcharge"
          value={formatCurrency(summary.average_overcharge)}
          subtitle="Per failed invoice"
          icon={<CircleDollarSign className="h-5 w-5" />}
        />
      </div>

      {/* ================================================== */}
      {/* BREAKDOWNS */}
      {/* ================================================== */}

      <div className="grid gap-6 lg:grid-cols-2">
        <BreakdownCard
          title="Error Breakdown"
          items={breakdown.errors}
          formatAmount
        />

        <BreakdownCard
          title="Severity Breakdown"
          items={breakdown.severity}
          formatAmount
        />
      </div>

      {/* ================================================== */}
      {/* RECENT AUDITS */}
      {/* ================================================== */}

      <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-6 py-5">
          <h2 className="font-bold text-slate-950">
            Recent Audits
          </h2>

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
              {recent_audits.map((audit) => (
                <tr
                  key={audit.invoice_id}
                  className="border-b border-slate-100 last:border-0"
                >
                  <td className="px-6 py-4">
                    <p className="font-semibold text-slate-900">
                      {audit.invoice_id}
                    </p>

                    <p className="text-xs text-slate-500">
                      {audit.load_id}
                    </p>
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
                      audit.overcharge_amount,
                    )}
                  </td>
                </tr>
              ))}

              {recent_audits.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="px-6 py-10 text-center text-sm text-slate-500"
                  >
                    No audits available.
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

/* ====================================================== */
/* METRIC CARD */
/* ====================================================== */

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
          danger
            ? "bg-red-50 text-red-600"
            : "bg-slate-100 text-slate-700"
        }`}
      >
        {icon}
      </div>

      <p className="mt-5 text-sm text-slate-500">
        {title}
      </p>

      <p className="mt-1 text-2xl font-bold text-slate-950">
        {value}
      </p>

      <p className="mt-1 text-xs text-slate-400">
        {subtitle}
      </p>
    </div>
  );
}

/* ====================================================== */
/* BREAKDOWN CARD */
/* ====================================================== */

interface BreakdownCardProps {
  title: string;
  items: BreakdownItem[];
  formatAmount?: boolean;
}

function BreakdownCard({
  title,
  items,
  formatAmount = false,
}: BreakdownCardProps) {
  const maxCount = Math.max(
    ...items.map((item) => item.count),
    1,
  );

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="font-bold text-slate-950">
        {title}
      </h2>

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

            {formatAmount && item.amount > 0 && (
              <p className="mt-1 text-xs text-slate-400">
                {formatCurrency(item.amount)}
              </p>
            )}
          </div>
        ))}

        {items.length === 0 && (
          <p className="text-sm text-slate-500">
            No breakdown data available.
          </p>
        )}
      </div>
    </section>
  );
}

/* ====================================================== */
/* STATUS BADGE */
/* ====================================================== */

function StatusBadge({
  status,
}: {
  status: string;
}) {
  const passed =
    status.toUpperCase() === "PASS";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${
        passed
          ? "bg-emerald-100 text-emerald-700"
          : "bg-red-100 text-red-700"
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

/* ====================================================== */
/* SEVERITY BADGE */
/* ====================================================== */

function SeverityBadge({
  severity,
}: {
  severity: string;
}) {
  const normalized =
    severity.toUpperCase();

  const classes =
    normalized === "CRITICAL" ||
    normalized === "HIGH"
      ? "bg-red-100 text-red-700"
      : normalized === "MEDIUM"
        ? "bg-amber-100 text-amber-700"
        : "bg-slate-100 text-slate-700";

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-bold ${classes}`}
    >
      {severity}
    </span>
  );
}

export default Dashboard;