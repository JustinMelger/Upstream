from __future__ import annotations


"""Global theme customization for the NiceGUI frontend.

NiceGUI uses Quasar components. Global CSS must be registered with
`shared=True` when using `@ui.page` routes so it applies across all pages.
"""

from nicegui import ui


def apply_theme() -> None:
    """Apply a lightweight, opinionated UI theme for the NiceGUI app."""
    ui.add_head_html(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
        """,
        shared=True,
    )

    ui.add_css(
        """
        :root {
          --lp-bg0: #0b1220;
          --lp-bg1: #0e1b2e;
          --lp-surface: rgba(255, 255, 255, 0.06);
          --lp-surface-2: rgba(255, 255, 255, 0.09);
          --lp-border: rgba(255, 255, 255, 0.10);
          --lp-text: rgba(255, 255, 255, 0.90);
          --lp-muted: rgba(255, 255, 255, 0.65);
          --lp-accent: #2dd4bf;
          --lp-danger: #fb7185;
          --lp-radius: 16px;
        }

        html, body {
          font-family: "IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
          background: radial-gradient(1200px 600px at 15% 10%, rgba(45, 212, 191, 0.18), transparent 55%),
                      radial-gradient(900px 500px at 85% 20%, rgba(56, 189, 248, 0.16), transparent 50%),
                      radial-gradient(900px 700px at 65% 95%, rgba(251, 113, 133, 0.10), transparent 55%),
                      linear-gradient(180deg, var(--lp-bg0), var(--lp-bg1));
          color: var(--lp-text);
        }

        html {
          background-color: var(--lp-bg0);
          min-height: 100%;
        }

        body {
          min-height: 100vh;
        }

        a { color: var(--lp-accent); }
        a:hover { text-decoration: underline; }

        /* Login: dedicated background layer (page-local element). */
        @keyframes lp-login-drift {
          0%   { transform: translate3d(-2%, -2%, 0) scale(1.05); }
          50%  { transform: translate3d(2%, -1%, 0) scale(1.08); }
          100% { transform: translate3d(-1%, 2%, 0) scale(1.06); }
        }

        .lp-login-bg {
          position: fixed;
          inset: 0;
          z-index: -1;
          pointer-events: none;
          background: linear-gradient(180deg, var(--lp-bg0), var(--lp-bg1));
        }

        .lp-login-bg::before {
          content: "";
          position: absolute;
          inset: -20%;
          background:
            radial-gradient(900px 520px at 18% 14%, rgba(45, 212, 191, 0.24), transparent 58%),
            radial-gradient(820px 520px at 86% 18%, rgba(56, 189, 248, 0.20), transparent 55%),
            radial-gradient(900px 720px at 60% 96%, rgba(251, 113, 133, 0.14), transparent 58%);
          animation: lp-login-drift 18s ease-in-out infinite;
          opacity: 1;
        }

        .lp-brand {
          font-family: "IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
          letter-spacing: 0.2px;
        }

        /* Layout */
        .lp-header {
          background: rgba(10, 16, 28, 0.55) !important;
          border-bottom: 1px solid var(--lp-border);
          backdrop-filter: blur(10px);
        }

        .lp-container {
          width: min(1100px, calc(100vw - 32px));
          margin: 20px auto 64px;
          gap: 14px;
        }

        .lp-card {
          background: var(--lp-surface) !important;
          border: 1px solid var(--lp-border);
          border-radius: var(--lp-radius);
          box-shadow: 0 12px 30px rgba(0,0,0,0.35);
        }

        .lp-nav-active {
          color: var(--lp-accent) !important;
        }

        /* Chips */
        .lp-chip {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 2px 10px;
          border-radius: 999px;
          border: 1px solid var(--lp-border);
          background: rgba(255, 255, 255, 0.06);
          color: var(--lp-text);
          font-size: 12px;
          line-height: 20px;
          font-weight: 600;
          letter-spacing: 0.2px;
          width: fit-content;
        }

        .lp-chip--muted {
          background: rgba(255, 255, 255, 0.05);
          color: var(--lp-muted);
        }

        .lp-chip--teal {
          border-color: rgba(45, 212, 191, 0.35);
          background: rgba(45, 212, 191, 0.12);
        }

        .lp-chip--sky {
          border-color: rgba(56, 189, 248, 0.35);
          background: rgba(56, 189, 248, 0.12);
        }

        .lp-chip--lime {
          border-color: rgba(132, 204, 22, 0.35);
          background: rgba(132, 204, 22, 0.10);
        }

        .lp-chip--rose {
          border-color: rgba(251, 113, 133, 0.35);
          background: rgba(251, 113, 133, 0.10);
        }

        .lp-meta-chip {
          display: inline-flex;
          align-items: center;
          padding: 2px 10px;
          border-radius: 999px;
          border: 1px solid rgba(255, 255, 255, 0.10);
          background: rgba(255, 255, 255, 0.04);
          color: var(--lp-muted);
          font-size: 12px;
          line-height: 20px;
          font-weight: 600;
          width: fit-content;
        }

        /* Quasar element tweaks */
        .q-card {
          background: var(--lp-surface) !important;
          border: 1px solid var(--lp-border);
          border-radius: var(--lp-radius);
        }

        /* Ensure no white "page" shows while scrolling (Quasar layout containers). */
        body #q-app,
        body .q-layout,
        body .q-page-container,
        body .q-page {
          background: transparent !important;
          color: var(--lp-text) !important;
        }

        /* Tables */
        body .q-table__container,
        body .q-table__card,
        body .q-table,
        body .q-table__middle,
        body .q-table__top,
        body .q-table__bottom {
          background: rgba(255, 255, 255, 0.04) !important;
          color: var(--lp-text) !important;
          border-color: var(--lp-border) !important;
        }

        body .q-table__container {
          border: 1px solid var(--lp-border) !important;
          border-radius: var(--lp-radius) !important;
          overflow: hidden;
          box-shadow: 0 12px 30px rgba(0,0,0,0.25);
        }

        body .q-table thead tr th {
          color: var(--lp-muted) !important;
          border-bottom: 1px solid var(--lp-border) !important;
          font-weight: 600;
          letter-spacing: 0.2px;
          background: rgba(0, 0, 0, 0.12) !important;
        }

        body .q-table tbody tr td {
          border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
        }

        body .q-table tbody tr:hover td {
          background: rgba(255, 255, 255, 0.04) !important;
        }

        .q-field--outlined .q-field__control {
          background: rgba(255, 255, 255, 0.04);
          border-radius: 12px;
        }

        .q-btn--outline .q-btn__content,
        .q-btn--outline .q-icon {
          color: var(--lp-text);
        }

        .q-btn {
          border-radius: 12px;
        }

        .q-btn--standard {
          background: rgba(45, 212, 191, 0.18) !important;
        }

        .q-separator {
          background: var(--lp-border);
        }

        /* Dialogs: darker backdrop + more opaque cards for readability. */
        body .q-dialog__backdrop {
          background: rgba(0, 0, 0, 0.65) !important;
          backdrop-filter: blur(3px);
        }

        body .q-card.lp-dialog,
        body .q-dialog .q-card.lp-dialog {
          background: rgba(10, 16, 28, 0.92) !important;
          border: 1px solid rgba(255, 255, 255, 0.14) !important;
          box-shadow: 0 22px 60px rgba(0,0,0,0.65) !important;
        }

        /* Dropdowns / menus (Quasar) */
        body .q-menu,
        body .q-menu .q-list {
          background: rgba(10, 16, 28, 0.98) !important;
          color: var(--lp-text) !important;
          border: 1px solid var(--lp-border);
          border-radius: 14px;
          box-shadow: 0 18px 45px rgba(0,0,0,0.55);
          backdrop-filter: blur(10px);
        }

        body .q-menu .q-item,
        body .q-menu .q-item__label,
        body .q-menu .q-item__section {
          color: var(--lp-text) !important;
        }

        body .q-menu .q-item--active,
        body .q-menu .q-item.q-router-link--active {
          color: var(--lp-accent) !important;
        }

        body .q-menu .q-item:hover {
          background: rgba(255, 255, 255, 0.06) !important;
        }

        .q-field__native,
        .q-field__prefix,
        .q-field__suffix,
        .q-field__label,
        .q-placeholder {
          color: var(--lp-text) !important;
        }

        .q-field--focused .q-field__label {
          color: var(--lp-accent) !important;
        }

        .q-field__bottom {
          color: var(--lp-muted) !important;
        }

        .text-gray-600 { color: var(--lp-muted) !important; }
        """,
        shared=True,
    )
