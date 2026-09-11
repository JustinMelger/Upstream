import { useState, useRef, type FormEvent } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router";
import { Dialog, DropdownMenu } from "radix-ui";
import { Plus, ChevronDown, X } from "lucide-react";
import { useAuth } from "./auth";
import { api, send, humanError } from "../lib/api/client";
import { Empty, ErrorPanel, Heading, Loading } from "../components/ui";
import { Contributor } from "../components/resources";
import s from "./pages.module.css";
import d from "./supporting.module.css";
type UserRow = { username: string; role: string; disabled: boolean };
export function Admin() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const [adding, setAdding] = useState(false);
  const addButton = useRef<HTMLButtonElement>(null);
  const query = useQuery({
    queryKey: ["users"],
    queryFn: () => api<UserRow[]>("/auth/users"),
    enabled: user?.role === "admin",
  });
  if (user?.role !== "admin")
    return (
      <Empty title="Administrator access required.">
        Your personal learning workspace is available from the navigation.
      </Empty>
    );
  const search = params.get("q") || "";
  const rows = (query.data || [])
    .filter((row) =>
      row.username.toLowerCase().includes(search.trim().toLowerCase()),
    )
    .sort((a, b) => a.username.localeCompare(b.username));
  return (
    <>
      <Heading
        title="User administration"
        action={
          <button ref={addButton} onClick={() => setAdding(true)}>
            <Plus size={16} />
            Add member
          </button>
        }
      >
        Manage access to your learning library.
      </Heading>
      <div className={d.adminTools}>
        <label>
          Search usernames
          <input
            id="account-search"
            value={search}
            onChange={(e) => {
              const next = new URLSearchParams(params);
              if (e.target.value) next.set("q", e.target.value);
              else next.delete("q");
              setParams(next, { replace: true });
            }}
            placeholder="Search usernames"
          />
        </label>
        <span className="muted" role="status">
          {rows.length} {rows.length === 1 ? "account" : "accounts"}
        </span>
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorPanel error={query.error} retry={() => void query.refetch()} />
      ) : rows.length ? (
        <>
          <div className={d.accounts}>
            <table>
              <caption>Workspace accounts</caption>
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.username}>
                    <td>
                      <Contributor username={row.username} prefix="" />
                    </td>
                    <td>
                      <span className={s.badge}>
                        {row.role === "admin" ? "Administrator" : "Member"}
                      </span>
                    </td>
                    <td>
                      <AccountStatus disabled={row.disabled} />
                    </td>
                    <td>
                      <AccountActions
                        row={row}
                        currentUsername={user.username}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className={d.accountCards}>
            {rows.map((row) => (
              <article className={d.accountCard} key={row.username}>
                <div>
                  <Contributor username={row.username} prefix="" />
                  <span className={s.badge}>
                    {row.role === "admin" ? "Administrator" : "Member"}
                  </span>
                  <AccountStatus disabled={row.disabled} />
                </div>
                <AccountActions row={row} currentUsername={user.username} />
              </article>
            ))}
          </div>
        </>
      ) : (
        <Empty
          title={search ? "No matching accounts." : "No accounts to display."}
          action={false}
        >
          {search
            ? "Try another username or clear your search."
            : "Add a member to give them access."}
        </Empty>
      )}
      <AccountDialog
        mode="create"
        open={adding}
        onClose={() => setAdding(false)}
        returnFocus={() => addButton.current?.focus()}
      />
    </>
  );
}
function AccountStatus({ disabled }: { disabled: boolean }) {
  return (
    <span className={d.accountStatus} data-active={!disabled}>
      {disabled ? "Disabled" : "Active"}
    </span>
  );
}
function AccountActions({
  row,
  currentUsername,
}: {
  row: UserRow;
  currentUsername: string;
}) {
  const cache = useQueryClient();
  const trigger = useRef<HTMLButtonElement>(null);
  const [dialog, setDialog] = useState<"reset" | "delete" | null>(null);
  const mutation = useMutation({
    mutationFn: () =>
      send("/auth/users/disable", {
        username: row.username,
        disabled: !row.disabled,
      }),
    onSuccess: () => void cache.invalidateQueries({ queryKey: ["users"] }),
  });
  const self = row.username.toLowerCase() === currentUsername.toLowerCase();
  return (
    <div>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild>
          <button
            ref={trigger}
            className="secondary"
            disabled={mutation.isPending}
            aria-label={`Manage ${row.username}`}
          >
            Manage <ChevronDown size={16} />
          </button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            className={s.menu}
            align="end"
            onCloseAutoFocus={(e) => {
              if (dialog) e.preventDefault();
            }}
          >
            <DropdownMenu.Item
              className={d.menuItem}
              onSelect={() => setDialog("reset")}
            >
              Reset password
            </DropdownMenu.Item>
            <DropdownMenu.Item
              className={d.menuItem}
              disabled={self}
              onSelect={() => mutation.mutate()}
            >
              {row.disabled ? "Enable account" : "Disable account"}
            </DropdownMenu.Item>
            <DropdownMenu.Separator />
            <DropdownMenu.Item
              className={`${d.menuItem} ${d.danger}`}
              disabled={self}
              onSelect={() => setDialog("delete")}
            >
              Delete account
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
      {mutation.isPending && <p role="status">Saving…</p>}
      {mutation.error && (
        <p role="alert" className={d.danger}>
          {humanError(mutation.error)}
        </p>
      )}
      <AccountDialog
        mode={dialog || "reset"}
        username={row.username}
        open={dialog !== null}
        onClose={() => setDialog(null)}
        returnFocus={() => {
          if (trigger.current?.isConnected) trigger.current.focus();
          else document.getElementById("account-search")?.focus();
        }}
      />
    </div>
  );
}
function AccountDialog({
  mode,
  username,
  open,
  onClose,
  returnFocus,
}: {
  mode: "create" | "reset" | "delete";
  username?: string;
  open: boolean;
  onClose: () => void;
  returnFocus: () => void;
}) {
  const cache = useQueryClient();
  const mutation = useMutation({
    mutationFn: (values: Record<string, FormDataEntryValue>) =>
      mode === "delete"
        ? api(`/auth/users/${encodeURIComponent(username!)}`, {
            method: "DELETE",
          })
        : send(
            mode === "create" ? "/auth/users" : "/auth/users/reset",
            mode === "create" ? values : { ...values, username },
          ),
    onSuccess: async () => {
      onClose();
      await cache.invalidateQueries({ queryKey: ["users"] });
      if (mode === "delete")
        requestAnimationFrame(() =>
          document.getElementById("account-search")?.focus(),
        );
    },
  });
  function close() {
    if (!mutation.isPending) {
      onClose();
      mutation.reset();
    }
  }
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    mutation.mutate(Object.fromEntries(new FormData(e.currentTarget)));
  }
  return (
    <Dialog.Root
      open={open}
      onOpenChange={(value) => {
        if (!value) close();
        else mutation.reset();
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className={s.overlay} />
        <Dialog.Content
          className={`${s.dialog} ${d.dialog}`}
          onCloseAutoFocus={(e) => {
            e.preventDefault();
            returnFocus();
          }}
          onEscapeKeyDown={(e) => {
            if (mutation.isPending) e.preventDefault();
          }}
          onPointerDownOutside={(e) => {
            if (mutation.isPending) e.preventDefault();
          }}
        >
          <Dialog.Title>
            {mode === "create"
              ? "Add a member"
              : mode === "reset"
                ? `Reset password for ${username}`
                : `Delete ${username}?`}
          </Dialog.Title>
          <Dialog.Description>
            {mode === "create"
              ? "Create an account to give someone access to the learning library."
              : mode === "reset"
                ? "Existing sessions will be revoked. Share the new password securely."
                : "This permanently removes the account and associated records. Use Disable to retain the account and prevent access."}
          </Dialog.Description>
          <form className={d.accountForm} onSubmit={submit}>
            {mode === "create" && (
              <label>
                Username
                <input name="username" required autoComplete="off" />
              </label>
            )}
            {mode !== "delete" && (
              <label>
                {mode === "create" ? "Initial password" : "New password"}
                <input
                  name="password"
                  type="password"
                  required
                  autoComplete="new-password"
                />
              </label>
            )}
            {mode === "create" && (
              <label>
                Role
                <select name="role">
                  <option value="user">Member</option>
                  <option value="admin">Administrator</option>
                </select>
              </label>
            )}
            {mutation.error && (
              <p role="alert" className={s.error}>
                {humanError(mutation.error)}
              </p>
            )}
            <div className={s.actions}>
              <button
                type="button"
                className="secondary"
                disabled={mutation.isPending}
                onClick={close}
              >
                Cancel
              </button>
              <button
                className={mode === "delete" ? "danger" : ""}
                disabled={mutation.isPending}
                aria-busy={mutation.isPending}
              >
                {mutation.isPending
                  ? "Saving…"
                  : mode === "create"
                    ? "Create account"
                    : mode === "reset"
                      ? "Reset password"
                      : "Delete"}
              </button>
            </div>
          </form>
          <button
            type="button"
            className={s.close}
            aria-label="Close"
            onClick={close}
            disabled={mutation.isPending}
          >
            <X size={18} />
          </button>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
