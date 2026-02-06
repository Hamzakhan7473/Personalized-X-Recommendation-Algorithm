"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login } from "@/lib/api";

export default function LoginPage() {
  const [handle, setHandle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!handle.trim()) {
      setError("Enter your handle");
      return;
    }
    setLoading(true);
    try {
      const { user, session_id } = await login(handle.trim());
      if (typeof window !== "undefined") {
        localStorage.setItem("session_id", session_id);
        localStorage.setItem("user", JSON.stringify(user));
      }
      router.push("/");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container" style={{ maxWidth: "400px", marginTop: "3rem" }}>
      <h1 style={{ marginBottom: "0.5rem" }}>Sign in</h1>
      <p style={{ color: "#71767b", marginBottom: "1.5rem" }}>
        Enter your handle to use the feed. Seed users: <strong>me</strong>, <strong>alice_dev</strong>, <strong>bob_trades</strong>, <strong>carol_news</strong>, <strong>dave_memes</strong>, <strong>eve_founder</strong>.
      </p>
      <form onSubmit={onSubmit} className="card">
        <label htmlFor="handle" style={{ display: "block", marginBottom: "0.5rem", fontSize: "0.9rem" }}>
          Handle (without @)
        </label>
        <input
          id="handle"
          type="text"
          value={handle}
          onChange={(e) => setHandle(e.target.value)}
          placeholder="me"
          autoComplete="username"
          style={{
            width: "100%",
            padding: "0.75rem",
            borderRadius: "8px",
            border: "1px solid #2f3336",
            background: "#0a0a0a",
            color: "#e7e9ea",
            fontSize: "1rem",
            marginBottom: "1rem",
          }}
        />
        {error && (
          <p style={{ color: "#f4212e", fontSize: "0.9rem", marginBottom: "1rem" }}>{error}</p>
        )}
        <button type="submit" disabled={loading} style={{ width: "100%" }}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p style={{ marginTop: "1rem", fontSize: "0.9rem", color: "#71767b" }}>
        No account? Use any seed handle above to try the app.
      </p>
    </div>
  );
}
