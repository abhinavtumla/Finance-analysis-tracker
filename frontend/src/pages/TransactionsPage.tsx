import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { fetchCategories } from "../api/categories";
import { createTransaction, deleteTransaction, fetchTransactions, updateTransaction } from "../api/transactions";
import { TransactionForm } from "../components/TransactionForm";
import { useAuth } from "../context/AuthContext";
import type { CategoryResponse } from "../types/category";
import type { TransactionResponse } from "../types/transaction";
import { formatCurrency } from "../utils/format";

const PAGE_SIZE = 20;

export function TransactionsPage() {
  const { token } = useAuth();

  const [categories, setCategories] = useState<CategoryResponse[]>([]);
  const [transactions, setTransactions] = useState<TransactionResponse[]>([]);
  const [editingTransaction, setEditingTransaction] = useState<TransactionResponse | null>(null);

  const [categoryFilter, setCategoryFilter] = useState<number | "">("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    fetchCategories(token).catch(() => {
      // Category fetch failure surfaces via the transaction list error below
      // when the user tries to create/edit; nothing to show here on its own.
    }).then((data) => data && setCategories(data));
  }, [token]);

  function reloadTransactions() {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    fetchTransactions(token, {
      category_id: categoryFilter === "" ? undefined : categoryFilter,
      search: search || undefined,
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
    })
      .then(setTransactions)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load transactions."))
      .finally(() => setIsLoading(false));
  }

  useEffect(reloadTransactions, [token, categoryFilter, search, page]);

  function categoryName(categoryId: number): string {
    return categories.find((c) => c.id === categoryId)?.name ?? `#${categoryId}`;
  }

  async function handleCreate(payload: Parameters<typeof createTransaction>[1]) {
    if (!token) return;
    await createTransaction(token, payload);
    setPage(0);
    reloadTransactions();
  }

  async function handleUpdate(payload: Parameters<typeof updateTransaction>[2]) {
    if (!token || !editingTransaction) return;
    await updateTransaction(token, editingTransaction.id, payload);
    setEditingTransaction(null);
    reloadTransactions();
  }

  async function handleDelete(transaction: TransactionResponse) {
    if (!token) return;
    if (!window.confirm(`Delete this ${formatCurrency(transaction.amount)} transaction?`)) return;
    await deleteTransaction(token, transaction.id);
    reloadTransactions();
  }

  return (
    <div>
      <h1>Transactions</h1>

      <section className="transaction-form-section">
        <h2>{editingTransaction ? "Edit transaction" : "Add a transaction"}</h2>
        <TransactionForm
          categories={categories}
          initialValues={editingTransaction ?? undefined}
          submitLabel={editingTransaction ? "Save changes" : "Add transaction"}
          onSubmit={editingTransaction ? handleUpdate : handleCreate}
          onCancel={editingTransaction ? () => setEditingTransaction(null) : undefined}
        />
      </section>

      <section className="transaction-filters">
        <input
          type="search"
          placeholder="Search description..."
          value={search}
          onChange={(event) => {
            setPage(0);
            setSearch(event.target.value);
          }}
        />
        <select
          value={categoryFilter}
          onChange={(event) => {
            setPage(0);
            setCategoryFilter(event.target.value === "" ? "" : Number(event.target.value));
          }}
        >
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </section>

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">{error}</p>}

      {!isLoading && !error && (
        <>
          <table className="transaction-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Description</th>
                <th>Amount</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction) => (
                <tr key={transaction.id}>
                  <td>{transaction.transaction_date}</td>
                  <td>{categoryName(transaction.category_id)}</td>
                  <td>{transaction.description ?? ""}</td>
                  <td className={parseFloat(transaction.amount) < 0 ? "amount-negative" : "amount-positive"}>
                    {formatCurrency(transaction.amount)}
                  </td>
                  <td className="transaction-actions">
                    <button onClick={() => setEditingTransaction(transaction)}>Edit</button>
                    <button onClick={() => handleDelete(transaction)}>Delete</button>
                  </td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td colSpan={5}>No transactions found.</td>
                </tr>
              )}
            </tbody>
          </table>

          <div className="pagination">
            <button disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span>Page {page + 1}</span>
            <button disabled={transactions.length < PAGE_SIZE} onClick={() => setPage((p) => p + 1)}>
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
