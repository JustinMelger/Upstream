from __future__ import annotations


"""Global theme customization for the NiceGUI frontend.

NiceGUI uses Quasar components. Global CSS must be registered with
`shared=True` when using `@ui.page` routes so it applies across all pages.
"""

from nicegui import ui


def apply_theme() -> None:
    """Apply a global design-token based theme for the NiceGUI app."""
    ui.add_head_html(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
        """,
        shared=True,
    )

    ui.add_css(
        """
        :root {
          --lp-font-display: "Space Grotesk", "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
          --lp-font-body: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
          --lp-font-mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;

          --lp-type-xs: 0.78rem;
          --lp-type-sm: 0.9rem;
          --lp-type-md: 1.02rem;
          --lp-type-lg: 1.28rem;
          --lp-type-xl: clamp(1.46rem, 2vw, 1.82rem);

          --lp-space-1: 4px;
          --lp-space-2: 8px;
          --lp-space-3: 12px;
          --lp-space-4: 16px;
          --lp-space-5: 20px;
          --lp-space-6: 24px;
          --lp-space-8: 32px;

          --lp-radius-sm: 10px;
          --lp-radius-md: 14px;
          --lp-radius-lg: 18px;
          --lp-radius-pill: 999px;

          --lp-bg0: #0b1220;
          --lp-bg1: #101a2c;
          --lp-bg2: #16243a;
          --lp-surface-1: rgba(255, 255, 255, 0.032);
          --lp-surface-2: rgba(255, 255, 255, 0.052);
          --lp-surface-3: rgba(255, 255, 255, 0.082);
          --lp-surface-elevated: rgba(16, 25, 40, 0.9);
          --lp-border-soft: rgba(148, 163, 184, 0.2);
          --lp-border-strong: rgba(186, 204, 227, 0.3);
          --lp-text: rgba(241, 245, 249, 0.96);
          --lp-muted: rgba(220, 225, 235, 0.8);

          --lp-primary: #4f98d4;
          --lp-primary-strong: #74b0e4;
          --lp-success: #34d399;
          --lp-warning: #fbbf24;
          --lp-danger: #fb7185;

          --lp-shadow-sm: 0 8px 20px rgba(0, 0, 0, 0.24);
          --lp-shadow-md: 0 16px 40px rgba(0, 0, 0, 0.34);
          --lp-shadow-lg: 0 24px 60px rgba(0, 0, 0, 0.56);

          --lp-focus-ring: 0 0 0 3px rgba(124, 192, 251, 0.35);

          --lp-max-content: 1320px;
          --lp-page-pad-x: 40px;
          --lp-rail-width: 296px;
        }

        html, body {
          font-family: var(--lp-font-body);
          background:
            radial-gradient(1100px 680px at 18% 6%, rgba(116, 176, 228, 0.1), transparent 62%),
            radial-gradient(860px 520px at 86% 18%, rgba(45, 175, 150, 0.08), transparent 58%),
            radial-gradient(980px 680px at 62% 96%, rgba(232, 179, 87, 0.06), transparent 62%),
            linear-gradient(180deg, var(--lp-bg0), var(--lp-bg1) 54%, var(--lp-bg2));
          color: var(--lp-text);
          letter-spacing: 0.01em;
          line-height: 1.45;
        }

        html {
          background-color: var(--lp-bg0);
          min-height: 100%;
          scroll-behavior: smooth;
        }

        body {
          min-height: 100vh;
        }

        a { color: var(--lp-primary-strong); }
        a:hover { text-decoration: underline; }

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
            radial-gradient(900px 520px at 18% 14%, rgba(88, 166, 232, 0.26), transparent 58%),
            radial-gradient(820px 520px at 86% 18%, rgba(52, 211, 153, 0.18), transparent 55%),
            radial-gradient(900px 720px at 60% 96%, rgba(251, 191, 36, 0.12), transparent 58%);
          animation: lp-login-drift 18s ease-in-out infinite;
          opacity: 1;
        }

        .lp-brand {
          font-family: var(--lp-font-display);
          letter-spacing: 0.02em;
        }

        .lp-header {
          background: rgba(12, 20, 33, 0.66) !important;
          border-bottom: 1px solid var(--lp-border-soft);
          backdrop-filter: blur(12px);
        }

        .lp-header-inner {
          width: min(var(--lp-max-content), calc(100vw - var(--lp-page-pad-x)));
          margin: 0 auto;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--lp-space-3) 0;
          gap: var(--lp-space-3);
        }

        .lp-header-inner .text-lg {
          font-family: var(--lp-font-display);
          font-weight: 700;
          font-size: var(--lp-type-lg);
          letter-spacing: 0.02em;
        }

        .lp-container {
          width: min(var(--lp-max-content), calc(100vw - var(--lp-page-pad-x)));
          margin: var(--lp-space-5) auto 72px;
          gap: var(--lp-space-4);
        }

        .lp-topbar {
          width: 100%;
          display: flex;
          align-items: center;
          gap: var(--lp-space-4);
        }

        .lp-topbar-meta {
          color: var(--lp-text);
          font-size: var(--lp-type-sm);
          font-weight: 600;
          letter-spacing: 0.03em;
          white-space: nowrap;
          opacity: 0.9;
        }

        .lp-topbar-count {
          opacity: 0.78;
          font-weight: 500;
        }

        .lp-topbar-group {
          padding-inline: 6px;
        }

        .lp-topbar-group--secondary {
          opacity: 0.92;
        }

        .lp-topbar-group:last-child {
          padding-left: 10px;
        }

        .lp-topbar-group-label {
          font-size: var(--lp-type-xs);
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: var(--lp-muted);
          font-weight: 700;
          opacity: 0.82;
        }

        .lp-topbar-secondary-control {
          opacity: 0.94;
        }

        .lp-topbar-share {
          opacity: 0.94;
          letter-spacing: 0.02em;
        }

        .lp-topbar-meta--quiet {
          opacity: 0.68;
        }

        .lp-sticky-controls {
          position: sticky;
          top: 74px;
          z-index: 6;
          padding: 12px 14px;
          margin: -12px -14px 6px;
          background: linear-gradient(180deg, rgba(16, 25, 40, 0.9), rgba(15, 24, 39, 0.78));
          border: 1px solid rgba(186, 204, 227, 0.12);
          border-radius: 20px;
          backdrop-filter: blur(10px);
          box-shadow: var(--lp-shadow-sm);
        }

        .lp-split {
          display: flex;
          gap: var(--lp-space-6);
          align-items: flex-start;
          width: 100%;
        }

        .lp-rail {
          width: var(--lp-rail-width);
          flex: 0 0 var(--lp-rail-width);
          position: sticky;
          top: 94px;
          background: rgba(15, 24, 39, 0.58);
          border: 1px solid rgba(186, 204, 227, 0.1);
          border-radius: 22px;
          backdrop-filter: blur(12px);
          box-shadow: 0 14px 34px rgba(0, 0, 0, 0.18);
        }

        .lp-rail-content {
          padding: var(--lp-space-5);
          display: flex;
          flex-direction: column;
          gap: var(--lp-space-4);
        }

        .lp-rail--bar {
          border: none;
          border-right: 1px solid var(--lp-border-soft);
          border-radius: 0;
          box-shadow: none;
          background: rgba(15, 24, 39, 0.58);
          position: sticky;
          height: calc(100vh - 94px);
          overflow: auto;
        }

        .lp-rail--bar::before {
          content: "";
          position: absolute;
          top: 0;
          bottom: 0;
          left: -100vw;
          width: 100vw;
          background: rgba(15, 24, 39, 0.58);
          border-right: 1px solid var(--lp-border-soft);
          backdrop-filter: blur(12px);
          pointer-events: none;
        }

        .lp-main {
          flex: 1;
          min-width: 0;
          max-width: none;
        }

        .lp-courses-toolbar-controls {
          display: inline-flex;
          align-items: center;
          gap: var(--lp-space-2);
          padding-left: 10px;
          border-left: 1px solid rgba(186, 204, 227, 0.08);
        }

        .lp-courses-toolbar .lp-courses-toolbar-controls:first-of-type {
          margin-left: auto;
        }

        .lp-courses-search {
          min-width: min(520px, 100%);
        }

        .lp-filters-head {
          padding-bottom: var(--lp-space-2);
          margin-bottom: var(--lp-space-1);
          border-bottom: 1px solid rgba(186, 204, 227, 0.06);
        }

        .lp-filters-tip {
          margin-top: -2px;
          margin-bottom: var(--lp-space-1);
          opacity: 0.78;
        }

        @media (max-width: 1280px) {
          :root {
            --lp-page-pad-x: 28px;
            --lp-rail-width: 276px;
          }
        }

        @media (max-width: 1080px) {
          :root {
            --lp-page-pad-x: 24px;
          }
          .lp-split {
            flex-direction: column;
            gap: var(--lp-space-4);
          }
          .lp-rail {
            width: 100%;
            flex: 1 1 auto;
            position: static;
            top: auto;
          }
          .lp-rail--bar {
            border: 1px solid var(--lp-border-soft);
            border-radius: var(--lp-radius-lg);
            height: auto;
          }
          .lp-rail--bar::before {
            display: none;
          }
          .lp-main {
            max-width: 100%;
          }
          .lp-course-card-main {
            flex-direction: column-reverse;
          }
          .lp-course-media-slot {
            width: 100%;
            margin-left: 0;
            padding-right: 0;
            padding-top: 0;
            justify-content: flex-start;
          }
          .lp-course-thumb--side {
            width: min(100%, 360px);
          }
        }

        @media (max-width: 640px) {
          :root {
            --lp-page-pad-x: 18px;
          }
          .lp-header-inner {
            flex-wrap: wrap;
          }
          .lp-topbar {
            flex-wrap: wrap;
            align-items: stretch;
            gap: var(--lp-space-3);
          }
          .lp-courses-toolbar-controls {
            flex-wrap: wrap;
            padding-inline: 0;
            border-left: none;
          }
          .lp-courses-search {
            min-width: 100%;
          }
          .lp-sticky-controls {
            position: static;
            top: auto;
            margin: 0;
            padding: 0;
            border: none;
            border-radius: 0;
            background: transparent;
            backdrop-filter: none;
          }
          .lp-card-title {
            font-size: 1.08rem;
          }
          .lp-card-body {
            font-size: 0.98rem;
          }
        }

        .lp-card {
          background: var(--lp-surface-1) !important;
          border: 1px solid rgba(186, 204, 227, 0.14);
          border-radius: 22px;
          box-shadow: var(--lp-shadow-sm);
        }

        .lp-card-title {
          font-family: var(--lp-font-display);
          font-size: clamp(1.12rem, 1.28vw, 1.4rem);
          line-height: 1.2;
          font-weight: 600;
          letter-spacing: 0.01em;
          margin-bottom: 4px;
        }

        .lp-card-subtitle {
          font-size: var(--lp-type-xs);
          font-weight: 500;
          letter-spacing: 0.02em;
          opacity: 0.82;
        }

        .lp-course-thumb {
          width: min(100%, 276px);
          display: block;
          aspect-ratio: 16 / 9;
          object-fit: cover;
          border-radius: var(--lp-radius-md);
          border: 1px solid rgba(186, 204, 227, 0.28);
          box-shadow: var(--lp-shadow-sm);
          margin-bottom: 10px;
        }

        .lp-course-card-main {
          display: flex;
          flex-wrap: nowrap;
          align-items: flex-start;
          justify-content: space-between;
          gap: 18px;
          width: 100%;
        }

        .lp-course-card-content {
          min-width: 0;
          flex: 1 1 auto;
        }

        .lp-course-card-stack {
          gap: var(--lp-space-3);
          padding-right: var(--lp-space-2);
          padding-top: 2px;
          padding-bottom: 2px;
        }

        .lp-course-media-slot {
          width: 276px;
          margin-left: auto;
          padding-right: 44px;
          padding-top: 52px;
          flex: 0 0 auto;
          display: flex;
          justify-content: flex-end;
          align-items: flex-start;
        }

        .lp-course-thumb--side {
          margin-left: 0;
          margin-right: 0;
          margin-top: 0;
          margin-bottom: 0;
          width: 276px;
          flex: 0 0 auto;
        }

        .lp-course-thumb-placeholder {
          padding: 6px 10px;
          border-radius: var(--lp-radius-pill);
          border: 1px dashed rgba(186, 204, 227, 0.28);
          background: linear-gradient(135deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.01));
          display: flex;
          align-items: center;
          justify-content: center;
          flex-direction: row;
          gap: 5px;
        }

        .lp-course-thumb-placeholder-icon {
          font-size: 0.92rem;
          color: rgba(186, 204, 227, 0.62);
        }

        .lp-course-thumb-placeholder-label {
          font-size: 0.78rem;
          color: rgba(186, 204, 227, 0.72);
          letter-spacing: 0.02em;
        }

        .lp-card-body {
          margin-top: 0;
          font-size: var(--lp-type-md);
          line-height: 1.58;
          max-width: 64ch;
          color: var(--lp-muted);
        }

        .lp-course-summary {
          opacity: 0.95;
        }

        .lp-card-taxonomy {
          margin-top: -2px;
        }

        .lp-card-actions {
          padding-top: 0;
          margin-top: 6px;
          gap: 10px !important;
          opacity: 0.98;
        }

        .lp-social-strip {
          margin-top: 3px;
          margin-bottom: 0;
        }

        .lp-card--hover {
          transition: transform 160ms ease, box-shadow 180ms ease, border-color 180ms ease, background 180ms ease;
        }

        .lp-card--hover:hover {
          transform: translateY(-2px);
          box-shadow: var(--lp-shadow-md);
          border-color: var(--lp-border-strong);
          background: var(--lp-surface-2) !important;
        }

        .lp-course-card,
        .lp-accent-card {
          position: relative;
          overflow: hidden;
        }

        .lp-course-card--surface {
          background:
            radial-gradient(110% 85% at 82% 6%, rgba(116, 176, 228, 0.12), transparent 62%),
            radial-gradient(120% 90% at 8% 100%, rgba(45, 175, 150, 0.075), transparent 68%),
            linear-gradient(140deg, rgba(24, 35, 52, 0.76), rgba(18, 29, 44, 0.64));
          border: 1px solid rgba(186, 204, 227, 0.16);
        }

        .lp-course-card::before,
        .lp-accent-card::before {
          content: "";
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 3px;
          background: rgba(255, 255, 255, 0.12);
        }

        .lp-course-card::after {
          content: "";
          position: absolute;
          inset: 0;
          pointer-events: none;
          background: linear-gradient(120deg, rgba(255, 255, 255, 0.045), transparent 22%, transparent 78%, rgba(255, 255, 255, 0.03));
          opacity: 0.56;
          transition: opacity 180ms ease;
        }

        .lp-course-card:hover::after {
          opacity: 0.72;
        }

        .lp-course-card--interested::before,
        .lp-accent-card--interested::before {
          background: linear-gradient(180deg, rgba(88, 166, 232, 0.92), rgba(88, 166, 232, 0.12));
        }

        .lp-course-card--in_progress::before,
        .lp-accent-card--in_progress::before {
          background: linear-gradient(180deg, rgba(52, 211, 153, 0.92), rgba(52, 211, 153, 0.12));
        }

        .lp-course-card--completed::before,
        .lp-accent-card--completed::before {
          background: linear-gradient(180deg, rgba(163, 230, 53, 0.92), rgba(163, 230, 53, 0.1));
        }

        .lp-accent-card--not_selected::before {
          background: linear-gradient(180deg, rgba(148, 163, 184, 0.62), rgba(148, 163, 184, 0.08));
        }

        .lp-card-topright {
          position: absolute;
          top: var(--lp-space-4);
          right: var(--lp-space-4);
          z-index: 3;
          display: flex;
          align-items: center;
          gap: var(--lp-space-2);
        }

        .lp-card-badge {
          position: absolute;
          top: var(--lp-space-4);
          right: var(--lp-space-4);
          z-index: 2;
        }

        .lp-filter-chip {
          display: inline-flex;
          align-items: center;
          gap: var(--lp-space-2);
          padding: 4px 11px;
          border-radius: var(--lp-radius-pill);
          border: 1px solid rgba(186, 204, 227, 0.18);
          background: rgba(255, 255, 255, 0.06);
          color: var(--lp-text);
          font-size: 12px;
          line-height: 20px;
          width: fit-content;
        }

        .lp-panel {
          background: rgba(255, 255, 255, 0.035) !important;
          border: 1px solid var(--lp-border-soft);
          border-radius: var(--lp-radius-md);
          box-shadow: var(--lp-shadow-sm);
        }

        .lp-panel .q-field__control,
        .lp-panel .q-field__native,
        .lp-panel .q-field__label,
        .lp-panel .q-field__marginal {
          color: var(--lp-text) !important;
        }

        .lp-filter-select .q-field__label {
          color: rgba(226, 234, 244, 0.68) !important;
          font-weight: 500;
        }

        .lp-filter-select .q-field__native {
          color: var(--lp-text) !important;
          font-weight: 600;
        }

        .lp-panel .q-field--outlined .q-field__control:before,
        .lp-panel .q-field--outlined .q-field__control:after {
          border-color: var(--lp-border-soft) !important;
        }

        .lp-nav-active {
          color: var(--lp-primary-strong) !important;
        }

        .lp-chip {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 3px 11px;
          border-radius: var(--lp-radius-pill);
          border: 1px solid var(--lp-border-soft);
          background: var(--lp-surface-2);
          color: var(--lp-text);
          font-size: var(--lp-type-xs);
          line-height: 20px;
          font-weight: 600;
          letter-spacing: 0.02em;
          width: fit-content;
        }

        .lp-chip--muted {
          background: rgba(148, 163, 184, 0.12);
          color: var(--lp-muted);
        }

        .lp-chip--teal {
          border-color: rgba(52, 211, 153, 0.4);
          background: rgba(52, 211, 153, 0.15);
        }

        .lp-chip--sky {
          border-color: rgba(88, 166, 232, 0.4);
          background: rgba(88, 166, 232, 0.15);
        }

        .lp-chip--lime {
          border-color: rgba(163, 230, 53, 0.42);
          background: rgba(163, 230, 53, 0.12);
        }

        .lp-chip--rose {
          border-color: rgba(251, 113, 133, 0.45);
          background: rgba(251, 113, 133, 0.14);
        }

        .lp-meta-chip {
          display: inline-flex;
          align-items: center;
          padding: 2px 10px;
          border-radius: var(--lp-radius-pill);
          border: 1px solid rgba(186, 204, 227, 0.17);
          background: rgba(255, 255, 255, 0.045);
          color: rgba(226, 234, 244, 0.9);
          font-size: var(--lp-type-xs);
          line-height: 20px;
          font-weight: 600;
          width: fit-content;
        }

        .lp-meta-chip--quiet {
          border-color: rgba(186, 204, 227, 0.22);
          background: rgba(255, 255, 255, 0.028);
          color: rgba(226, 234, 244, 0.76);
        }

        .q-card {
          background: var(--lp-surface-1) !important;
          border: 1px solid var(--lp-border-soft);
          border-radius: var(--lp-radius-lg);
        }

        body #q-app,
        body .q-layout,
        body .q-page-container,
        body .q-page {
          background: transparent !important;
          color: var(--lp-text) !important;
        }

        body .q-table__container,
        body .q-table__card,
        body .q-table,
        body .q-table__middle,
        body .q-table__top,
        body .q-table__bottom {
          background: rgba(255, 255, 255, 0.04) !important;
          color: var(--lp-text) !important;
          border-color: var(--lp-border-soft) !important;
        }

        body .q-table__container {
          border: 1px solid var(--lp-border-soft) !important;
          border-radius: var(--lp-radius-lg) !important;
          overflow: hidden;
          box-shadow: var(--lp-shadow-sm);
        }

        body .q-table thead tr th {
          color: var(--lp-muted) !important;
          border-bottom: 1px solid var(--lp-border-soft) !important;
          font-weight: 600;
          letter-spacing: 0.02em;
          background: rgba(0, 0, 0, 0.14) !important;
        }

        body .q-table tbody tr td {
          border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
        }

        body .q-table tbody tr:hover td {
          background: rgba(255, 255, 255, 0.05) !important;
        }

        .q-field--outlined .q-field__control {
          background: rgba(255, 255, 255, 0.04);
          border-radius: var(--lp-radius-sm);
        }

        .q-field--focused .q-field__label {
          color: var(--lp-primary-strong) !important;
        }

        .q-field__native,
        .q-field__prefix,
        .q-field__suffix,
        .q-field__label,
        .q-placeholder {
          color: var(--lp-text) !important;
        }

        .q-field__bottom {
          color: var(--lp-muted) !important;
          font-size: var(--lp-type-xs) !important;
        }

        .q-btn {
          border-radius: var(--lp-radius-sm);
          transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
          font-weight: 600;
          font-size: var(--lp-type-sm);
          letter-spacing: 0.01em;
        }

        .lp-courses-toolbar .q-btn,
        .lp-rail .q-btn,
        .lp-card-actions .q-btn {
          border-radius: var(--lp-radius-pill);
        }

        .q-btn:hover {
          transform: translateY(-1px);
        }

        .q-btn--outline {
          border-color: var(--lp-border-soft) !important;
          background: rgba(255, 255, 255, 0.02) !important;
        }

        .q-btn--outline .q-btn__content,
        .q-btn--outline .q-icon {
          color: var(--lp-text);
        }

        .q-btn--outline:hover {
          border-color: var(--lp-border-strong) !important;
          background: rgba(255, 255, 255, 0.06) !important;
        }

        .q-btn--standard {
          background: linear-gradient(180deg, rgba(88, 166, 232, 0.88), rgba(79, 152, 212, 0.68)) !important;
          color: #f8fbff !important;
        }

        .q-btn--standard:hover {
          box-shadow: 0 8px 20px rgba(88, 166, 232, 0.32);
        }

        :is(button, .q-btn, .q-field__control, .q-item, a, input, textarea, select):focus-visible {
          outline: none !important;
          box-shadow: var(--lp-focus-ring) !important;
        }

        .q-separator {
          background: var(--lp-border-soft);
        }

        body .q-dialog__backdrop {
          background: rgba(0, 0, 0, 0.68) !important;
          backdrop-filter: blur(4px);
        }

        body .q-card.lp-dialog,
        body .q-dialog .q-card.lp-dialog {
          background: rgba(7, 16, 32, 0.94) !important;
          border: 1px solid var(--lp-border-strong) !important;
          box-shadow: var(--lp-shadow-lg) !important;
        }

        body .q-menu,
        body .q-menu .q-list {
          background: rgba(7, 16, 32, 0.98) !important;
          color: var(--lp-text) !important;
          border: 1px solid var(--lp-border-soft);
          border-radius: var(--lp-radius-md);
          box-shadow: var(--lp-shadow-md);
          backdrop-filter: blur(10px);
        }

        body .q-menu .q-item,
        body .q-menu .q-item__label,
        body .q-menu .q-item__section {
          color: var(--lp-text) !important;
        }

        body .q-menu .q-item--active,
        body .q-menu .q-item.q-router-link--active {
          color: var(--lp-primary-strong) !important;
        }

        body .q-menu .q-item:hover {
          background: rgba(255, 255, 255, 0.07) !important;
        }

        .text-gray-600 { color: var(--lp-muted) !important; }

        /* Typography rhythm across common regions. */
        .lp-rail .text-md,
        .lp-panel .text-md {
          font-family: var(--lp-font-display);
          font-size: var(--lp-type-md);
          font-weight: 700;
          letter-spacing: 0.02em;
        }

        .lp-rail .text-xs,
        .lp-panel .text-xs {
          font-size: var(--lp-type-xs);
        }

        .lp-topbar .q-field__native,
        .lp-topbar input {
          font-size: var(--lp-type-md) !important;
        }

        .lp-topbar .q-radio__label {
          font-size: var(--lp-type-sm);
          font-weight: 600;
          color: var(--lp-text) !important;
          letter-spacing: 0.01em;
        }

        .lp-topbar .q-field__native,
        .lp-topbar .q-select__dropdown-icon {
          color: var(--lp-text) !important;
        }

        .lp-topbar-search .q-field__control {
          border-radius: 999px !important;
          background: rgba(255, 255, 255, 0.032) !important;
        }

        .lp-topbar-search .q-field--outlined .q-field__control:before,
        .lp-topbar-search .q-field--outlined .q-field__control:after {
          border-color: rgba(186, 204, 227, 0.24) !important;
          border-width: 1px !important;
        }

        .lp-topbar-search .q-field--focused .q-field__control:after {
          border-color: rgba(124, 192, 251, 0.55) !important;
        }

        .lp-status-select .q-field__control {
          border-radius: 999px !important;
          min-height: 38px !important;
          background: rgba(255, 255, 255, 0.025) !important;
        }

        .lp-status-select .q-field--outlined .q-field__control:before,
        .lp-status-select .q-field--outlined .q-field__control:after {
          border-color: rgba(186, 204, 227, 0.2) !important;
        }

        .lp-rail .q-field--outlined .q-field__control {
          min-height: 42px;
          background: rgba(255, 255, 255, 0.02) !important;
        }

        .lp-rail .q-field__label {
          opacity: 0.82;
        }

        .lp-card--hover {
          animation: lp-card-fade-in 180ms ease both;
        }

        @keyframes lp-card-fade-in {
          from {
            opacity: 0;
            transform: translateY(4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .lp-status-saved {
          min-width: 36px;
          font-size: var(--lp-type-xs);
          color: rgba(163, 230, 53, 0.9);
          font-weight: 600;
          letter-spacing: 0.02em;
        }

        .lp-video-wrap {
          width: min(100%, 640px);
          aspect-ratio: 16 / 9;
          border-radius: var(--lp-radius-md);
          overflow: hidden;
          border: 1px solid rgba(186, 204, 227, 0.25);
          background: rgba(0, 0, 0, 0.24);
          margin-top: 4px;
          margin-bottom: 6px;
        }

        .lp-video-wrap iframe {
          width: 100%;
          height: 100%;
          border: 0;
          display: block;
        }

        .lp-video-wrap > div {
          width: 100%;
          height: 100%;
        }

        body .q-card.lp-dialog .text-xl,
        body .q-dialog .q-card.lp-dialog .text-xl {
          font-family: var(--lp-font-display);
          font-size: var(--lp-type-lg) !important;
          font-weight: 700 !important;
          letter-spacing: 0.015em;
        }

        body .q-card.lp-dialog .text-sm,
        body .q-dialog .q-card.lp-dialog .text-sm {
          font-size: var(--lp-type-sm) !important;
          line-height: 1.45;
        }
        """,
        shared=True,
    )
