import { apiRequest } from "./client";
import type { CategoryResponse } from "../types/category";

export function fetchCategories(token: string) {
  return apiRequest<CategoryResponse[]>("/categories/", { token });
}
