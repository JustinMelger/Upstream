import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Activity as ActivityIcon,
  BookOpen,
  Compass,
  LogOut,
  Menu,
  Plus,
  Shield,
  User,
  X,
} from "lucide-react";
import { Dialog, DropdownMenu } from "radix-ui";
import { useState } from "react";
import {
  BrowserRouter,
  Link,
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
  useLocation,
} from "react-router";

import { Brand } from "../components/Brand";
import { Empty } from "../components/ui";
import uiStyles from "../components/ui.module.css";
import { ActivityPage } from "../features/activity";
import { Admin } from "../features/admin";
import { AuthProvider, Login, RequireAuth, useAuth } from "../features/auth";
import {
  CourseFeedback,
  CourseJourneyProvider,
} from "../features/course-journey";
import { Detail } from "../features/detail";
import { Explore } from "../features/explore";
import { Learning } from "../features/learning";
import p from "../features/pages.module.css";
import { Profile } from "../features/profile";
import { Share } from "../features/share";
import { humanError } from "../lib/api/client";
import s from "./App.module.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, retry: 1, refetchOnWindowFocus: true },
  },
});

function Navigation({ close }: { close?: () => void }) {
  return (
    <>
      <Link className={s.brand} to="/home" onClick={close}>
        <Brand />
      </Link>
      <nav aria-label="Main navigation">
        {[
          ["/home", "My learning", BookOpen],
          ["/explore", "Explore", Compass],
          ["/activity", "Activity", ActivityIcon],
        ].map(([path, label, Icon]) => {
          const Glyph = Icon as typeof BookOpen;

          return (
            <NavLink key={String(path)} to={String(path)} onClick={close}>
              <Glyph size={18} />
              {String(label)}
            </NavLink>
          );
        })}
      </nav>
    </>
  );
}

function Shell() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");

  return (
    <div className={s.shell}>
      <a className={s.skip} href="#main">
        Skip to content
      </a>
      <div className={s.main}>
        <header className={s.utility}>
          <Dialog.Root open={open} onOpenChange={setOpen}>
            <Dialog.Trigger
              className={s.mobileMenu}
              aria-label="Open navigation"
            >
              <Menu size={20} />
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className={uiStyles.overlay} />
              <Dialog.Content className={s.drawer}>
                <Dialog.Title className={s.srOnly}>Navigation</Dialog.Title>
                <Dialog.Description className={s.srOnly}>
                  Your learning workspace
                </Dialog.Description>
                <Navigation close={() => setOpen(false)} />
                <Dialog.Close
                  className={uiStyles.close}
                  aria-label="Close navigation"
                >
                  <X size={18} />
                </Dialog.Close>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
          <div className={s.desktopNav}>
            <Navigation />
          </div>
          <Link to="/home" className={s.mobileBrand} aria-label="Upstream home">
            <Brand wordmark={false} />
          </Link>
          <div className={s.utilityActions}>
            <DropdownMenu.Root>
              <DropdownMenu.Trigger>
                <Plus size={17} />
                Share
              </DropdownMenu.Trigger>
              <DropdownMenu.Portal>
                <DropdownMenu.Content className={p.menu} sideOffset={8}>
                  <DropdownMenu.Item asChild>
                    <Link to="/share/item">Learning item</Link>
                  </DropdownMenu.Item>
                  <DropdownMenu.Item asChild>
                    <Link to="/share/path">Learning path</Link>
                  </DropdownMenu.Item>
                </DropdownMenu.Content>
              </DropdownMenu.Portal>
            </DropdownMenu.Root>
            <DropdownMenu.Root>
              <DropdownMenu.Trigger
                className={s.avatar}
                aria-label="Account menu"
              >
                {user?.username.slice(0, 2).toUpperCase()}
              </DropdownMenu.Trigger>
              <DropdownMenu.Portal>
                <DropdownMenu.Content className={p.menu} sideOffset={8}>
                  <DropdownMenu.Label>{user?.username}</DropdownMenu.Label>
                  <DropdownMenu.Item asChild>
                    <Link to="/profile">
                      <User size={16} />
                      Profile
                    </Link>
                  </DropdownMenu.Item>
                  {user?.role === "admin" && (
                    <DropdownMenu.Item asChild>
                      <Link to="/admin/users">
                        <Shield size={16} />
                        Admin
                      </Link>
                    </DropdownMenu.Item>
                  )}
                  <DropdownMenu.Item
                    onSelect={() => {
                      void logout().catch((e) => setError(humanError(e)));
                    }}
                  >
                    <LogOut size={16} />
                    Sign out
                  </DropdownMenu.Item>
                </DropdownMenu.Content>
              </DropdownMenu.Portal>
            </DropdownMenu.Root>
          </div>
        </header>
        <main id="main" className={s.canvas} key={location.pathname}>
          {error && <p role="alert">{error}</p>}
          <CourseFeedback />
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              element={
                <RequireAuth>
                  <CourseJourneyProvider>
                    <Shell />
                  </CourseJourneyProvider>
                </RequireAuth>
              }
            >
              <Route index element={<Navigate to="/home" replace />} />
              <Route path="home" element={<Learning />} />
              <Route path="explore" element={<Explore />} />
              <Route path="explore/:kind/:id" element={<Detail />} />
              <Route path="share/:kind" element={<Share />} />
              <Route path="activity" element={<ActivityPage />} />
              <Route
                path="teams"
                element={<Navigate to="/activity?retired=teams" replace />}
              />
              <Route path="profile" element={<Profile />} />
              <Route
                path="profile/stats"
                element={<Navigate to="/activity?view=stats" replace />}
              />
              <Route path="admin/users" element={<Admin />} />
              <Route
                path="*"
                element={
                  <Empty title="This page isn’t here.">
                    Return to your shared library to find your next idea.
                  </Empty>
                }
              />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
