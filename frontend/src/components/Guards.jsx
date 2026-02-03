import React, { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { getToken, getRole, logout as clearSession } from "../lib/session.js";
import { api } from "../lib/api.js";

function FullPageLoader() {
  return (
    <div style={{ padding: 24 }}>
      <div className="card" style={{ maxWidth: 520 }}>
        <div style={{ fontWeight: 900, marginBottom: 6 }}>Checking session…</div>
        <div style={{ color: "rgba(255,255,255,.7)" }}>Please wait.</div>
      </div>
    </div>
  );
}

export function RequireAuth({ children }) {
  const token = getToken();
  const loc = useLocation();

  const [status, setStatus] = useState("checking"); // checking | ok | fail

  useEffect(() => {
    let alive = true;

    async function check() {
      if (!token) {
        if (alive) setStatus("fail");
        return;
      }

      try {
        await api.me(); // validates Bearer token
        if (alive) setStatus("ok");
      } catch (e) {
        // Αν είναι invalid/expired token => καθάρισε localStorage
        clearSession();
        if (alive) setStatus("fail");
      }
    }

    check();
    return () => {
      alive = false;
    };
  }, [token]);

  if (!token) return <Navigate to="/login" replace state={{ from: loc.pathname }} />;

  if (status === "checking") return <FullPageLoader />;

  if (status === "fail") return <Navigate to="/login" replace state={{ from: loc.pathname }} />;

  return children;
}

export function RequireRole({ role: neededRole, children }) {
  // πρώτα κάνουμε auth validation
  return (
    <RequireAuth>
      <RoleGate neededRole={neededRole}>{children}</RoleGate>
    </RequireAuth>
  );
}

function RoleGate({ neededRole, children }) {
  const role = getRole();

  if (neededRole && role !== neededRole) {
    // αν έχει token αλλά λάθος role, στείλ’τον στο σωστό home
    return <Navigate to={role === "teacher" ? "/t/home" : "/u/home"} replace />;
  }

  return children;
}
