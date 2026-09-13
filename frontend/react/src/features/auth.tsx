import { Brand } from "../components/Brand";
import { ResourceArtwork } from "../components/resources";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
  type FormEvent,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  Navigate,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router";
import { ArrowRight } from "lucide-react";
import {
  api,
  send,
  setCsrf,
  safeReturn,
  humanError,
  ApiError,
  type Session,
} from "../lib/api/client";
import { ErrorPanel, Loading } from "../components/ui";
import s from "./pages.module.css";
import { claimDrafts, clearDrafts } from "./drafts";
type AuthState = {
  user: Session | null;
  loading: boolean;
  error: unknown;
  refresh: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};
const Auth = createContext<AuthState>(null!);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Session | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState<unknown>(null);
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
  useEffect(() => {
    void refresh();
    const expire = () => {
      setUser(null);
      setCsrf("");
      cache.clear();
    };
    window.addEventListener("session-expired", expire);
    return () => window.removeEventListener("session-expired", expire);
  }, [cache, refresh]);
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
    <Auth.Provider value={{ user, loading, error, refresh, login, logout }}>
      {children}
    </Auth.Provider>
  );
}
export const useAuth = () => useContext(Auth);
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
  const { login, user, loading } = useAuth(),
    navigate = useNavigate();
  const [params] = useSearchParams();
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const target = safeReturn(params.get("returnTo"));
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
        <p className={s.brandTagline}>Share what you learn.</p>
      </div>
      <section>
        <h1>
          Make room for
          <br />
          your next idea.
        </h1>
        <p className="muted">
          A shared library. A clear next step.
          <br />A place to keep growing.
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
