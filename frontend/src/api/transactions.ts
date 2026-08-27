import { apiRequest } from "./client";
import type {
  TransactionCreatePayload,
  TransactionFilters,
  TransactionImportSummary,
  TransactionResponse,
  TransactionUpdatePayload,
} from "../types/transaction";

export function fetchTransactions(token: string, filters: TransactionFilters) {
  const params = new URLSearchParams();
  if (filters.category_id !== undefined) params.set("category_id", String(filters.category_id));
  if (filters.start_date) params.set("start_date", filters.start_date);
  if (filters.end_date) params.set("end_date", filters.end_date);
  if (filters.search) params.set("search", filters.search);
  params.set("skip", String(filters.skip ?? 0));
  params.set("limit", String(filters.limit ?? 20));

  return apiRequest<TransactionResponse[]>(`/transactions/?${params.toString()}`, { token });
}

export function createTransaction(token: string, payload: TransactionCreatePayload) {
  return apiRequest<TransactionResponse>("/transactions/", { method: "POST", body: payload, token });
}

export function updateTransaction(token: string, id: number, payload: TransactionUpdatePayload) {
  return apiRequest<TransactionResponse>(`/transactions/${id}`, { method: "PUT", body: payload, token });
}

export function deleteTransaction(token: string, id: number) {
  return apiRequest<void>(`/transactions/${id}`, { method: "DELETE", token });
}

export function importTransactions(token: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<TransactionImportSummary>("/transactions/import", {
    method: "POST",
    body: formData,
    token,
  });
}
