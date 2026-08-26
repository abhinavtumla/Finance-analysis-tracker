import { apiRequest } from "./client";
import type {
  GoalContributionPayload,
  GoalCreatePayload,
  GoalResponse,
  GoalUpdatePayload,
} from "../types/goal";

export function fetchGoals(token: string) {
  return apiRequest<GoalResponse[]>("/goals/", { token });
}

export function createGoal(token: string, payload: GoalCreatePayload) {
  return apiRequest<GoalResponse>("/goals/", { method: "POST", body: payload, token });
}

export function updateGoal(token: string, id: number, payload: GoalUpdatePayload) {
  return apiRequest<GoalResponse>(`/goals/${id}`, { method: "PUT", body: payload, token });
}

export function contributeToGoal(token: string, id: number, payload: GoalContributionPayload) {
  return apiRequest<GoalResponse>(`/goals/${id}/contribute`, { method: "POST", body: payload, token });
}

export function deleteGoal(token: string, id: number) {
  return apiRequest<void>(`/goals/${id}`, { method: "DELETE", token });
}
