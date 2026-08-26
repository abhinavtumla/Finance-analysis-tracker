import { apiRequest } from "./client";
import type { DashboardSummary } from "../types/dashboard";

export function fetchDashboardSummary(token: string, month: number, year: number) {
  const params = new URLSearchParams({ month: String(month), year: String(year) });
  return apiRequest<DashboardSummary>(`/dashboard/?${params.toString()}`, { token });
}
