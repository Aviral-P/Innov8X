import axios from "axios";
import type { AuditResponse } from "../types/audit";
import type { DashboardResponse } from "../types/dashboard";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

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

export async function getDashboard(): Promise<DashboardResponse> {
  const response = await api.get<DashboardResponse>(
    "/api/v1/audits/dashboard",
  );

  return response.data;
}