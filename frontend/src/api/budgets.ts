import { apiRequest } from "./client";
import type { BudgetCreatePayload, BudgetResponse, BudgetUpdatePayload } from "../types/budget";

export function fetchBudgets(token: string) {
  return apiRequest<BudgetResponse[]>("/budgets/", { token });
}

export function createBudget(token: string, payload: BudgetCreatePayload) {
  return apiRequest<BudgetResponse>("/budgets/", { method: "POST", body: payload, token });
}

export function updateBudget(token: string, id: number, payload: BudgetUpdatePayload) {
  return apiRequest<BudgetResponse>(`/budgets/${id}`, { method: "PUT", body: payload, token });
}

export function deleteBudget(token: string, id: number) {
  return apiRequest<void>(`/budgets/${id}`, { method: "DELETE", token });
}
