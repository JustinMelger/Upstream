import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Plus } from "lucide-react";
import { Dialog } from "radix-ui";
import { type FormEvent, useState } from "react";
import { Link } from "react-router";
import { useNavigate } from "react-router";

import { ResourceArtwork, ResourceCard } from "../components/resources";
import { Empty, ErrorPanel, Loading } from "../components/ui";
import uiStyles from "../components/ui.module.css";
import { humanError, send } from "../lib/api/client";
import {
  api,
  type LearningItem,
  type Page,
  type Summary,
} from "../lib/api/client";
import { useAuth } from "./auth";
import s from "./pages.module.css";
import pageStyles from "./profile.module.css";
import d from "./supporting.module.css";

export function Profile() {
  const { user, expireSession } = useAuth();
  const navigate = useNavigate();

  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);
  const summary = useQuery({
    queryKey: ["learning-summary"],
    queryFn: () => api<Summary>("/learning/summary"),
  });
  const contributions = useQuery({
    queryKey: ["learning-items", "contributions", "profile"],
    queryFn: () =>
      api<Page<LearningItem>>(
        "/learning/items?view=contributions&page=1&page_size=3",
      ),
  });

  async function changePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const form = new FormData(event.currentTarget);
    const currentPassword = String(form.get("current_password") || "");
    const newPassword = String(form.get("new_password") || "");
    const confirmation = String(form.get("confirm_password") || "");

    if (!currentPassword.trim()) {
      setPasswordError("Enter your current password.");

      return;
    }

    if (!newPassword.trim()) {
      setPasswordError("Enter a new password.");

      return;
    }

    if (newPassword.length < 12) {
      setPasswordError(
        "Your new password must contain at least 12 characters.",
      );

      return;
    }

    if (newPassword !== confirmation) {
      setPasswordError("The new passwords do not match.");

      return;
    }

    setChangingPassword(true);
    setPasswordError("");

    try {
      await send("/auth/password/change", {
        current_password: currentPassword,
        new_password: newPassword,
      });

      expireSession();
      navigate("/login?passwordChanged=1", { replace: true });
    } catch (error) {
      setPasswordError(humanError(error));
    } finally {
      setChangingPassword(false);
    }
  }

  return (
    <>
      <header className={pageStyles.profileIdentity}>
        <span className={pageStyles.avatar} aria-hidden="true">
          {user?.username.slice(0, 2).toUpperCase()}
        </span>
        <div>
          <div className={pageStyles.identityLine}>
            <h1>{user?.username}</h1>
            <span className={s.badge}>
              {user?.role === "admin" ? "Administrator" : "Member"}
            </span>
          </div>
        </div>
        <div className={pageStyles.profileArtwork}>
          <ResourceArtwork type="course" title="Your learning library" eager />
        </div>
      </header>
      {summary.isPending ? (
        <Loading />
      ) : summary.error ? (
        <ErrorPanel
          error={summary.error}
          retry={() => void summary.refetch()}
        />
      ) : (
        <nav
          className={pageStyles.profileTotals}
          aria-label="Your learning totals"
        >
          <Link to="/home?view=tracked&status=in_progress">
            <strong>{summary.data.in_progress}</strong>
            <span>In progress →</span>
          </Link>
          <Link to="/home?view=tracked&status=completed">
            <strong>{summary.data.completed}</strong>
            <span>Completed →</span>
          </Link>
          <Link to="/home?view=paths">
            <strong>{summary.data.selected_paths}</strong>
            <span>Selected paths →</span>
          </Link>
          <Link to="/activity?view=stats">
            View my stats <ArrowRight size={16} />
          </Link>
        </nav>
      )}
      <section className={d.section}>
        <div className={d.sectionHeading}>
          <div>
            <h2>Security</h2>
            <p className="muted">
              Change your password. You will need to sign in again afterwards.
            </p>
          </div>
          <Dialog.Root
            open={passwordDialogOpen}
            onOpenChange={(open) => {
              setPasswordDialogOpen(open);
              if (!open) setPasswordError("");
            }}
          >
            <Dialog.Trigger asChild>
              <button type="button" className="secondary">
                Change password
              </button>
            </Dialog.Trigger>

            <Dialog.Portal>
              <Dialog.Overlay className={uiStyles.overlay} />
              <Dialog.Content className={uiStyles.dialog}>
                <Dialog.Title>Change password</Dialog.Title>
                <Dialog.Description>
                  You will need to sign in again after changing your password.
                </Dialog.Description>

                <form onSubmit={changePassword}>
                  <label>
                    Current password
                    <input
                      name="current_password"
                      type="password"
                      autoComplete="current-password"
                      required
                    />
                  </label>

                  <label>
                    New password
                    <input
                      name="new_password"
                      type="password"
                      autoComplete="new-password"
                      aria-describedby="new-password-requirements"
                      required
                    />
                  </label>
                  <p id="new-password-requirements" className="muted">
                    Use at least 12 characters.
                  </p>

                  <label>
                    Confirm new password
                    <input
                      name="confirm_password"
                      type="password"
                      autoComplete="new-password"
                      required
                    />
                  </label>

                  {passwordError && (
                    <p role="alert" className={s.error}>
                      {passwordError}
                    </p>
                  )}

                  <div className={uiStyles.actions}>
                    <Dialog.Close
                      className="secondary"
                      disabled={changingPassword}
                    >
                      Cancel
                    </Dialog.Close>
                    <button type="submit" disabled={changingPassword}>
                      {changingPassword
                        ? "Changing password…"
                        : "Change password"}
                    </button>
                  </div>
                </form>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
        </div>
      </section>
      <section className={d.section}>
        <div className={d.sectionHeading}>
          <div>
            <h2>Your contributions</h2>
          </div>
          <div className={uiStyles.actions}>
            <Link className="button" to="/share/item">
              <Plus size={16} />
              Share something
            </Link>
            <Link className={s.textAction} to="/home?view=contributions">
              View all contributions <ArrowRight size={16} />
            </Link>
          </div>
        </div>
        {contributions.isPending ? (
          <Loading />
        ) : contributions.error ? (
          <ErrorPanel
            error={contributions.error}
            retry={() => void contributions.refetch()}
          />
        ) : contributions.data.items.length ? (
          <div className={s.collectionGrid}>
            {contributions.data.items.map((item) => (
              <ResourceCard key={`${item.type}:${item.id}`} item={item} />
            ))}
          </div>
        ) : (
          <Empty title="Your library starts with one good find." action={false}>
            Share a resource that helped you learn. It will appear here for you
            to revisit.
          </Empty>
        )}
      </section>
    </>
  );
}
