// Mirrors app/schemas/transaction.py.
// `amount` is kept as a string end-to-end on the frontend (never parsed into a
// JS `number` for editing/sending) so we never introduce floating-point
// rounding into a value the backend treats as an exact Decimal.

export interface TransactionResponse {
  id: number;
  category_id: number;
  amount: string;
  description: string | null;
  transaction_date: string; // YYYY-MM-DD
  created_at: string;
}

export interface TransactionCreatePayload {
  category_id: number;
  amount: string;
  description?: string | null;
  transaction_date: string;
}

export interface TransactionUpdatePayload {
  category_id?: number;
  amount?: string;
  description?: string | null;
  transaction_date?: string;
}

export interface TransactionFilters {
  category_id?: number;
  start_date?: string;
  end_date?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface TransactionImportRowResult {
  row_number: number;
  status: "imported" | "failed";
  error: string | null;
}

export interface TransactionImportSummary {
  total_rows: number;
  imported_count: number;
  failed_count: number;
  results: TransactionImportRowResult[];
}
