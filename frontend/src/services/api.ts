import axios from "axios";
import type { AuditResponse } from "../types/audit";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 120000,
});

export function getApiErrorMessage(
  error: unknown,
): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (
      detail &&
      typeof detail === "object" &&
      "message" in detail
    ) {
      return String(detail.message);
    }

    if (error.response?.status === 422) {
      return "The uploaded document could not be accepted as a valid freight invoice.";
    }

    if (error.response?.status === 500) {
      return "The invoice audit failed on the backend.";
    }

    if (!error.response) {
      return "Unable to connect to the FreightGuard backend.";
    }
  }

  return "Unable to audit the invoice. Please try again.";
}

export async function auditInvoice(
  file: File,
): Promise<AuditResponse> {
  const formData = new FormData();

  formData.append("invoice", file);

  const response = await api.post<AuditResponse>(
    "/api/v1/audits",
    formData,
  );

  return response.data;
}