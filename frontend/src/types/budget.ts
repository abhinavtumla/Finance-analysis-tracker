// Mirrors app/schemas/budget.py. spent/remaining/percentage_used/is_exceeded
// are calculated live by the backend on every read, not stored.

export interface BudgetResponse {
  id: number;
  category_id: number | null; // null = an "overall" budget covering all categories
  month: number;
  year: number;
  limit_amount: string;
  spent: string;
  remaining: string;
  percentage_used: number;
  is_exceeded: boolean;
  created_at: string;
}

export interface BudgetCreatePayload {
  category_id: number | null;
  month: number;
  year: number;
  limit_amount: string;
}

export interface BudgetUpdatePayload {
  limit_amount: string;
}
