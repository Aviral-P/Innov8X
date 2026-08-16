import { useLocation, useNavigate } from "react-router-dom";
import AuditResult from "../components/AuditResult";
import type { AuditResponse } from "../types/audit";

interface LocationState {
  result?: AuditResponse;
}

function AuditResultPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const state = location.state as LocationState | null;

  const result = state?.result;

  if (!result) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-950">
            No audit result found
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Run an invoice audit first.
          </p>

          <button
            type="button"
            onClick={() => navigate("/audits/new")}
            className="mt-5 rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
          >
            Run New Audit
          </button>
        </div>
      </div>
    );
  }

  return (
    <AuditResult
      result={result}
      onReset={() => navigate("/audits/new")}
    />
  );
}

export default AuditResultPage;