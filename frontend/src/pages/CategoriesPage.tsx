import { useEffect, useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { createCategory, deleteCategory, fetchCategories, updateCategory } from "../api/categories";
import { useAuth } from "../context/AuthContext";
import type { CategoryResponse } from "../types/category";

export function CategoriesPage() {
  const { token } = useAuth();

  const [categories, setCategories] = useState<CategoryResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create-form state
  const [name, setName] = useState("");
  const [type, setType] = useState("expense");
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Inline edit state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editType, setEditType] = useState("expense");
  const [rowError, setRowError] = useState<string | null>(null);

  function reloadCategories() {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    fetchCategories(token)
      .then(setCategories)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load categories."))
      .finally(() => setIsLoading(false));
  }

  useEffect(reloadCategories, [token]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setFormError(null);
    setIsSubmitting(true);
    try {
      await createCategory(token, { name, type });
      setName("");
      reloadCategories();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to create category.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function startEditing(category: CategoryResponse) {
    setEditingId(category.id);
    setEditName(category.name);
    setEditType(category.type);
    setRowError(null);
  }

  async function saveEdit(id: number) {
    if (!token) return;
    setRowError(null);
    try {
      await updateCategory(token, id, { name: editName, type: editType });
      setEditingId(null);
      reloadCategories();
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : "Failed to update category.");
    }
  }

  async function handleDelete(category: CategoryResponse) {
    if (!token) return;
    const warning = category.is_default
      ? `"${category.name}" is one of your default categories. `
      : "";
    if (
      !window.confirm(
        `${warning}Delete "${category.name}"? Existing transactions/budgets using it will be left pointing at a deleted category.`,
      )
    ) {
      return;
    }
    try {
      await deleteCategory(token, category.id);
      reloadCategories();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete category.");
    }
  }

  return (
    <div>
      <h1>Categories</h1>

      <section className="transaction-form-section">
        <h2>Add a category</h2>
        <form className="transaction-form" onSubmit={handleCreate}>
          <label>
            Name
            <input type="text" value={name} onChange={(event) => setName(event.target.value)} required />
          </label>
          <label>
            Type
            <select value={type} onChange={(event) => setType(event.target.value)}>
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </label>
          {formError && <p className="form-error">{formError}</p>}
          <div className="transaction-form-actions">
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Add category"}
            </button>
          </div>
        </form>
      </section>

      {isLoading && <p>Loading...</p>}
      {error && <p className="form-error">{error}</p>}

      {!isLoading && !error && (
        <table className="transaction-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Default</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {categories.map((category) => (
              <tr key={category.id}>
                {editingId === category.id ? (
                  <>
                    <td>
                      <input
                        type="text"
                        value={editName}
                        onChange={(event) => setEditName(event.target.value)}
                      />
                    </td>
                    <td>
                      <select value={editType} onChange={(event) => setEditType(event.target.value)}>
                        <option value="expense">Expense</option>
                        <option value="income">Income</option>
                      </select>
                    </td>
                    <td>{category.is_default ? "Yes" : ""}</td>
                    <td className="transaction-actions">
                      <button onClick={() => saveEdit(category.id)}>Save</button>
                      <button onClick={() => setEditingId(null)}>Cancel</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td>{category.name}</td>
                    <td>{category.type}</td>
                    <td>{category.is_default ? "Yes" : ""}</td>
                    <td className="transaction-actions">
                      <button onClick={() => startEditing(category)}>Edit</button>
                      <button onClick={() => handleDelete(category)}>Delete</button>
                    </td>
                  </>
                )}
              </tr>
            ))}
            {categories.length === 0 && (
              <tr>
                <td colSpan={4}>No categories yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
      {rowError && <p className="form-error">{rowError}</p>}
    </div>
  );
}
