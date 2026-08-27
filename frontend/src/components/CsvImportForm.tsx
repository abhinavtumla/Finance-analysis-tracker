import { useRef, useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { importTransactions } from "../api/transactions";
import { useAuth } from "../context/AuthContext";
import type { TransactionImportSummary } from "../types/transaction";

interface CsvImportFormProps {
  onImported: () => void;
}

export function CsvImportForm({ onImported }: CsvImportFormProps) {
  const { token } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<TransactionImportSummary | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!token || !file) return;

    setError(null);
    setSummary(null);
    setIsSubmitting(true);
    try {
      const result = await importTransactions(token, file);
      setSummary(result);
      if (result.imported_count > 0) {
        onImported();
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Import failed.");
    } finally {
      setIsSubmitting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const failedRows = summary?.results.filter((r) => r.status === "failed") ?? [];

  return (
    <section className="transaction-form-section">
      <h2>Import from CSV</h2>
      <p className="hint">
        Columns: <code>date</code> (YYYY-MM-DD), <code>description</code>, <code>category</code> (must match an
        existing category name), <code>amount</code> (signed: positive for income, negative for expense).
      </p>
      <form className="transaction-form-actions" onSubmit={handleSubmit}>
        <input type="file" accept=".csv" ref={fileInputRef} required />
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Importing..." : "Import"}
        </button>
      </form>

      {error && <p className="form-error">{error}</p>}

      {summary && (
        <div>
          <p>
            Imported {summary.imported_count} of {summary.total_rows} row(s)
            {summary.failed_count > 0 && ` — ${summary.failed_count} failed`}.
          </p>
          {failedRows.length > 0 && (
            <table className="transaction-table">
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {failedRows.map((row) => (
                  <tr key={row.row_number}>
                    <td>{row.row_number}</td>
                    <td className="form-error">{row.error}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </section>
  );
}
