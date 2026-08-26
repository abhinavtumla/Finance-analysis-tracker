import { apiRequest } from "./client";
import type { LoginPayload, RegisterPayload, TokenResponse, UserResponse } from "../types/auth";

export function registerUser(payload: RegisterPayload) {
  return apiRequest<UserResponse>("/auth/register", { method: "POST", body: payload });
}

export function loginUser(payload: LoginPayload) {
  return apiRequest<TokenResponse>("/auth/login", { method: "POST", body: payload });
}

export function fetchCurrentUser(token: string) {
  return apiRequest<UserResponse>("/auth/me", { token });
}
