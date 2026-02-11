import React, { useState } from "react";
import { api } from "../lib/api.js";
import { setSession } from "../lib/session.js";
import { useNavigate, Link, useLocation } from "react-router-dom";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const nav = useNavigate();
  const loc = useLocation();

  async function submit(e) {
    e.preventDefault();
    try {
      setErr("");
      const out = await api.login({ email, password });
      setSession(out); // token, role, user_id, name
      
      const backTo = loc.state?.from;
      if (backTo) nav(backTo, { replace: true });
      else nav(out.role === "teacher" ? "/t/home" : "/u/home", { replace: true });
    } catch (e2) {
      setErr(e2.message);
    }
  }

  return (
    <div className="card" style={{ maxWidth: 420, margin: "40px auto", padding: 16 }}>
      <h2 style={{ marginTop: 0 }}>Login</h2>

      <form onSubmit={submit} style={{ display: "grid", gap: 10 }}>

        <label>
          Email:
          <input value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: "100%" }} />
        </label>

        <label>
          Password:
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: "100%" }}
          />
        </label>

        {err && <div style={{ color: "crimson" }}>{err}</div>}

        <button className="btn btn-primary" type="submit" disabled={!email || !password}>
          Continue
        </button>
        <div style={{ marginTop: 8, color: "rgba(255,255,255,.7)" }}>
          New student? <Link to="/register">Create an account</Link>
        </div>
      </form>
    </div>
  );
}
