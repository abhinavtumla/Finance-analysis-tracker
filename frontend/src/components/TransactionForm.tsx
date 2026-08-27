import { useEffect, useRef, useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { suggestCategory } from "../api/transactions";
import { useAuth } from "../context/AuthContext";
import type { CategoryResponse } from "../types/category";
import type { TransactionCreatePayload } from "../types/transaction";
import { toMagnitude, toSignedAmount } from "../utils/money";

export interface TransactionFormValues {
  category_id: number;
  amount: string; // signed, as returned by the backend
  description: string | null;
  transaction_date: string;
}

interface TransactionFormProps {
  categories: CategoryResponse[];
  initialValues?: TransactionFormValues;
  submitLabel: string;
  onSubmit: (payload: TransactionCreatePayload) => Promise<void>;
  onCancel?: () => void;
}

const today = () => new Date().toISOString().slice(0, 10);

export function TransactionForm({
  categories,
  initialValues,
  submitLabel,
  onSubmit,
  onCancel,
}: TransactionFormProps) {
  const { token } = useAuth();
  const [categoryId, setCategoryId] = useState<number | "">(initialValues?.category_id ?? "");
  const [magnitude, setMagnitude] = useState(
    initialValues ? toMagnitude(initialValues.amount) : "",
  );
  const [description, setDescription] = useState(initialValues?.description ?? "");
  const [transactionDate, setTransactionDate] = useState(initialValues?.transaction_date ?? today());
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Tracks whether the user has explicitly chosen a category, so the
  // description-blur auto-suggestion below never overwrites a deliberate
  // choice (including an existing category when editing).
  const hasChosenCategory = useRef(initialValues !== undefined);

  // Re-sync the form whenever a different transaction is loaded for editing.
  useEffect(() => {
    setCategoryId(initialValues?.category_id ?? "");
    setMagnitude(initialValues ? toMagnitude(initialValues.amount) : "");
    setDescription(initialValues?.description ?? "");
    setTransactionDate(initialValues?.transaction_date ?? today());
    setError(null);
    hasChosenCategory.current = initialValues !== undefined;
  }, [initialValues]);

  const selectedCategory = categories.find((c) => c.id === categoryId);

  async function handleDescriptionBlur() {
    if (!token || hasChosenCategory.current || !description.trim()) return;
    try {
      const suggestion = await suggestCategory(token, description);
      // Only apply it if the user still hasn't picked a category by the
      // time this comes back — they may have already chosen one manually
      // while the request was in flight.
      if (suggestion.category_id !== null && !hasChosenCategory.current) {
        setCategoryId(suggestion.category_id);
      }
    } catch {
      // Best-effort convenience feature — a failed suggestion just means no
      // pre-fill happens, nothing to show the user.
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selectedCategory) {
      setError("Choose a category.");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit({
        category_id: selectedCategory.id,
        amount: toSignedAmount(magnitude, selectedCategory.type),
        description: description || null,
        transaction_date: transactionDate,
      });
      if (!initialValues) {
        // Creating a new transaction: clear the form for the next entry,
        // including the category so the next description gets its own
        // fresh suggestion instead of inheriting this one.
        setCategoryId("");
        setMagnitude("");
        setDescription("");
        hasChosenCategory.current = false;
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save transaction.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="transaction-form" onSubmit={handleSubmit}>
      <label>
        Category
        <select
          value={categoryId}
          onChange={(event) => {
            hasChosenCategory.current = true;
            setCategoryId(Number(event.target.value));
          }}
          required
        >
          <option value="" disabled>
            Select a category
          </option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name} ({category.type})
            </option>
          ))}
        </select>
      </label>
      <label>
        Amount
        <input
          type="number"
          min="0.01"
          step="0.01"
          value={magnitude}
          onChange={(event) => setMagnitude(event.target.value)}
          required
        />
      </label>
      <label>
        Description
        <input
          type="text"
          value={description ?? ""}
          onChange={(event) => setDescription(event.target.value)}
          onBlur={handleDescriptionBlur}
        />
      </label>
      <label>
        Date
        <input
          type="date"
          value={transactionDate}
          onChange={(event) => setTransactionDate(event.target.value)}
          required
        />
      </label>
      {error && <p className="form-error">{error}</p>}
      <div className="transaction-form-actions">
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : submitLabel}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
