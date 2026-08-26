import { useEffect, useState } from "react";
import { fetchDashboardSummary } from "../api/dashboard";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { DashboardSummary } from "../types/dashboard";
import { formatCurrency } from "../utils/format";
import { MONTH_NAMES } from "../utils/months";

export function DashboardPage() {
  const { token } = useAuth();
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year, setYear] = useState(today.getFullYear());
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    fetchDashboardSummary(token, month, year)
      .then((data) => {
        if (!cancelled) setSummary(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load dashboard.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token, month, year]);

  const yearOptions = [today.getFullYear() - 1, today.getFullYear(), today.getFullYear() + 1];

  return (
    <div>
      <h1>Dashboard</h1>

      <div className="month-selector">
        <select value={month} onChange={(event) => setMonth(Number(event.target.value))}>
          {MONTH_NAMES.map((name, index) => (
            <option key={name} value={index + 1}>
              {name}
            </option>
          ))}
        </select>
        <select value={year} onChange={(event) => setYear(Number(event.target.value))}>
          {yearOptions.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </div>

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">{error}</p>}

      {summary && !isLoading && !error && (
        <div className="summary-grid">
          <SummaryCard label="Total Balance (all time)" value={formatCurrency(summary.total_balance)} />
          <SummaryCard label="Income this month" value={formatCurrency(summary.monthly_income)} />
          <SummaryCard label="Expenses this month" value={formatCurrency(summary.monthly_expenses)} />

          {summary.monthly_budget !== null && (
            <div className="budget-card">
              <h2>Overall Budget</h2>
              <p>
                {formatCurrency(summary.monthly_expenses)} of {formatCurrency(summary.monthly_budget)} spent
              </p>
              <ProgressBar percentage={summary.percentage_used ?? 0} />
              {summary.amount_exceeded !== null && parseFloat(summary.amount_exceeded) > 0 ? (
                <p className="form-error">Over budget by {formatCurrency(summary.amount_exceeded)}</p>
              ) : (
                <p>{formatCurrency(summary.remaining_budget ?? "0")} remaining</p>
              )}
            </div>
          )}

          {summary.monthly_budget === null && (
            <p className="hint">No overall budget set for this month.</p>
          )}
        </div>
      )}
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-card">
      <p className="summary-label">{label}</p>
      <p className="summary-value">{value}</p>
    </div>
  );
}

function ProgressBar({ percentage }: { percentage: number }) {
  const clamped = Math.min(Math.max(percentage, 0), 100);
  return (
    <div className="progress-bar">
      <div className="progress-bar-fill" style={{ width: `${clamped}%` }} />
    </div>
  );
}
