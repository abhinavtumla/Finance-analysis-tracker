import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div>
      <header className="app-header">
        <div className="app-header-left">
          <span className="app-title">Finance Tracker</span>
          <nav className="app-nav">
            <NavLink to="/" end>
              Dashboard
            </NavLink>
            <NavLink to="/transactions">Transactions</NavLink>
            <NavLink to="/categories">Categories</NavLink>
            <NavLink to="/budgets">Budgets</NavLink>
            <NavLink to="/goals">Goals</NavLink>
          </nav>
        </div>
        <span className="app-header-right">
          {user?.email}
          <button onClick={logout}>Log out</button>
        </span>
      </header>
      <main>{children}</main>
    </div>
  );
}
