import { useState } from "react";
import {
  FileText,
  Upload,
  X,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { auditInvoice, getApiErrorMessage } from "../services/api";
import type { AuditResponse } from "../types/audit";

interface InvoiceUploaderProps {
  onAuditComplete: (result: AuditResponse) => void;
}

const ACCEPTED_EXTENSIONS = [
  ".pdf",
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
  ".tif",
  ".tiff",
  ".eml",
];

function InvoiceUploader({ onAuditComplete }: InvoiceUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) return;

    const extension = `.${selectedFile.name.split(".").pop()?.toLowerCase()}`;

    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setError(
        "Unsupported file. Upload a PDF, PNG, JPG, WEBP, TIFF, or EML freight invoice.",
      );
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setError(null);
  }

  function clearFile() {
    if (loading) return;
    setFile(null);
    setError(null);
  }

  async function handleAudit() {
    if (!file) {
      setError("Please select an invoice first.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const result = await auditInvoice(file);
      onAuditComplete(result);
    } catch (err) {
      console.error(err);
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-2xl">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-slate-900">
            <FileText className="h-7 w-7 text-white" />
          </div>

          <h2 className="text-2xl font-bold text-slate-900">
            Audit an Invoice
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Upload a freight invoice and FreightGuard will compare it against
            available contractual and operational evidence.
          </p>
        </div>

        {!file ? (
          <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 px-6 py-12 transition hover:border-slate-500 hover:bg-slate-50">
            <Upload className="mb-4 h-8 w-8 text-slate-400" />

            <span className="text-sm font-medium text-slate-700">
              Choose an invoice
            </span>

            <span className="mt-1 text-xs text-slate-400">
              PDF, PNG, JPG, WEBP, TIFF or EML
            </span>

            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp,.tif,.tiff,.eml"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>
        ) : (
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center justify-between">
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                </div>

                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-900">
                    {file.name}
                  </p>

                  <p className="text-xs text-slate-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={clearFile}
                disabled={loading}
                aria-label="Remove selected invoice"
                className="rounded-lg p-2 text-slate-400 transition hover:bg-white hover:text-slate-700 disabled:cursor-not-allowed"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={handleAudit}
          disabled={!file || loading}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          {loading ? "Analyzing invoice..." : "Audit Invoice"}
        </button>

        <p className="mt-3 text-center text-xs text-slate-400">
          FreightGuard will not invent operational evidence when a matching record
          cannot be verified.
        </p>
      </div>
    </div>
  );
}

export default InvoiceUploader;