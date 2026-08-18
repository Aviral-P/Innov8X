import { useNavigate } from "react-router-dom";
import { ShieldCheck, FileSearch } from "lucide-react";
import InvoiceUploader from "../components/InvoiceUploader";
import type { AuditResponse } from "../types/audit";

function NewAudit() {
  const navigate = useNavigate();

  function handleAuditComplete(result: AuditResponse) {
  const key = "innov8x_audits";

  const existing = JSON.parse(
    localStorage.getItem(key) ?? "[]",
  ) as AuditResponse[];

  const updated = [
    ...existing.filter(
      (audit) =>
        audit.invoice_id !== result.invoice_id,
    ),
    result,
  ];

  localStorage.setItem(
    key,
    JSON.stringify(updated),
  );

  window.dispatchEvent(
    new Event("innov8x-audit-complete"),
  );

  navigate("/audits/result", {
    state: {
      result,
    },
  });
}

  return (
    <div className="space-y-8">
      <div>
        <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
          <ShieldCheck className="h-4 w-4" />
          Invoice Audit
        </p>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
          Run New Audit
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
          Upload a freight invoice and FreightGuard will extract the billing data,
          match it against available evidence, and identify supported
          discrepancies.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
        <InvoiceUploader onAuditComplete={handleAuditComplete} />

        <div className="h-fit rounded-2xl border border-slate-200 bg-slate-50 p-6">
          <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white shadow-sm">
            <FileSearch className="h-5 w-5 text-slate-700" />
          </div>

          <h2 className="font-semibold text-slate-900">
            Evidence-first auditing
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            A missing operational record does not become a guessed match.
            When evidence is insufficient, FreightGuard sends the invoice for
            review instead of inventing an audit result.
          </p>

          <div className="mt-5 space-y-3 text-sm">
            <div className="flex gap-3">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
              <span className="text-slate-600">Extract invoice data</span>
            </div>
            <div className="flex gap-3">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
              <span className="text-slate-600">Match operational records</span>
            </div>
            <div className="flex gap-3">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
              <span className="text-slate-600">Validate contractual charges</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default NewAudit;