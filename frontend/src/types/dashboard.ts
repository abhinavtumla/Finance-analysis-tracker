// Mirrors app/schemas/dashboard.py.
// Note: Decimal fields serialize as JSON strings (e.g. "1234.56"), not numbers —
// confirmed by hitting the live endpoint. percentage_used is a plain float.

export interface DashboardSummary {
  total_balance: string;
  monthly_income: string;
  monthly_expenses: string;
  monthly_budget: string | null;
  remaining_budget: string | null;
  percentage_used: number | null;
  amount_exceeded: string | null;
}
