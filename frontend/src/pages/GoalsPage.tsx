import { useEffect, useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { contributeToGoal, createGoal, deleteGoal, fetchGoals, updateGoal } from "../api/goals";
import { useAuth } from "../context/AuthContext";
import type { GoalResponse } from "../types/goal";
import { formatCurrency } from "../utils/format";

export function GoalsPage() {
  const { token } = useAuth();

  const [goals, setGoals] = useState<GoalResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create-form state
  const [name, setName] = useState("");
  const [targetAmount, setTargetAmount] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Per-goal edit state
  const [editingGoal, setEditingGoal] = useState<GoalResponse | null>(null);
  const [editName, setEditName] = useState("");
  const [editTargetAmount, setEditTargetAmount] = useState("");
  const [editTargetDate, setEditTargetDate] = useState("");

  // Per-goal contribute state
  const [contributingGoalId, setContributingGoalId] = useState<number | null>(null);
  const [contributionAmount, setContributionAmount] = useState("");
  const [rowError, setRowError] = useState<string | null>(null);

  function reloadGoals() {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    fetchGoals(token)
      .then(setGoals)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load goals."))
      .finally(() => setIsLoading(false));
  }

  useEffect(reloadGoals, [token]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setFormError(null);
    setIsSubmitting(true);
    try {
      await createGoal(token, {
        name,
        target_amount: targetAmount,
        target_date: targetDate || null,
      });
      setName("");
      setTargetAmount("");
      setTargetDate("");
      reloadGoals();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to create goal.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function startEditing(goal: GoalResponse) {
    setContributingGoalId(null);
    setEditingGoal(goal);
    setEditName(goal.name);
    setEditTargetAmount(goal.target_amount);
    setEditTargetDate(goal.target_date ?? "");
    setRowError(null);
  }

  async function saveEdit(id: number) {
    if (!token) return;
    setRowError(null);
    try {
      await updateGoal(token, id, {
        name: editName,
        target_amount: editTargetAmount,
        target_date: editTargetDate || null,
      });
      setEditingGoal(null);
      reloadGoals();
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : "Failed to update goal.");
    }
  }

  function startContributing(goal: GoalResponse) {
    setEditingGoal(null);
    setContributingGoalId(goal.id);
    setContributionAmount("");
    setRowError(null);
  }

  async function submitContribution(id: number) {
    if (!token) return;
    setRowError(null);
    try {
      await contributeToGoal(token, id, { amount: contributionAmount });
      setContributingGoalId(null);
      reloadGoals();
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : "Failed to add contribution.");
    }
  }

  async function handleDelete(goal: GoalResponse) {
    if (!token) return;
    if (!window.confirm(`Delete the "${goal.name}" goal?`)) return;
    await deleteGoal(token, goal.id);
    reloadGoals();
  }

  return (
    <div>
      <h1>Savings Goals</h1>

      <section className="transaction-form-section">
        <h2>Create a goal</h2>
        <form className="transaction-form" onSubmit={handleCreate}>
          <label>
            Name
            <input type="text" value={name} onChange={(event) => setName(event.target.value)} required />
          </label>
          <label>
            Target amount
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={targetAmount}
              onChange={(event) => setTargetAmount(event.target.value)}
              required
            />
          </label>
          <label>
            Target date (optional)
            <input type="date" value={targetDate} onChange={(event) => setTargetDate(event.target.value)} />
          </label>
          {formError && <p className="form-error">{formError}</p>}
          <div className="transaction-form-actions">
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Create goal"}
            </button>
          </div>
        </form>
      </section>

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">{error}</p>}

      {!isLoading && !error && (
        <div className="budget-list">
          {goals.map((goal) => (
            <div key={goal.id} className="budget-card">
              {editingGoal?.id === goal.id ? (
                <div className="transaction-form">
                  <label>
                    Name
                    <input type="text" value={editName} onChange={(event) => setEditName(event.target.value)} />
                  </label>
                  <label>
                    Target amount
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={editTargetAmount}
                      onChange={(event) => setEditTargetAmount(event.target.value)}
                    />
                  </label>
                  <label>
                    Target date
                    <input
                      type="date"
                      value={editTargetDate}
                      onChange={(event) => setEditTargetDate(event.target.value)}
                    />
                  </label>
                  {rowError && <p className="form-error">{rowError}</p>}
                  <div className="transaction-form-actions">
                    <button onClick={() => saveEdit(goal.id)}>Save</button>
                    <button onClick={() => setEditingGoal(null)}>Cancel</button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="budget-card-header">
                    <h2>
                      {goal.name} {goal.is_completed && "✅"}
                    </h2>
                    <div className="transaction-actions">
                      <button onClick={() => startEditing(goal)}>Edit</button>
                      <button onClick={() => handleDelete(goal)}>Delete</button>
                    </div>
                  </div>
                  <p>
                    {formatCurrency(goal.current_amount)} of {formatCurrency(goal.target_amount)}
                    {goal.target_date && ` · by ${goal.target_date}`}
                  </p>
                  <div className="progress-bar">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                    />
                  </div>

                  {contributingGoalId === goal.id ? (
                    <div className="transaction-form-actions">
                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        placeholder="Amount"
                        value={contributionAmount}
                        onChange={(event) => setContributionAmount(event.target.value)}
                      />
                      <button onClick={() => submitContribution(goal.id)}>Add</button>
                      <button onClick={() => setContributingGoalId(null)}>Cancel</button>
                      {rowError && <p className="form-error">{rowError}</p>}
                    </div>
                  ) : (
                    <div className="transaction-form-actions">
                      <button onClick={() => startContributing(goal)}>Contribute</button>
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
          {goals.length === 0 && <p>No savings goals yet.</p>}
        </div>
      )}
    </div>
  );
}
