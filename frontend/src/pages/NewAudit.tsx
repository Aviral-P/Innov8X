import { useNavigate } from "react-router-dom";
import InvoiceUploader from "../components/InvoiceUploader";
import type { AuditResponse } from "../types/audit";

function NewAudit() {
  const navigate = useNavigate();

  function handleAuditComplete(result: AuditResponse) {
    navigate("/audits/result", {
      state: {
        result,
      },
    });
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
          Invoice Audit
        </p>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
          Run New Audit
        </h1>

        <p className="mt-2 max-w-2xl text-sm text-slate-500">
          Upload a freight invoice and Innov8X will compare it against
          contractual and operational evidence.
        </p>
      </div>

      <InvoiceUploader
        onAuditComplete={handleAuditComplete}
      />
    </div>
  );
}

export default NewAudit;