import { useEffect, useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { fetchCategories } from "../api/categories";
import { createBudget, deleteBudget, fetchBudgets, updateBudget } from "../api/budgets";
import { useAuth } from "../context/AuthContext";
import type { BudgetResponse } from "../types/budget";
import type { CategoryResponse } from "../types/category";
import { formatCurrency } from "../utils/format";
import { MONTH_NAMES } from "../utils/months";

const today = new Date();
const YEAR_OPTIONS = [today.getFullYear() - 1, today.getFullYear(), today.getFullYear() + 1];

export function BudgetsPage() {
  const { token } = useAuth();

  const [categories, setCategories] = useState<CategoryResponse[]>([]);
  const [budgets, setBudgets] = useState<BudgetResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create-form state
  const [categoryValue, setCategoryValue] = useState<string>(""); // "" = overall budget
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year, setYear] = useState(today.getFullYear());
  const [limitAmount, setLimitAmount] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Inline edit state (only limit_amount is editable, per the backend)
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingLimit, setEditingLimit] = useState("");

  useEffect(() => {
    if (!token) return;
    fetchCategories(token).then(setCategories).catch(() => {});
  }, [token]);

  function reloadBudgets() {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    fetchBudgets(token)
      .then(setBudgets)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load budgets."))
      .finally(() => setIsLoading(false));
  }

  useEffect(reloadBudgets, [token]);

  const expenseCategories = categories.filter((c) => c.type === "expense");

  function categoryName(categoryId: number | null): string {
    if (categoryId === null) return "Overall";
    return categories.find((c) => c.id === categoryId)?.name ?? `#${categoryId}`;
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setFormError(null);
    setIsSubmitting(true);
    try {
      await createBudget(token, {
        category_id: categoryValue === "" ? null : Number(categoryValue),
        month,
        year,
        limit_amount: limitAmount,
      });
      setLimitAmount("");
      reloadBudgets();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to create budget.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function startEditing(budget: BudgetResponse) {
    setEditingId(budget.id);
    setEditingLimit(budget.limit_amount);
  }

  async function saveEdit(id: number) {
    if (!token) return;
    try {
      await updateBudget(token, id, { limit_amount: editingLimit });
      setEditingId(null);
      reloadBudgets();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update budget.");
    }
  }

  async function handleDelete(budget: BudgetResponse) {
    if (!token) return;
    if (!window.confirm(`Delete the ${categoryName(budget.category_id)} budget for ${MONTH_NAMES[budget.month - 1]} ${budget.year}?`)) {
      return;
    }
    await deleteBudget(token, budget.id);
    reloadBudgets();
  }

  const sortedBudgets = [...budgets].sort((a, b) => {
    if (a.year !== b.year) return b.year - a.year;
    if (a.month !== b.month) return b.month - a.month;
    return categoryName(a.category_id).localeCompare(categoryName(b.category_id));
  });

  return (
    <div>
      <h1>Budgets</h1>

      <section className="transaction-form-section">
        <h2>Set a budget</h2>
        <form className="transaction-form" onSubmit={handleCreate}>
          <label>
            Category
            <select value={categoryValue} onChange={(event) => setCategoryValue(event.target.value)}>
              <option value="">Overall (all categories)</option>
              {expenseCategories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Month
            <select value={month} onChange={(event) => setMonth(Number(event.target.value))}>
              {MONTH_NAMES.map((name, index) => (
                <option key={name} value={index + 1}>
                  {name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Year
            <select value={year} onChange={(event) => setYear(Number(event.target.value))}>
              {YEAR_OPTIONS.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </label>
          <label>
            Limit amount
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={limitAmount}
              onChange={(event) => setLimitAmount(event.target.value)}
              required
            />
          </label>
          {formError && <p className="form-error">{formError}</p>}
          <div className="transaction-form-actions">
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Set budget"}
            </button>
          </div>
        </form>
      </section>

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">{error}</p>}

      {!isLoading && !error && (
        <div className="budget-list">
          {sortedBudgets.map((budget) => (
            <div key={budget.id} className="budget-card">
              <div className="budget-card-header">
                <h2>
                  {categoryName(budget.category_id)} — {MONTH_NAMES[budget.month - 1]} {budget.year}
                </h2>
                <div className="transaction-actions">
                  <button onClick={() => startEditing(budget)}>Edit</button>
                  <button onClick={() => handleDelete(budget)}>Delete</button>
                </div>
              </div>

              {editingId === budget.id ? (
                <div className="transaction-form-actions">
                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={editingLimit}
                    onChange={(event) => setEditingLimit(event.target.value)}
                  />
                  <button onClick={() => saveEdit(budget.id)}>Save</button>
                  <button onClick={() => setEditingId(null)}>Cancel</button>
                </div>
              ) : (
                <>
                  <p>
                    {formatCurrency(budget.spent)} of {formatCurrency(budget.limit_amount)} spent
                  </p>
                  <div className="progress-bar">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${Math.min(budget.percentage_used, 100)}%` }}
                    />
                  </div>
                  {budget.is_exceeded ? (
                    <p className="form-error">
                      Over budget by {formatCurrency((parseFloat(budget.spent) - parseFloat(budget.limit_amount)).toFixed(2))}
                    </p>
                  ) : (
                    <p>{formatCurrency(budget.remaining)} remaining</p>
                  )}
                </>
              )}
            </div>
          ))}
          {sortedBudgets.length === 0 && <p>No budgets set yet.</p>}
        </div>
      )}
    </div>
  );
}
