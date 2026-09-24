import React, { useState } from "react";
import "../Auth.css";
export default function Login({ onLogin, onShowSignup }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }

    setLoading(true);

    setTimeout(() => {
      setLoading(false);
      onLogin?.({ email });
    }, 700);
  };

  return (
    <div className="auth-page">
      <div className="auth-background">
        <div className="auth-glow auth-glow-one" />
        <div className="auth-glow auth-glow-two" />
      </div>

      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-orb">◈</div>
          <div>
            <h1>LDRP AI</h1>
            <span>Academic Assistant</span>
          </div>
        </div>

        <div className="auth-heading">
          <h2>Welcome Back</h2>
          <p>Sign in to continue to your LDRP AI assistant.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>Email Address</label>

            <div className="auth-input-wrapper">
              <span className="auth-input-icon">✉</span>

              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Password</label>

            <div className="auth-input-wrapper">
              <span className="auth-input-icon">⌑</span>

              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />

              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          <div className="auth-options">
            <label className="remember-me">
              <input type="checkbox" />
              <span>Remember me</span>
            </label>

            <button type="button" className="forgot-password">
              Forgot password?
            </button>
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="auth-submit" disabled={loading}>
            {loading ? (
              <>
                <span className="auth-spinner" />
                Signing in...
              </>
            ) : (
              <>
                Sign In <span>→</span>
              </>
            )}
          </button>
        </form>

        <div className="auth-switch">
          <span>Don't have an account?</span>
          <button type="button" onClick={onShowSignup}>
            Create account
          </button>
        </div>

        <div className="auth-footer">
          <span>Powered by</span>
          <strong>LDRP RAG</strong>
        </div>
      </div>
    </div>
  );
}
