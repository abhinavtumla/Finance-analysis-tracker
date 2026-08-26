# Finance Tracker frontend

React + TypeScript + Vite frontend for the Personal Finance Tracker API.

## Setup

```bash
npm install
cp .env.example .env   # points VITE_API_BASE_URL at the backend
npm run dev
```

Requires the backend running at the URL configured in `.env` (default `http://localhost:8000`), with CORS configured to allow this app's origin (`http://localhost:5173` by default — see `app/config.py`'s `cors_origins`).

## Structure

- `src/api/` — typed fetch calls to each backend router, built on `src/api/client.ts`
- `src/types/` — TypeScript interfaces mirroring the backend's Pydantic schemas
- `src/context/AuthContext.tsx` — holds the JWT + current user, persists the token to `localStorage`
- `src/components/` — shared UI (`Layout`, `ProtectedRoute`, `TransactionForm`)
- `src/pages/` — one component per route (Login, Register, Dashboard, Transactions, Budgets, Goals)
- `src/utils/` — currency formatting and the signed-amount helper (`money.ts`) that keeps Decimal amounts as strings end-to-end instead of parsing them into floats
