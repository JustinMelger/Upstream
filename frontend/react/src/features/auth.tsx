import { useQueryClient } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import {
  createContext,
  type FormEvent,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import {
  Navigate,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router";

import { Brand } from "../components/Brand";
import { ResourceArtwork } from "../components/resources";
import { ErrorPanel, Loading } from "../components/ui";
import {
  api,
  ApiError,
  humanError,
  safeReturn,
  send,
  type Session,
  setCsrf,
} from "../lib/api/client";
import { claimDrafts, clearDrafts } from "./drafts";
import s from "./pages.module.css";

type AuthState = {
  user: Session | null;
  loading: boolean;
  error: unknown;
  refresh: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  expireSession: () => void;
};

const Auth = createContext<AuthState>(null!);

/**
 * Restore the browser session and expose sign-in and sign-out actions.
 *
 * Session expiry clears cached server data but preserves recoverable drafts;
 * explicit sign-out clears drafts as well. Session credentials stay in cookies.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const cache = useQueryClient();
  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const session = await api<Session>("/auth/browser/session");
      claimDrafts(session.username);
      setCsrf(session.csrf_token);
      setUser(session);
    } catch (e) {
      setUser(null);
      if (!(e instanceof ApiError && e.status === 401)) setError(e);
    } finally {
      setLoading(false);
    }
  }, []);
  const expireSession = useCallback(() => {
    setUser(null);
    setCsrf("");
    cache.clear();
  }, [cache]);

  useEffect(() => {
    void refresh();

    window.addEventListener("session-expired", expireSession);

    return () => window.removeEventListener("session-expired", expireSession);
  }, [expireSession, refresh]);

  async function login(username: string, password: string) {
    const session = await send<Session>("/auth/browser/login", {
      username,
      password,
    });
    cache.clear();
    claimDrafts(session.username);
    setCsrf(session.csrf_token);
    setUser(session);
  }

  async function logout() {
    await send("/auth/browser/logout");
    clearDrafts();
    setCsrf("");
    setUser(null);
    cache.clear();
  }

  return (
    <Auth.Provider
      value={{ user, loading, error, refresh, login, logout, expireSession }}
    >
      {children}
    </Auth.Provider>
  );
}

/**
 * Read session state and actions from the enclosing AuthProvider.
 */
export const useAuth = () => useContext(Auth);

/**
 * Wait for session restoration before rendering protected content.
 *
 * Session lookup failures offer retry; signed-out users are redirected to login
 * with the current path, query and hash preserved as the return destination.
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading, error, refresh } = useAuth();
  const location = useLocation();
  if (loading) return <Loading />;
  if (error) return <ErrorPanel error={error} retry={() => void refresh()} />;
  if (!user)
    return (
      <Navigate
        to={
          "/login?returnTo=" +
          encodeURIComponent(
            location.pathname + location.search + location.hash,
          )
        }
        replace
      />
    );

  return children;
}

export function Login() {
  const { login, user, loading } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const target = safeReturn(params.get("returnTo"));
  const passwordChanged = params.get("passwordChanged") === "1";

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setBusy(true);
    setError("");

    try {
      await login(String(form.get("username")), String(form.get("password")));
      navigate(target, { replace: true });
    } catch (e) {
      setError(humanError(e));
    } finally {
      setBusy(false);
    }
  }

  if (!loading && user) return <Navigate to={target} replace />;

  return (
    <main className={s.login}>
      <div className={s.loginBrand}>
        <Brand large />
        <p className={s.brandTagline}>
          Turn everyday discoveries into team knowledge.
        </p>
      </div>
      <section>
        <h1>
          Good finds.
          <br />
          Shared knowledge.
        </h1>
        <p className="muted">
          Discover what others find useful and add what helps you.
        </p>
        <div className={s.loginArtwork}>
          <ResourceArtwork type="path" title="Your next idea" eager />
        </div>
      </section>
      <form className={s.loginForm} onSubmit={submit}>
        <h2>Welcome back</h2>
        <p className="muted">Sign in to your learning workspace.</p>
        <label>
          Username
          <input name="username" autoComplete="username" required autoFocus />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            required
          />
        </label>
        {passwordChanged && (
          <p role="status" className="muted">
            Password changed. Sign in again with your new password.
          </p>
        )}
        {error && (
          <p role="alert" className={s.error}>
            {error}
          </p>
        )}
        <button aria-busy={busy || loading} disabled={busy || loading}>
          {busy ? "Signing in…" : "Sign in"}
          <ArrowRight size={17} />
        </button>
        <small className="muted">
          Need an account? Contact your administrator.
        </small>
      </form>
    </main>
  );
}
