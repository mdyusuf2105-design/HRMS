
import { useEffect, useState } from "react";
import {
  Building2,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ArrowRight,
  ShieldCheck,
  Users,
  CalendarCheck,
} from "lucide-react";
import { loginUser } from "./api/client";
import api from "./api/client";
import Dashboard from "./components/Dashboard";
import "./App.css";

export default function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkingSession, setCheckingSession] = useState(true);
  const [error, setError] = useState("");
  const [user, setUser] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      const token = sessionStorage.getItem("access_token");

      if (!token) {
        if (!cancelled) setCheckingSession(false);
        return;
      }

      try {
        const response = await api.get("/auth/me");
        if (!cancelled) setUser(response.data);
      } catch {
        sessionStorage.removeItem("access_token");
      } finally {
        if (!cancelled) setCheckingSession(false);
      }
    }

    restoreSession();

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await loginUser(username.trim(), password);
      const response = await api.get("/auth/me");
      setUser(response.data);
      setPassword("");
    } catch (err) {
      sessionStorage.removeItem("access_token");

      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Unable to sign in. Please check your credentials and try again."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    sessionStorage.removeItem("access_token");
    setUser(null);
    setPassword("");
    setError("");
  }

  if (checkingSession) {
    return (
      <div className="session-loading">
        <div className="session-loading-mark">H</div>
        <p>Checking your session...</p>
      </div>
    );
  }

  if (user) {
    return <Dashboard user={user} onLogout={handleLogout} />;
  }

  return (
    <main className="login-layout">
      <section className="login-brand-panel">
        <div className="login-brand">
          <div className="login-brand-mark">
            <Building2 size={25} />
          </div>
          <div>
            <strong>HORIZON</strong>
            <span>HUMAN RESOURCES</span>
          </div>
        </div>

        <div className="brand-message">
          <div className="brand-eyebrow">HUMAN RESOURCE MANAGEMENT</div>
          <h1>
            Better workforce
            <br />
            management starts
            <br />
            <span>with clarity.</span>
          </h1>
          <p>
            One secure workspace to manage your people, attendance, leave
            requests, and payroll.
          </p>

          <div className="login-feature-list">
            <div>
              <span className="feature-icon">
                <Users size={18} />
              </span>
              <div>
                <strong>Employee management</strong>
                <span>Keep workforce information organized.</span>
              </div>
            </div>

            <div>
              <span className="feature-icon">
                <CalendarCheck size={18} />
              </span>
              <div>
                <strong>Attendance and leave</strong>
                <span>Track attendance and leave workflows.</span>
              </div>
            </div>

            <div>
              <span className="feature-icon">
                <ShieldCheck size={18} />
              </span>
              <div>
                <strong>Secure access</strong>
                <span>Authenticate through your HRMS account.</span>
              </div>
            </div>
          </div>
        </div>

        <div className="brand-footer">
          HORIZON HRMS <span>·</span> WORKFORCE MANAGEMENT
        </div>
      </section>

      <section className="login-form-panel">
        <div className="login-form-container">
          <div className="login-mobile-brand">
            <div className="login-brand-mark">
              <Building2 size={22} />
            </div>
            <strong>HORIZON</strong>
          </div>

          <div className="login-heading">
            <span className="form-eyebrow">WELCOME BACK</span>
            <h2>Sign in to your account</h2>
            <p>Enter your credentials to access your workspace.</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="form-field">
              <label htmlFor="username">Email address</label>
              <div className="input-wrapper">
                <Mail size={17} />
                <input
                  id="username"
                  type="email"
                  placeholder="you@company.com"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            <div className="form-field">
              <label htmlFor="password">Password</label>
              <div className="input-wrapper">
                <LockKeyhole size={17} />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((current) => !current)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="login-error" role="alert">
                {error}
              </div>
            )}

            <button
              className="login-submit"
              type="submit"
              disabled={loading}
            >
              {loading ? "Signing in..." : "Sign in"}
              {!loading && <ArrowRight size={17} />}
            </button>
          </form>

          <div className="login-security-note">
            <ShieldCheck size={15} />
            <span>Authentication is verified by the HRMS backend.</span>
          </div>

          <div className="login-copyright">
            © 2026 Horizon HRMS. All rights reserved.
          </div>
        </div>
      </section>
    </main>
  );
}
