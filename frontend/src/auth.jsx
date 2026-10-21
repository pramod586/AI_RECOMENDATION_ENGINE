
import { useState } from "react";
import "./auth.css";

function Auth({ onLogin, onRegister, loading, error }) {
  const [isLogin, setIsLogin] = useState(true);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();

    if (isLogin) {
      onLogin({ email, password });
    } else {
      onRegister({ full_name: fullName, email, password });
    }
  };

  const switchMode = () => {
    setIsLogin(!isLogin);
    setFullName("");
    setEmail("");
    setPassword("");
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-icon">✦</div>
          <h1>AI Knowledge Assistant</h1>
          <p>Your personal AI-powered knowledge companion</p>
        </div>

        <div className="auth-heading">
          <h2>{isLogin ? "Welcome back" : "Create your account"}</h2>
          <p>
            {isLogin
              ? "Sign in to continue to your workspace."
              : "Register to start using your AI assistant."}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {!isLogin && (
            <div className="auth-field">
              <label htmlFor="fullName">Full name</label>
              <input
                id="fullName"
                type="text"
                placeholder="Enter your full name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                minLength={2}
                maxLength={100}
                required
              />
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="email">Email address</label>
            <input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="auth-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={isLogin ? undefined : 8}
              maxLength={128}
              required
            />
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : isLogin
                ? "Sign in"
                : "Create account"}
          </button>
        </form>

        <div className="auth-switch">
          {isLogin ? "Don't have an account?" : "Already have an account?"}
          <button type="button" onClick={switchMode}>
            {isLogin ? "Sign up" : "Sign in"}
          </button>
        </div>

        <div className="auth-footer">
          Secure authentication powered by your AI Knowledge Assistant
        </div>
      </div>
    </div>
  );
}

export default Auth;