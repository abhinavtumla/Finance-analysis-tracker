import { useEffect, useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
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
  const [categoryId, setCategoryId] = useState<number | "">(initialValues?.category_id ?? "");
  const [magnitude, setMagnitude] = useState(
    initialValues ? toMagnitude(initialValues.amount) : "",
  );
  const [description, setDescription] = useState(initialValues?.description ?? "");
  const [transactionDate, setTransactionDate] = useState(initialValues?.transaction_date ?? today());
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Re-sync the form whenever a different transaction is loaded for editing.
  useEffect(() => {
    setCategoryId(initialValues?.category_id ?? "");
    setMagnitude(initialValues ? toMagnitude(initialValues.amount) : "");
    setDescription(initialValues?.description ?? "");
    setTransactionDate(initialValues?.transaction_date ?? today());
    setError(null);
  }, [initialValues]);

  const selectedCategory = categories.find((c) => c.id === categoryId);

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
        // Creating a new transaction: clear the form for the next entry.
        setMagnitude("");
        setDescription("");
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
          onChange={(event) => setCategoryId(Number(event.target.value))}
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
