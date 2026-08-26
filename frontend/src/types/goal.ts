// Mirrors app/schemas/goal.py.

export interface GoalResponse {
  id: number;
  name: string;
  target_amount: string;
  current_amount: string;
  target_date: string | null;
  progress_percentage: number;
  is_completed: boolean;
  created_at: string;
}

export interface GoalCreatePayload {
  name: string;
  target_amount: string;
  current_amount?: string;
  target_date?: string | null;
}

export interface GoalUpdatePayload {
  name?: string;
  target_amount?: string;
  target_date?: string | null;
}

export interface GoalContributionPayload {
  amount: string;
}
