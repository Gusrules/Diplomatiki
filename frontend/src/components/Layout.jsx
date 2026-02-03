import React, { useMemo } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { getRole, getUserId, getName, logout } from "../lib/session.js";

const shell = { maxWidth: 1100, margin: "0 auto", width: "100%" };

function RoleBadge({ role }) {
  const label = role === "teacher" ? "Teacher" : "Student";
  return (
    <span
      style={{
        fontSize: 12,
        fontWeight: 800,
        padding: "4px 10px",
        borderRadius: 999,
        background: role === "teacher" ? "#fff3cd" : "#1e3a8a",
        color: role === "teacher" ? "#7c5a00" : "#bfdbfe",
        border: "1px solid rgba(255,255,255,.15)",
      }}
    >
      {label}
    </span>
  );
}

function Avatar({ name }) {
  const letter = (name || "?")[0]?.toUpperCase() ?? "?";
  return (
    <div
      style={{
        width: 34,
        height: 34,
        borderRadius: "50%",
        display: "grid",
        placeItems: "center",
        fontWeight: 900,
        background: "rgba(255,255,255,.08)",
        border: "1px solid rgba(255,255,255,.15)",
      }}
    >
      {letter}
    </div>
  );
}

function NavLink({ to, children }) {
  const { pathname } = useLocation();
  const active = pathname === to;

  return (
    <Link
      to={to}
      style={{
        padding: "6px 10px",
        borderRadius: 10,
        fontWeight: active ? 900 : 600,
        color: active ? "#fff" : "rgba(255,255,255,.8)",
        background: active ? "rgba(255,255,255,.12)" : "transparent",
      }}
    >
      {children}
    </Link>
  );
}

export default function Layout({ children }) {
  const role = getRole();
  const userId = getUserId();
  const name = getName();
  const nav = useNavigate();
  const loc = useLocation();

  const hideHeader = loc.pathname === "/login";

  const homePath = useMemo(() => {
    if (role === "teacher") return "/t/home";
    if (role === "student") return "/u/home";
    return "/";
  }, [role]);

async function onLogout() {
    try { await api.logout(); } catch {}
    logout();
    nav("/login");
  }

  return (
    <div>
      {!hideHeader && (
        <header
          style={{
            position: "sticky",
            top: 0,
            zIndex: 50,
            backdropFilter: "blur(10px)",
            background: "rgba(10,14,24,.6)",
            borderBottom: "1px solid rgba(255,255,255,.08)",
          }}
        >
          <div
            style={{
              ...shell,
              padding: "12px 16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 14,
            }}
          >
            {/* LEFT */}
            <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
              <Link to={homePath} style={{ textDecoration: "none", color: "#fff" }}>
                <div style={{ fontWeight: 900 }}>Diplomatiki Quiz</div>
                <div style={{ fontSize: 12, opacity: 0.7 }}>
                  University quiz & spaced repetition
                </div>
              </Link>

              {role === "student" && (
                <nav style={{ display: "flex", gap: 6 }}>
                  <NavLink to="/u/home">Home</NavLink>
                  <NavLink to="/subjects">Subjects</NavLink>
                  <NavLink to="/review">Daily Review</NavLink>
                </nav>
              )}

              {role === "teacher" && (
                <nav style={{ display: "flex", gap: 6 }}>
                  <NavLink to="/t/home">Dashboard</NavLink>
                  <NavLink to="/t/subjects">My subjects</NavLink>
                </nav>
              )}
            </div>

            {/* RIGHT */}
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              {role && (
                <>
                  <RoleBadge role={role} />
                  <Avatar name={name} />
                  <button className="btn" onClick={onLogout}>
                    Logout
                  </button>
                </>
              )}
            </div>
          </div>
        </header>
      )}

      <main style={{shell, paddingTop: "24px"}}>{children}</main>
    </div>
  );
}
