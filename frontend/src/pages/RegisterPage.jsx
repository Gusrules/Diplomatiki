import React, { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api.js";

function isValidEmail(v) {
  // απλό email check (frontend UX). Το backend (EmailStr) είναι το “source of truth”.
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim());
}

function splitBackendError(msg) {
  // backend σου επιστρέφει: "email: ... | password: ..."
  // το κάνουμε λίστα γραμμών
  if (!msg) return [];
  return String(msg)
    .split(" | ")
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [errLines, setErrLines] = useState([]);
  const [ok, setOk] = useState("");

  const nav = useNavigate();

  // ✅ realtime password rules
  const pwdChecks = useMemo(() => {
    const p = password || "";
    return {
      len: p.length >= 6,
      number: /\d/.test(p),
      upper: /[A-Z]/.test(p),
      special: /[^A-Za-z0-9]/.test(p), // οποιοσδήποτε “ειδικός” χαρακτήρας
    };
  }, [password]);

  const pwdOk = pwdChecks.len && pwdChecks.number && pwdChecks.upper && pwdChecks.special;

  // ✅ realtime email UX check
  const emailOk = useMemo(() => {
    if (!email.trim()) return false;
    return isValidEmail(email);
  }, [email]);

  const canSubmit = name.trim().length >= 2 && emailOk && pwdOk;

  async function submit(e) {
    e.preventDefault();
    try {
      setErrLines([]);
      setOk("");

      await api.registerStudent({
        name: name.trim(),
        email: email.trim(),
        password,
      });

      setOk("✅ Account created. You can login now.");
      nav("/login", { replace: true });
    } catch (e2) {
      setOk("");
      setErrLines(splitBackendError(e2.message));
    }
  }

  // μικρό helper UI για checklist
  function CheckRow({ ok, label }) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ width: 18, display: "inline-block", textAlign: "center" }}>
          {ok ? "✅" : "⬜"}
        </span>
        <span style={{ color: ok ? "rgba(255,255,255,.9)" : "rgba(255,255,255,.65)" }}>{label}</span>
      </div>
    );
  }

  return (
    <div className="card" style={{ maxWidth: 460, margin: "40px auto", padding: 16 }}>
      <h2 style={{ marginTop: 0 }}>Create student account</h2>

      <form onSubmit={submit} style={{ display: "grid", gap: 10 }}>
        <label>
          Name:
          <input value={name} onChange={(e) => setName(e.target.value)} style={{ width: "100%" }} />
        </label>

        <label>
          Email:
          <input value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: "100%" }} />
        </label>

        {/* ✅ μικρό realtime hint για email */}
        {email.trim() && !emailOk && (
          <div style={{ color: "rgba(255,255,255,.7)", fontSize: 13 }}>
            Tip: make sure to use a valid email address (example: name@example.com).
          </div>
        )}

        <label>
          Password:
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: "100%" }}
          />
        </label>

        {/* ✅ realtime password checks */}
        <div className="card" style={{ padding: 12, display: "grid", gap: 6 }}>
          <div style={{ fontWeight: 900, marginBottom: 4 }}>Password requirements</div>
          <CheckRow ok={pwdChecks.len} label="At least 6 characters" />
          <CheckRow ok={pwdChecks.number} label="Contains a number (0-9)" />
          <CheckRow ok={pwdChecks.upper} label="Contains an uppercase letter (A-Z)" />
          <CheckRow ok={pwdChecks.special} label="Contains a special character (e.g. !,@,#)" />
        </div>

        {/* ✅ prettier errors */}
        {errLines.length > 0 && (
          <div style={{ color: "crimson" }}>
            <div style={{ fontWeight: 900, marginBottom: 6 }}>Fix the following:</div>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {errLines.map((line, idx) => (
                <li key={idx}>{line}</li>
              ))}
            </ul>
          </div>
        )}

        {ok && <div style={{ color: "limegreen" }}>{ok}</div>}

        <button className="btn btn-primary" type="submit" disabled={!canSubmit}>
          Create account
        </button>

        <div style={{ marginTop: 6, color: "rgba(255,255,255,.7)" }}>
          Already have an account? <Link to="/login">Login</Link>
        </div>
      </form>
    </div>
  );
}
