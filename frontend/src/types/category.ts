// Mirrors app/schemas/category.py.

export interface CategoryResponse {
  id: number;
  name: string;
  type: string; // "income" | "expense" by convention, not enforced by the backend schema
  is_default: boolean;
  created_at: string;
}

export interface CategoryCreatePayload {
  name: string;
  type: string;
}

export interface CategoryUpdatePayload {
  name?: string;
  type?: string;
}
