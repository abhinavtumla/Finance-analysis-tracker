import { apiRequest } from "./client";
import type { CategoryCreatePayload, CategoryResponse, CategoryUpdatePayload } from "../types/category";

export function fetchCategories(token: string) {
  return apiRequest<CategoryResponse[]>("/categories/", { token });
}

export function createCategory(token: string, payload: CategoryCreatePayload) {
  return apiRequest<CategoryResponse>("/categories/", { method: "POST", body: payload, token });
}

export function updateCategory(token: string, id: number, payload: CategoryUpdatePayload) {
  return apiRequest<CategoryResponse>(`/categories/${id}`, { method: "PUT", body: payload, token });
}

export function deleteCategory(token: string, id: number) {
  return apiRequest<void>(`/categories/${id}`, { method: "DELETE", token });
}
