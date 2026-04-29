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

          --lp-bg0: #111a29;
          --lp-bg1: #172232;
          --lp-bg2: #1c283a;
          --lp-surface-1: rgba(255, 255, 255, 0.042);
          --lp-surface-2: rgba(255, 255, 255, 0.062);
          --lp-surface-3: rgba(255, 255, 255, 0.092);
          --lp-surface-elevated: rgba(25, 36, 52, 0.9);
          --lp-border-soft: rgba(148, 163, 184, 0.2);
          --lp-border-strong: rgba(186, 204, 227, 0.3);
          --lp-text: rgba(241, 245, 249, 0.96);
          --lp-muted: rgba(220, 225, 235, 0.8);

          --lp-primary: #4f98d4;
          --lp-primary-strong: #74b0e4;
          --lp-primary-shadow: rgba(88, 166, 232, 0.32);
          --lp-success: #34d399;
          --lp-warning: #fbbf24;
          --lp-danger: #fb7185;
          --lp-page-accent: var(--lp-primary);
          --lp-page-accent-strong: var(--lp-primary-strong);
          --lp-page-accent-soft: rgba(88, 166, 232, 0.16);
          --lp-page-glow-1: rgba(88, 166, 232, 0.08);
          --lp-page-glow-2: rgba(52, 211, 153, 0.05);
          --lp-page-surface: rgba(23, 35, 52, 0.82);
          --lp-section-title: rgba(220, 225, 235, 0.86);

          --lp-shadow-sm: 0 6px 18px rgba(0, 0, 0, 0.14);
          --lp-shadow-md: 0 12px 30px rgba(0, 0, 0, 0.2);
          --lp-shadow-lg: 0 20px 46px rgba(0, 0, 0, 0.34);
          --lp-hover-lift: -2px;
          --lp-hover-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);

          --lp-focus-ring: 0 0 0 3px rgba(124, 192, 251, 0.35);

          --lp-max-content: 1200px;
          --lp-page-pad-x: 40px;
          --lp-rail-width: 296px;
        }

        html, body {
          font-family: var(--lp-font-body);
          background:
            radial-gradient(980px 620px at 18% 6%, rgba(116, 176, 228, 0.05), transparent 64%),
            radial-gradient(820px 460px at 86% 18%, rgba(45, 175, 150, 0.04), transparent 60%),
            linear-gradient(180deg, var(--lp-bg0), var(--lp-bg1) 56%, var(--lp-bg2));
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
            radial-gradient(900px 520px at 18% 14%, rgba(88, 166, 232, 0.14), transparent 60%),
            radial-gradient(820px 520px at 86% 18%, rgba(52, 211, 153, 0.09), transparent 58%),
            radial-gradient(900px 720px at 60% 96%, rgba(251, 191, 36, 0.05), transparent 60%);
          animation: lp-login-drift 18s ease-in-out infinite;
          opacity: 1;
        }

        .lp-brand {
          font-family: var(--lp-font-display);
          letter-spacing: 0.02em;
        }

        .lp-header {
          background: rgba(18, 28, 42, 0.82) !important;
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

        .lp-header-actions .q-btn {
          min-height: 38px !important;
          border-radius: 16px !important;
          letter-spacing: 0.02em;
        }

        .lp-header-menu-btn.q-btn--outline {
          border-color: rgba(116, 176, 228, 0.42) !important;
          background: rgba(20, 31, 46, 0.92) !important;
        }

        .lp-header-menu-btn .q-icon {
          margin-right: 4px;
        }

        .lp-menu-logout-item,
        .lp-menu-logout-item .q-item__label {
          color: rgba(251, 153, 169, 0.92) !important;
          font-weight: 600;
        }

        .lp-menu-logout-item:hover {
          background: rgba(251, 113, 133, 0.12) !important;
        }

        .lp-container {
          width: min(var(--lp-max-content), calc(100vw - var(--lp-page-pad-x)));
          margin: var(--lp-space-5) auto 72px;
          gap: var(--lp-space-4);
        }

        .lp-catalog-scope {
          width: min(var(--lp-max-content), calc(100vw - var(--lp-page-pad-x)));
          margin: var(--lp-space-5) auto 72px;
          gap: var(--lp-space-4);
          position: relative;
          isolation: isolate;
        }

        .lp-catalog-scope::before {
          content: "";
          position: absolute;
          inset: -18px -12px;
          z-index: -1;
          pointer-events: none;
          border-radius: 28px;
          background:
            radial-gradient(780px 420px at 8% 14%, var(--lp-page-glow-1), transparent 62%),
            radial-gradient(700px 360px at 88% 26%, var(--lp-page-glow-2), transparent 66%);
          opacity: 0.68;
        }

        .lp-catalog-scope.lp-catalog--courses {
          --lp-page-accent: #4f98d4;
          --lp-page-accent-strong: #74b0e4;
          --lp-page-accent-soft: rgba(88, 166, 232, 0.26);
          --lp-page-glow-1: rgba(88, 166, 232, 0.18);
          --lp-page-glow-2: rgba(52, 211, 153, 0.1);
          --lp-page-surface: rgba(16, 25, 40, 0.82);
          --lp-primary: #4f98d4;
          --lp-primary-strong: #74b0e4;
          --lp-primary-shadow: rgba(88, 166, 232, 0.32);
          --lp-section-title: rgba(220, 225, 235, 0.9);
        }

        .lp-catalog-scope.lp-catalog--articles {
          --lp-page-accent: #1ba0aa;
          --lp-page-accent-strong: #39c2cb;
          --lp-page-accent-soft: rgba(57, 194, 203, 0.24);
          --lp-page-glow-1: rgba(57, 194, 203, 0.15);
          --lp-page-glow-2: rgba(248, 180, 76, 0.1);
          --lp-page-surface: rgba(14, 25, 37, 0.8);
          --lp-primary: #1ba0aa;
          --lp-primary-strong: #39c2cb;
          --lp-primary-shadow: rgba(57, 194, 203, 0.3);
          --lp-section-title: rgba(217, 236, 239, 0.9);
        }

        .lp-catalog-scope.lp-catalog--paths {
          --lp-page-accent: #2da395;
          --lp-page-accent-strong: #4bc0b2;
          --lp-page-accent-soft: rgba(75, 192, 178, 0.24);
          --lp-page-glow-1: rgba(75, 192, 178, 0.17);
          --lp-page-glow-2: rgba(88, 166, 232, 0.11);
          --lp-page-surface: rgba(14, 27, 34, 0.82);
          --lp-primary: #2da395;
          --lp-primary-strong: #4bc0b2;
          --lp-primary-shadow: rgba(75, 192, 178, 0.3);
          --lp-section-title: rgba(218, 239, 233, 0.9);
        }

        .lp-catalog-scope.lp-catalog--explore {
          --lp-page-accent: #4f98d4;
          --lp-page-accent-strong: #74b0e4;
          --lp-page-accent-soft: rgba(88, 166, 232, 0.24);
          --lp-page-glow-1: rgba(88, 166, 232, 0.14);
          --lp-page-glow-2: rgba(45, 175, 150, 0.14);
          --lp-page-surface: rgba(16, 25, 40, 0.8);
          --lp-primary: #4f98d4;
          --lp-primary-strong: #74b0e4;
          --lp-primary-shadow: rgba(88, 166, 232, 0.32);
          --lp-section-title: rgba(220, 225, 235, 0.88);
        }

        .lp-catalog-hero {
          position: relative;
          overflow: hidden;
          padding: 14px 16px;
          border-radius: 18px;
          border: 1px solid color-mix(in srgb, var(--lp-page-accent-soft) 52%, rgba(186, 204, 227, 0.16));
          background: rgba(23, 35, 52, 0.78);
          box-shadow: var(--lp-shadow-sm);
        }

        .lp-catalog-hero-eyebrow {
          font-size: var(--lp-type-xs);
          text-transform: uppercase;
          letter-spacing: 0.06em;
          font-weight: 700;
          opacity: 0.86;
          color: color-mix(in srgb, var(--lp-page-accent-strong) 76%, rgba(220, 225, 235, 0.92));
        }

        .lp-catalog-hero-title {
          margin-top: 2px;
          font-family: var(--lp-font-display);
          font-size: clamp(1.08rem, 1.4vw, 1.34rem);
          line-height: 1.2;
          font-weight: 700;
          color: rgba(241, 245, 249, 0.97);
        }

        .lp-catalog-hero-subtitle {
          margin-top: 4px;
          max-width: 78ch;
          font-size: 0.92rem;
          line-height: 1.46;
          color: rgba(221, 230, 240, 0.84);
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
          background: rgba(23, 35, 52, 0.84);
          border: 1px solid rgba(186, 204, 227, 0.12);
          border-radius: 20px;
          backdrop-filter: blur(10px);
          box-shadow: var(--lp-shadow-sm);
        }

        .lp-catalog-scope .lp-sticky-controls {
          background: rgba(23, 35, 52, 0.84);
          border-color: color-mix(in srgb, var(--lp-page-accent-soft) 55%, rgba(186, 204, 227, 0.12));
        }

        .lp-page-shell {
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: var(--lp-space-4);
        }

        .lp-page-header-block {
          padding-top: 6px;
          padding-bottom: 2px;
        }

        .lp-page-header-kicker {
          opacity: 0.74;
          color: rgba(226, 232, 240, 0.78);
        }

        .lp-page-title {
          font-family: var(--lp-font-display);
          font-size: clamp(1.5rem, 2.1vw, 1.78rem);
          font-weight: 600;
          letter-spacing: 0.01em;
          line-height: 1.18;
        }

        .lp-page-header-subtitle {
          max-width: 44rem;
          opacity: 0.84;
        }

        .lp-page-controls {
          margin-top: 2px;
          margin-bottom: 4px;
        }

        .lp-page-controls-row {
          min-height: 42px;
        }

        .lp-panel-card {
          border: 1px solid rgba(186, 204, 227, 0.1) !important;
          border-radius: 18px;
          background: rgba(23, 35, 52, 0.74) !important;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .lp-panel-card--compact {
          padding-top: 14px !important;
          padding-bottom: 14px !important;
        }

        .lp-page-main-grid {
          width: 100%;
          display: grid;
          gap: var(--lp-space-5);
          align-items: start;
        }

        .lp-page-main-grid--sidebar {
          grid-template-columns: minmax(0, 1fr) 340px;
        }

        .lp-page-main-grid--balanced {
          grid-template-columns: repeat(2, minmax(0, 1fr));
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
          background: rgba(23, 35, 52, 0.46);
          border: 1px solid rgba(186, 204, 227, 0.075);
          border-radius: 22px;
          backdrop-filter: blur(8px);
          box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
        }

        .lp-catalog-scope .lp-rail {
          background: rgba(23, 35, 52, 0.46);
          border-color: color-mix(in srgb, var(--lp-page-accent-soft) 30%, rgba(186, 204, 227, 0.075));
        }

        .lp-rail-content {
          padding: var(--lp-space-5);
          display: flex;
          flex-direction: column;
          gap: var(--lp-space-4);
        }

        .lp-rail--bar {
          border: none;
          border-right: 1px solid rgba(186, 204, 227, 0.11);
          border-radius: 0;
          box-shadow: none;
          background: rgba(15, 24, 39, 0.44);
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
          background: rgba(15, 24, 39, 0.44);
          border-right: 1px solid rgba(186, 204, 227, 0.11);
          backdrop-filter: blur(8px);
          pointer-events: none;
        }

        .lp-main {
          flex: 1;
          min-width: 0;
          max-width: none;
        }

        .lp-courses-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: var(--lp-space-3);
          align-items: stretch;
        }

        .lp-courses-grid-item {
          min-width: 0;
          display: flex;
        }

        .lp-courses-grid-item .lp-course-card {
          width: 100%;
          min-height: 264px;
        }

        .lp-courses-section {
          margin-top: 2px;
        }

        .lp-courses-section-title {
          font-family: var(--lp-font-display);
          font-size: var(--lp-type-sm);
          letter-spacing: 0.03em;
          text-transform: uppercase;
          color: var(--lp-section-title);
          font-weight: 700;
        }

        .lp-courses-section-subtitle {
          font-size: var(--lp-type-xs);
          color: rgba(220, 225, 235, 0.68);
        }

        .lp-courses-collection-title {
          font-family: var(--lp-font-display);
          font-size: clamp(1.18rem, 1.5vw, 1.42rem);
          font-weight: 700;
          letter-spacing: 0.01em;
          color: rgba(238, 242, 249, 0.94);
          margin-top: 2px;
        }

        .lp-courses-row-title {
          font-family: var(--lp-font-display);
          font-size: 1.06rem;
          font-weight: 700;
          letter-spacing: 0.015em;
          color: rgba(226, 234, 244, 0.9);
        }

        .lp-courses-row-head {
          margin-top: 2px;
        }

        .lp-courses-rail-controls {
          opacity: 0.92;
        }

        .lp-courses-rail {
          display: grid;
          grid-auto-flow: column;
          grid-auto-columns: minmax(360px, 39vw);
          gap: var(--lp-space-3);
          overflow-x: auto;
          overflow-y: hidden;
          scroll-snap-type: x proximity;
          padding-bottom: 4px;
          scrollbar-width: thin;
        }

        .lp-rail-nav-btn {
          border: 1px solid rgba(186, 204, 227, 0.18);
          background: rgba(15, 24, 39, 0.7);
          color: rgba(235, 241, 249, 0.92);
        }

        .lp-rail-nav-btn:hover {
          border-color: rgba(186, 204, 227, 0.34);
          background: rgba(21, 34, 54, 0.86);
        }

        .lp-catalog-scope .lp-rail-nav-btn:hover {
          border-color: color-mix(in srgb, var(--lp-page-accent-soft) 65%, rgba(186, 204, 227, 0.34));
          background: color-mix(in srgb, var(--lp-page-accent-soft) 28%, rgba(21, 34, 54, 0.86));
        }

        .lp-courses-rail-item {
          min-width: 0;
          display: flex;
          scroll-snap-align: start;
        }

        .lp-courses-rail-item .lp-course-card {
          width: 100%;
          min-height: 244px;
        }

        .lp-catalog--explore .lp-courses-grid-item .lp-course-card,
        .lp-catalog--explore .lp-courses-grid-item .lp-path-card,
        .lp-catalog--explore .lp-courses-grid-item .lp-article-card,
        .lp-catalog--explore .lp-courses-rail-item .lp-course-card,
        .lp-catalog--explore .lp-courses-rail-item .lp-path-card,
        .lp-catalog--explore .lp-courses-rail-item .lp-article-card {
          width: 100%;
          min-height: 214px;
        }

        .lp-catalog--explore .lp-course-card,
        .lp-catalog--explore .lp-path-card,
        .lp-catalog--explore .lp-article-card {
          padding: 14px 14px 12px;
        }

        .lp-catalog--explore .lp-card-title {
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
          overflow: hidden;
        }

        .lp-catalog--explore .lp-course-summary,
        .lp-catalog--explore .lp-path-description {
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 2;
          overflow: hidden;
        }

        .lp-catalog--explore .lp-path-next-line {
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
          overflow: hidden;
        }

        .lp-catalog--explore .lp-course-card .lp-social-strip,
        .lp-catalog--explore .lp-path-card .lp-path-meta-row,
        .lp-catalog--explore .lp-article-card .lp-article-meta-row {
          min-height: 18px;
        }

        .lp-catalog--explore .lp-course-card .lp-course-context-line,
        .lp-catalog--explore .lp-path-card .lp-path-context-line,
        .lp-catalog--explore .lp-course-card .lp-card-taxonomy,
        .lp-catalog--explore .lp-article-card .lp-article-context-line,
        .lp-catalog--explore .lp-article-card .lp-article-tag-row {
          min-height: 28px;
          align-items: center;
        }

        .lp-catalog--explore .lp-path-card .lp-path-context-line {
          margin-top: 0;
        }

        .lp-catalog--explore .lp-article-card .lp-article-context-line {
          margin-top: -2px;
          margin-bottom: -2px;
          color: rgba(218, 227, 238, 0.78);
        }

        .lp-catalog--explore .lp-card-actions {
          margin-top: auto;
          min-height: 34px;
        }

        .lp-catalog--explore .lp-article-summary-chip {
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
          overflow: hidden;
          white-space: normal;
          line-height: 1.35;
        }

        .lp-catalog--explore .lp-course-media-slot,
        .lp-catalog--explore .lp-article-media-slot {
          width: 196px;
          padding-top: 26px;
          padding-right: 12px;
        }

        .lp-catalog--explore .lp-course-thumb--side {
          width: 196px;
        }

        .lp-catalog--explore .lp-courses-section-title {
          font-size: 1.32rem;
          text-transform: none;
          letter-spacing: 0.01em;
          margin-top: 6px;
        }

        .lp-catalog--explore .lp-courses-section-subtitle {
          font-size: 0.86rem;
          color: rgba(220, 225, 235, 0.72);
          margin-top: -4px;
          margin-bottom: 2px;
        }

        .lp-catalog--explore .lp-courses-grid,
        .lp-catalog--explore .lp-courses-rail {
          display: grid;
          grid-template-columns: none;
          grid-auto-flow: column;
          grid-auto-columns: 212px;
          justify-content: start;
          align-content: start;
          gap: 10px;
          overflow-x: auto;
          overflow-y: hidden;
          scroll-snap-type: x mandatory;
          padding: 4px 8px 10px 8px;
          scrollbar-width: none;
        }

        .lp-catalog--explore .lp-courses-grid::-webkit-scrollbar,
        .lp-catalog--explore .lp-courses-rail::-webkit-scrollbar {
          display: none;
        }

        .lp-catalog--explore .lp-courses-grid-item,
        .lp-catalog--explore .lp-courses-rail-item {
          scroll-snap-align: start;
          width: 212px;
          flex: 0 0 212px;
          min-width: 212px;
        }

        .lp-catalog--explore .lp-courses-grid-item--featured {
          grid-column: auto;
          width: 212px;
          flex: 0 0 212px;
        }

        .lp-catalog--explore .lp-explore-course-grid,
        .lp-catalog--explore .lp-explore-path-grid {
          grid-template-columns: repeat(auto-fit, minmax(212px, 212px));
          grid-auto-flow: row;
          overflow: visible;
          scroll-snap-type: none;
          scrollbar-width: auto;
          padding: 4px 0 10px;
          justify-content: start;
        }

        .lp-catalog--explore .lp-explore-course-grid::-webkit-scrollbar,
        .lp-catalog--explore .lp-explore-path-grid::-webkit-scrollbar {
          display: initial;
        }

        .lp-catalog--explore .lp-explore-course-grid .lp-courses-grid-item,
        .lp-catalog--explore .lp-explore-path-grid .lp-courses-grid-item {
          width: 212px;
          min-width: 212px;
          flex: 0 0 212px;
          scroll-snap-align: none;
        }

        .lp-catalog--explore .lp-explore-course-grid {
          grid-template-columns: repeat(4, 212px);
        }

        .lp-catalog--explore .lp-explore-path-grid {
          grid-template-columns: repeat(3, 212px);
        }

        .lp-catalog--explore .lp-explore-course-grid--single,
        .lp-catalog--explore .lp-explore-path-grid--single {
          grid-template-columns: minmax(248px, 320px);
        }

        .lp-catalog--explore .lp-explore-course-grid--pair {
          grid-template-columns: repeat(2, minmax(212px, 248px));
        }

        .lp-catalog--explore .lp-explore-path-grid--pair {
          grid-template-columns: repeat(2, minmax(232px, 280px));
        }

        .lp-catalog--explore .lp-explore-article-grid {
          grid-template-columns: repeat(4, 212px);
          grid-auto-flow: row;
          overflow: visible;
          scroll-snap-type: none;
          scrollbar-width: auto;
          padding: 4px 0 10px;
        }

        .lp-catalog--explore .lp-explore-article-grid .lp-courses-grid-item {
          width: 212px;
          min-width: 212px;
          flex: 0 0 212px;
          scroll-snap-align: none;
        }

        .lp-catalog--explore .lp-explore-path-grid .lp-path-card {
          min-height: 236px;
        }

        .lp-catalog--explore .lp-explore-course-grid--single .lp-courses-grid-item,
        .lp-catalog--explore .lp-explore-path-grid--single .lp-courses-grid-item {
          width: 100%;
          min-width: 248px;
          max-width: 320px;
        }

        .lp-catalog--explore .lp-explore-course-grid--pair .lp-courses-grid-item {
          width: 100%;
          min-width: 212px;
          max-width: 248px;
        }

        .lp-catalog--explore .lp-explore-path-grid--pair .lp-courses-grid-item {
          width: 100%;
          min-width: 232px;
          max-width: 280px;
        }

        .lp-explore-category-btn {
          border-radius: 999px !important;
          min-height: 30px !important;
          padding: 3px 12px !important;
          letter-spacing: 0.01em !important;
          text-transform: none !important;
          font-size: 0.78rem !important;
          border-color: rgba(186, 204, 227, 0.32) !important;
          color: rgba(215, 226, 239, 0.9) !important;
          background: rgba(255, 255, 255, 0.04) !important;
        }

        .lp-explore-category-btn--active {
          border-color: rgba(120, 178, 237, 0.48) !important;
          color: rgba(235, 244, 252, 0.96) !important;
          background: linear-gradient(160deg, rgba(70, 120, 196, 0.4), rgba(45, 87, 152, 0.3)) !important;
          box-shadow: inset 0 0 0 1px rgba(120, 178, 237, 0.28);
        }

        @media (max-width: 1280px) {
          .lp-catalog--explore .lp-explore-course-grid {
            grid-template-columns: repeat(3, 212px);
          }
          .lp-catalog--explore .lp-explore-path-grid {
            grid-template-columns: repeat(2, 212px);
          }
          .lp-catalog--explore .lp-explore-article-grid {
            grid-template-columns: repeat(3, 212px);
          }
        }

        @media (max-width: 920px) {
          .lp-catalog--explore .lp-explore-course-grid,
          .lp-catalog--explore .lp-explore-path-grid,
          .lp-catalog--explore .lp-explore-article-grid {
            grid-template-columns: repeat(2, 212px);
          }
        }

        @media (max-width: 640px) {
          .lp-catalog--explore .lp-explore-course-grid,
          .lp-catalog--explore .lp-explore-path-grid,
          .lp-catalog--explore .lp-explore-article-grid {
            grid-template-columns: repeat(1, 212px);
          }
        }

        .lp-catalog--explore .lp-course-card,
        .lp-catalog--explore .lp-path-card,
        .lp-catalog--explore .lp-article-card {
          width: 212px;
          min-height: 272px;
          border-radius: 12px;
          overflow: hidden;
          border: none !important;
          box-shadow: 0 7px 20px rgba(0, 0, 0, 0.34);
          transition: transform 160ms ease, box-shadow 180ms ease;
          display: flex;
          flex-direction: column;
        }

        .lp-catalog--explore .lp-course-card--surface,
        .lp-catalog--explore .lp-accent-card {
          background:
            radial-gradient(120% 90% at 72% 8%, rgba(88, 166, 232, 0.08), transparent 62%),
            linear-gradient(142deg, rgba(19, 32, 50, 0.78), rgba(13, 24, 40, 0.76)) !important;
          border: none !important;
        }

        .lp-catalog--explore .lp-course-card::before,
        .lp-catalog--explore .lp-accent-card::before,
        .lp-catalog--explore .lp-course-card::after {
          display: none;
        }

        .lp-catalog--explore .lp-path-card {
          min-height: 246px;
        }

        .lp-catalog--explore .lp-course-card:hover,
        .lp-catalog--explore .lp-path-card:hover,
        .lp-catalog--explore .lp-article-card:hover {
          transform: translateY(var(--lp-hover-lift));
          box-shadow: var(--lp-hover-shadow);
          z-index: 5;
        }

        .lp-catalog--explore .lp-card-title {
          font-size: 0.94rem;
          line-height: 1.22;
          padding-right: 110px;
          min-height: 2.44em;
          height: 2.44em;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 2;
          overflow: hidden;
        }

        .lp-catalog--explore .lp-card-body {
          font-size: 0.82rem;
          line-height: 1.3;
          max-width: 28ch;
          -webkit-line-clamp: 1;
        }

        .lp-catalog--explore .lp-course-summary,
        .lp-catalog--explore .lp-path-description,
        .lp-catalog--explore .lp-article-summary-chip {
          display: none;
        }

        .lp-catalog--explore .lp-course-status-line {
          display: none;
        }

        .lp-catalog--explore .lp-course-card-main,
        .lp-catalog--explore .lp-article-card-main {
          flex-direction: column;
          align-items: stretch;
          gap: 10px;
          flex: 1 1 auto;
        }

        .lp-catalog--explore .lp-course-card-content,
        .lp-catalog--explore .lp-article-card-content {
          order: 2;
          padding-top: 22px;
          padding-right: 0;
          display: flex;
          flex-direction: column;
          min-height: 132px;
          flex: 1 1 auto;
        }

        .lp-catalog--explore .lp-path-card .lp-card-content {
          padding-top: 22px;
          display: flex;
          flex-direction: column;
          min-height: 132px;
          flex: 1 1 auto;
        }

        .lp-catalog--explore .lp-course-media-slot,
        .lp-catalog--explore .lp-article-media-slot {
          order: 1;
          width: 100%;
          margin-left: 0;
          padding: 0;
          justify-content: stretch;
        }

        .lp-catalog--explore .lp-course-thumb--side {
          width: 100%;
          height: 96px;
          border-radius: 9px;
          object-fit: cover;
          border: none;
          box-shadow: none;
        }

        .lp-catalog--explore .lp-course-thumb--placeholder-block {
          height: 96px;
          border-radius: 9px;
          border: 1px solid rgba(255, 255, 255, 0.08);
          background:
            radial-gradient(120% 120% at 16% 12%, rgba(88, 166, 232, 0.1), transparent 58%),
            linear-gradient(145deg, rgba(23, 38, 59, 0.56), rgba(14, 26, 43, 0.5));
        }

        .lp-catalog--explore .lp-card-topright {
          top: 6px;
          right: 6px;
          padding: 1px 5px;
          gap: 4px;
          border-radius: 999px;
          background: rgba(7, 16, 32, 0.42);
          border: 1px solid rgba(186, 204, 227, 0.1);
          backdrop-filter: blur(8px);
        }

        .lp-catalog--explore .lp-card-topright .lp-chip {
          display: none !important;
        }

        .lp-catalog--explore .lp-social-strip,
        .lp-catalog--explore .lp-card-subtitle {
          font-size: 0.74rem;
          opacity: 0.68;
        }

        .lp-catalog--explore .lp-course-card .lp-social-strip {
          display: none;
        }

        .lp-catalog--explore .lp-path-card .lp-path-meta-row,
        .lp-catalog--explore .lp-article-card .lp-article-meta-row {
          min-height: 18px;
        }

        .lp-catalog--explore .lp-social-strip .lp-card-subtitle,
        .lp-catalog--explore .lp-article-byline,
        .lp-catalog--explore .lp-path-meta-row .lp-card-subtitle {
          display: none;
        }

        .lp-catalog--explore .lp-social-strip .lp-meta-chip--rating {
          display: none;
        }

        .lp-catalog--explore .lp-path-card .lp-card-topright .lp-meta-chip--rating {
          display: none;
        }

        .lp-catalog--explore .lp-course-context-line {
          display: none;
          margin-top: -4px;
          margin-bottom: 2px;
          color: rgba(218, 227, 238, 0.8);
          letter-spacing: 0.01em;
          line-height: 1.24;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 2;
          overflow: hidden;
          min-height: 2.48em;
        }

        .lp-catalog--explore .lp-course-context-line--placeholder {
          display: none;
        }

        .lp-catalog--explore .lp-social-strip .lp-meta-chip:nth-of-type(n+3) {
          display: none;
        }

        .lp-catalog--explore .lp-card-taxonomy .lp-meta-chip--quiet,
        .lp-catalog--explore .lp-article-tag-row .lp-meta-chip:nth-of-type(n+2),
        .lp-catalog--explore .lp-path-meta-row .lp-meta-chip:nth-of-type(n+2) {
          display: none;
        }

        .lp-catalog--explore .lp-path-card .lp-path-context-line,
        .lp-catalog--explore .lp-article-card .lp-article-context-line,
        .lp-catalog--explore .lp-article-card .lp-article-tag-row {
          min-height: 28px;
          align-items: center;
        }

        .lp-catalog--explore .lp-article-card .lp-article-meta-row,
        .lp-catalog--explore .lp-article-card .lp-article-context-line,
        .lp-catalog--explore .lp-article-card .lp-article-tag-row {
          display: none;
          min-height: 0;
          margin: 0;
        }

        .lp-catalog--explore .lp-path-card .lp-path-context-line {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .lp-catalog--explore .lp-path-card .lp-path-next-line {
          display: none;
        }

        .lp-catalog--explore .lp-path-card--calm .lp-path-meta-row {
          display: none;
          min-height: 0;
          margin: 0;
        }

        .lp-catalog--explore .lp-path-card--calm .lp-path-context-line {
          min-height: 20px;
          margin-top: 2px;
          margin-bottom: 2px;
          color: rgba(255, 255, 255, 0.62);
          white-space: normal;
          overflow: visible;
          text-overflow: unset;
        }

        .lp-catalog--explore .lp-path-card--calm .lp-path-progress-line--compact {
          height: 3px;
          border-radius: 2px;
          opacity: 0.7;
          margin-top: -1px;
          margin-bottom: 2px;
        }

        .lp-catalog--explore .lp-path-card--calm .lp-path-primary-cta {
          background: rgba(255, 255, 255, 0.03) !important;
          border: 1px solid rgba(255, 255, 255, 0.12) !important;
          color: rgba(220, 232, 245, 0.84) !important;
          box-shadow: none !important;
        }

        .lp-catalog--explore .lp-path-card--calm .lp-path-primary-cta--active {
          background: rgba(120, 170, 255, 0.14) !important;
          border-color: rgba(159, 195, 255, 0.28) !important;
          color: rgba(227, 239, 255, 0.92) !important;
        }

        .lp-article-tag-placeholder {
          width: 0;
          height: 0;
          overflow: hidden;
          visibility: hidden;
          margin: 0;
          padding: 0;
        }

        .lp-catalog--explore .lp-course-card .lp-card-taxonomy {
          min-height: 28px;
          align-items: center;
        }

        .lp-catalog--explore .lp-course-card .lp-card-taxonomy:empty {
          display: none;
          min-height: 0;
        }

        .lp-catalog--explore .lp-card-actions {
          margin-top: auto;
          min-height: 34px;
        }

        .lp-catalog--explore .lp-card-actions .q-btn {
          border-radius: 10px;
          min-height: 31px !important;
          padding: 4px 10px !important;
          font-size: 0.74rem !important;
          letter-spacing: 0.01em;
          text-transform: none;
        }

        .lp-catalog--explore .lp-course-progress-hint {
          color: rgba(255, 255, 255, 0.52);
          font-size: 0.72rem;
          margin-top: -2px;
        }

        .lp-catalog--explore .lp-course-progress-line {
          height: 4px;
          opacity: 0.62;
          margin-top: -2px;
          margin-bottom: 2px;
        }

        .lp-catalog--explore .lp-course-progress-slot {
          min-height: 24px;
        }

        .lp-catalog--explore .lp-card-review-line {
          min-height: 18px;
          margin-top: 1px;
          font-size: 0.74rem;
          line-height: 1.25;
          color: rgba(223, 232, 243, 0.8);
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
          overflow: hidden;
        }

        .lp-catalog--explore .lp-card-review-line--empty {
          color: rgba(193, 206, 221, 0.46);
        }

        .lp-catalog--explore .lp-card-meta-spacer {
          min-height: 28px;
          width: 100%;
        }

        .lp-catalog--explore .lp-card-actions .lp-status-select,
        .lp-catalog--explore .lp-path-card .lp-card-actions .q-btn:nth-child(2) {
          display: none !important;
        }

        .lp-catalog--explore .lp-card-actions .q-btn--outline {
          background: rgba(255, 255, 255, 0.04) !important;
          border-color: rgba(186, 204, 227, 0.16) !important;
        }

        .lp-catalog--explore .lp-card-actions .lp-course-cta-primary {
          background: linear-gradient(160deg, rgba(95, 162, 223, 0.94), rgba(67, 133, 198, 0.9)) !important;
          border: 1px solid rgba(160, 209, 244, 0.35) !important;
          color: rgba(240, 247, 255, 0.95) !important;
          box-shadow: 0 5px 14px rgba(56, 126, 192, 0.2);
        }

        .lp-catalog--explore .lp-card-actions .lp-course-cta-secondary {
          background: rgba(255, 255, 255, 0.03) !important;
          border: 1px solid rgba(255, 255, 255, 0.12) !important;
          color: rgba(220, 232, 245, 0.82) !important;
          box-shadow: none !important;
        }

        .lp-catalog--explore .lp-courses-rail-item--hero .lp-course-card {
          box-shadow: 0 11px 30px rgba(17, 35, 68, 0.36), 0 8px 24px rgba(0, 0, 0, 0.35);
        }

        .lp-catalog--explore .lp-card-topright .q-btn {
          opacity: 0;
          pointer-events: none;
          transition: opacity 120ms ease;
        }

        .lp-catalog--explore .lp-card--hover:hover .lp-card-topright .q-btn {
          opacity: 1;
          pointer-events: auto;
        }

        .lp-catalog--explore .lp-explore-spotlight-strip {
          width: 100%;
          margin: 0 0 4px;
          padding: 8px 10px;
          border-radius: 12px;
          border: 1px solid rgba(116, 176, 228, 0.24);
          background:
            radial-gradient(120% 140% at 10% 0%, rgba(116, 176, 228, 0.16), transparent 58%),
            linear-gradient(145deg, rgba(16, 27, 44, 0.78), rgba(13, 22, 35, 0.72));
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
        }

        .lp-catalog--explore .lp-explore-spotlight-strip > .column {
          max-width: 900px;
          min-width: 0;
        }

        .lp-catalog--explore .lp-explore-spotlight-eyebrow {
          font-size: 0.72rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: rgba(116, 176, 228, 0.92);
          font-weight: 700;
        }

        .lp-catalog--explore .lp-explore-spotlight-title {
          font-size: 0.96rem;
          font-weight: 700;
          line-height: 1.25;
        }

        .lp-catalog--explore .lp-explore-spotlight-body {
          font-size: 0.8rem;
          line-height: 1.35;
          color: rgba(220, 225, 235, 0.8);
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
          overflow: hidden;
        }

        .lp-catalog--explore .lp-explore-spotlight-meta {
          font-size: 0.78rem;
          color: rgba(220, 225, 235, 0.66);
        }

        .lp-catalog--explore .lp-sticky-controls {
          margin: 0 0 6px;
          padding: 8px 10px;
          background: linear-gradient(180deg, rgba(12, 21, 35, 0.58), rgba(11, 20, 33, 0.44));
          border-color: rgba(186, 204, 227, 0.06);
          box-shadow: 0 8px 22px rgba(0, 0, 0, 0.18);
        }

        .lp-catalog--explore .lp-topbar-group--secondary {
          opacity: 0.84;
        }

        .lp-explore-rhythm-strip {
          margin-top: -2px;
          margin-bottom: 4px;
          padding: 6px 10px;
          border-radius: 10px;
          border: 1px solid rgba(186, 204, 227, 0.08);
          background: rgba(10, 18, 31, 0.42);
        }

        .lp-explore-section-block {
          border-top: 1px solid rgba(186, 204, 227, 0.09);
          padding-top: 6px;
          margin-top: 2px;
        }

        .lp-catalog--explore .lp-courses-toolbar-controls {
          border-left-color: rgba(186, 204, 227, 0.05);
        }

        .lp-catalog--explore .lp-courses-collection-title {
          font-size: 1.1rem;
          margin-bottom: 2px;
          letter-spacing: 0.01em;
        }

        .lp-catalog--explore .lp-courses-row-title {
          font-size: 0.9rem;
          font-weight: 600;
          letter-spacing: 0.01em;
          text-transform: none;
          opacity: 0.92;
        }

        .lp-catalog--explore .lp-topbar .q-field__native,
        .lp-catalog--explore .lp-topbar input {
          font-size: 0.92rem !important;
        }

        .lp-catalog--explore .lp-topbar .q-radio__label {
          font-size: 0.86rem;
          font-weight: 600;
        }

        /* Explore calm pass: lower contrast, softer chips/cards, more spacing */
        .lp-catalog-scope.lp-catalog--explore {
          --lp-page-glow-1: rgba(88, 166, 232, 0.08);
          --lp-page-glow-2: rgba(45, 175, 150, 0.08);
        }

        .lp-catalog--explore .lp-catalog-hero-title {
          color: rgba(255, 255, 255, 0.92);
          font-size: clamp(1.18rem, 1.5vw, 1.34rem);
        }

        .lp-catalog--explore .lp-catalog-hero-subtitle {
          color: rgba(255, 255, 255, 0.65);
        }

        .lp-catalog--explore .lp-topbar-group-label {
          text-transform: none;
          letter-spacing: 0.01em;
          color: rgba(255, 255, 255, 0.45);
          font-weight: 500;
        }

        .lp-catalog--explore .lp-courses-section-title {
          color: rgba(255, 255, 255, 0.92);
          font-size: 1.16rem;
          font-weight: 600;
        }

        .lp-catalog--explore .lp-courses-section-subtitle {
          color: rgba(255, 255, 255, 0.65);
        }

        .lp-catalog--explore .lp-card-title {
          color: rgba(255, 255, 255, 0.92);
          font-weight: 600;
        }

        .lp-catalog--explore .lp-card-subtitle,
        .lp-catalog--explore .lp-course-context-line,
        .lp-catalog--explore .lp-explore-spotlight-meta {
          color: rgba(255, 255, 255, 0.45);
        }

        .lp-catalog--explore .lp-explore-spotlight-title {
          color: rgba(255, 255, 255, 0.92);
          font-size: 0.92rem;
          font-weight: 600;
        }

        .lp-catalog--explore .lp-explore-spotlight-body {
          color: rgba(255, 255, 255, 0.65);
        }

        .lp-catalog--explore .lp-explore-spotlight-strip {
          border: 1px solid rgba(255, 255, 255, 0.06);
          background:
            radial-gradient(120% 140% at 10% 0%, rgba(116, 176, 228, 0.1), transparent 62%),
            linear-gradient(145deg, rgba(16, 27, 44, 0.66), rgba(13, 22, 35, 0.62));
          margin: 4px 0 8px;
          padding: 10px 12px;
        }

        .lp-catalog--explore .lp-course-card,
        .lp-catalog--explore .lp-path-card,
        .lp-catalog--explore .lp-article-card {
          border: 1px solid rgba(255, 255, 255, 0.06) !important;
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.24);
        }

        .lp-catalog--explore .lp-course-card--surface,
        .lp-catalog--explore .lp-accent-card {
          background:
            radial-gradient(120% 90% at 72% 8%, rgba(88, 166, 232, 0.05), transparent 64%),
            linear-gradient(142deg, rgba(19, 32, 50, 0.62), rgba(13, 24, 40, 0.6)) !important;
        }

        .lp-catalog--explore .lp-chip,
        .lp-catalog--explore .lp-meta-chip {
          background: rgba(255, 255, 255, 0.05) !important;
          border-color: rgba(255, 255, 255, 0.08) !important;
          color: rgba(255, 255, 255, 0.6) !important;
        }

        .lp-catalog--explore .lp-chip--sky,
        .lp-catalog--explore .lp-chip--teal,
        .lp-catalog--explore .lp-chip--lime {
          background: rgba(255, 255, 255, 0.05) !important;
          border-color: rgba(255, 255, 255, 0.1) !important;
          color: rgba(255, 255, 255, 0.66) !important;
        }

        .lp-catalog--explore .lp-chip--muted {
          background: rgba(255, 255, 255, 0.04) !important;
          border-color: rgba(255, 255, 255, 0.08) !important;
          color: rgba(255, 255, 255, 0.56) !important;
        }

        .lp-catalog--explore .lp-chip--sky {
          background: rgba(159, 195, 255, 0.12) !important;
          border-color: rgba(159, 195, 255, 0.24) !important;
          color: rgba(196, 220, 255, 0.88) !important;
        }

        .lp-catalog--explore .lp-chip--teal {
          background: rgba(126, 217, 163, 0.12) !important;
          border-color: rgba(126, 217, 163, 0.24) !important;
          color: rgba(184, 236, 206, 0.88) !important;
        }

        .lp-catalog--explore .lp-chip--lime {
          background: rgba(186, 230, 126, 0.12) !important;
          border-color: rgba(186, 230, 126, 0.22) !important;
          color: rgba(214, 241, 177, 0.86) !important;
        }

        .lp-catalog--explore .lp-course-status-chip {
          font-size: 0.74rem !important;
          font-weight: 500 !important;
          letter-spacing: 0.01em !important;
          box-shadow: none !important;
        }

        .lp-explore-category-btn {
          border-color: rgba(255, 255, 255, 0.08) !important;
          color: rgba(255, 255, 255, 0.55) !important;
          background: transparent !important;
        }

        .lp-explore-category-btn--active {
          border-color: rgba(159, 195, 255, 0.32) !important;
          color: rgba(159, 195, 255, 0.96) !important;
          background: rgba(120, 170, 255, 0.15) !important;
          box-shadow: none !important;
        }

        .lp-explore-section-block {
          border-top: 1px solid rgba(255, 255, 255, 0.06);
          margin-top: 14px;
          padding-top: 16px;
        }

        .lp-explore-header {
          padding-top: 6px;
          padding-bottom: 4px;
        }

        .lp-explore-header-kicker {
          opacity: 0.74;
        }

        .lp-explore-header-subtitle {
          max-width: 46rem;
          opacity: 0.84;
        }

        .lp-explore-toolbar {
          border-radius: 18px;
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
          border-bottom: 1px solid rgba(186, 204, 227, 0.045);
        }

        .lp-filters-tip {
          margin-top: -2px;
          margin-bottom: var(--lp-space-1);
          opacity: 0.68;
        }

        @media (max-width: 1280px) {
          :root {
            --lp-page-pad-x: 28px;
            --lp-rail-width: 276px;
          }
        }

        @media (min-width: 1320px) {
          .lp-courses-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: var(--lp-space-4);
          }
          .lp-courses-grid-item--featured {
            grid-column: 1 / -1;
          }
          .lp-courses-grid-item--featured .lp-course-card {
            min-height: 304px;
          }
          .lp-catalog--explore .lp-courses-grid-item--featured .lp-course-card,
          .lp-catalog--explore .lp-courses-grid-item--featured .lp-path-card,
          .lp-catalog--explore .lp-courses-grid-item--featured .lp-article-card {
            min-height: 236px;
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
          .lp-article-card-main {
            flex-direction: column-reverse;
          }
          .lp-course-media-slot {
            width: 100%;
            margin-left: 0;
            padding-right: 0;
            padding-top: 0;
            justify-content: flex-start;
          }
          .lp-article-media-slot {
            width: 100%;
            margin-left: 0;
            padding-right: 0;
            padding-top: 0;
            justify-content: flex-start;
          }
          .lp-course-thumb--side {
            width: min(100%, 360px);
          }
          .lp-courses-rail {
            grid-auto-columns: minmax(320px, 82vw);
          }
          .lp-catalog--explore .lp-course-media-slot,
          .lp-catalog--explore .lp-article-media-slot {
            width: 100%;
            padding-right: 0;
            padding-top: 0;
          }
          .lp-catalog--explore .lp-course-thumb--side {
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
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .lp-catalog--articles .lp-card {
          background: rgba(24, 37, 50, 0.78) !important;
          border-color: rgba(162, 214, 220, 0.2);
          border-radius: 18px;
        }

        .lp-catalog--articles .lp-article-card .lp-card-title {
          padding-right: 112px;
          line-height: 1.26;
        }

        .lp-catalog--articles .lp-article-card .lp-card-subtitle.lp-article-meta-line {
          font-size: 0.8rem;
          letter-spacing: 0.025em;
          opacity: 0.92;
        }

        .lp-catalog--articles .lp-article-card .lp-article-byline {
          font-weight: 700;
          color: rgba(223, 243, 246, 0.95) !important;
          letter-spacing: 0.02em;
        }

        .lp-catalog--articles .lp-article-card .lp-article-date {
          color: rgba(187, 213, 218, 0.9) !important;
          letter-spacing: 0.018em;
          opacity: 0.9;
        }

        .lp-catalog--articles .lp-article-card .lp-article-summary-chip {
          border-style: dashed;
          color: rgba(222, 239, 241, 0.92);
        }

        .lp-catalog--paths .lp-accent-card {
          background: rgba(18, 37, 43, 0.8) !important;
          border-color: rgba(133, 214, 204, 0.22);
        }

        .lp-catalog--paths .lp-path-card .lp-card-title {
          font-size: clamp(1.08rem, 1.24vw, 1.34rem);
          padding-right: 200px;
        }

        .lp-catalog--paths .lp-path-card .lp-card-body {
          max-width: 70ch;
        }

        .lp-catalog--paths .lp-path-card .lp-path-milestone {
          border-color: rgba(117, 228, 203, 0.34);
          background: rgba(85, 206, 181, 0.14);
        }

        .lp-catalog--paths .lp-path-card .lp-path-progress-label {
          text-transform: uppercase;
          letter-spacing: 0.055em;
          font-weight: 700;
          color: rgba(167, 223, 214, 0.9);
        }

        .lp-catalog--paths .lp-path-card .lp-path-progress-count {
          font-weight: 600;
          color: rgba(217, 239, 235, 0.92) !important;
        }

        .lp-catalog--paths .lp-path-card .lp-path-progress-bar .q-linear-progress__track {
          background: rgba(75, 192, 178, 0.22) !important;
        }

        .lp-catalog--paths .lp-path-card .lp-path-progress-bar .q-linear-progress__model {
          background: linear-gradient(90deg, rgba(87, 208, 187, 0.92), rgba(73, 182, 206, 0.88)) !important;
        }

        .lp-catalog--paths .lp-path-card .lp-path-description {
          opacity: 0.9;
        }

        .lp-card-title {
          font-family: var(--lp-font-display);
          font-size: clamp(1.12rem, 1.28vw, 1.4rem);
          line-height: 1.2;
          font-weight: 600;
          letter-spacing: 0.01em;
          margin-bottom: 4px;
          padding-right: clamp(132px, 16vw, 196px);
        }

        .lp-catalog--articles .lp-card-title {
          font-size: clamp(1.02rem, 1.1vw, 1.24rem);
          font-weight: 600;
          letter-spacing: 0.008em;
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

        .lp-article-card-main {
          display: flex;
          flex-wrap: nowrap;
          align-items: flex-start;
          justify-content: space-between;
          gap: 18px;
          width: 100%;
        }

        .lp-article-card-content {
          min-width: 0;
          flex: 1 1 auto;
          gap: var(--lp-space-2);
          padding-right: var(--lp-space-2);
          padding-top: 2px;
          padding-bottom: 2px;
        }

        .lp-article-media-slot {
          width: 276px;
          margin-left: auto;
          padding-right: 16px;
          padding-top: 34px;
          flex: 0 0 auto;
          display: flex;
          justify-content: flex-end;
          align-items: flex-start;
        }

        .lp-article-thumb {
          object-fit: cover;
          background: rgba(255, 255, 255, 0.02);
        }

        .lp-course-thumb--side {
          margin-left: 0;
          margin-right: 0;
          margin-top: 0;
          margin-bottom: 0;
          width: 276px;
          flex: 0 0 auto;
        }

        .lp-course-thumb--contain {
          object-fit: contain;
          background: transparent;
          padding: 0;
        }

        .lp-course-thumb--placeholder-block {
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(26, 39, 56, 0.72);
          border: 1px dashed rgba(186, 204, 227, 0.28);
          box-shadow: none;
        }

        .lp-course-thumb-placeholder-block-icon {
          font-size: 1.2rem;
          color: rgba(189, 213, 239, 0.74);
        }

        .lp-course-thumb-placeholder {
          padding: 6px 10px;
          border-radius: var(--lp-radius-pill);
          border: 1px dashed rgba(186, 204, 227, 0.28);
          background: rgba(255, 255, 255, 0.025);
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

        .lp-course-status-line {
          font-size: var(--lp-type-xs);
          letter-spacing: 0.03em;
          text-transform: uppercase;
          font-weight: 700;
          color: rgba(198, 221, 244, 0.88);
          margin-top: 2px;
          margin-bottom: -2px;
        }

        .lp-course-status-chip {
          border-color: color-mix(in srgb, var(--lp-page-accent-soft) 70%, rgba(186, 204, 227, 0.3));
          background: color-mix(in srgb, var(--lp-page-accent-soft) 42%, rgba(255, 255, 255, 0.08));
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
          transform: translateY(-1px);
          box-shadow: 0 8px 18px rgba(0, 0, 0, 0.14);
          border-color: var(--lp-border-strong);
          background: var(--lp-surface-2) !important;
        }

        .lp-course-card,
        .lp-accent-card {
          position: relative;
          overflow: hidden;
        }

        .lp-course-card--surface {
          background: rgba(24, 35, 52, 0.76);
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

        .lp-course-card--interested::before,
        .lp-accent-card--interested::before {
          background: rgba(88, 166, 232, 0.88);
        }

        .lp-course-card--in_progress::before,
        .lp-accent-card--in_progress::before {
          background: rgba(52, 211, 153, 0.88);
        }

        .lp-course-card--completed::before,
        .lp-accent-card--completed::before {
          background: rgba(163, 230, 53, 0.88);
        }

        .lp-accent-card--not_selected::before {
          background: rgba(148, 163, 184, 0.62);
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

        .lp-meta-chip--rating {
          border-color: rgba(255, 204, 102, 0.36);
          background: rgba(255, 204, 102, 0.11);
          color: rgba(255, 214, 137, 0.96);
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
          letter-spacing: 0.02em;
        }

        .lp-container .q-btn {
          min-height: 33px !important;
          border-radius: 10px !important;
          font-size: 0.76rem !important;
          letter-spacing: 0.02em;
          font-weight: 600 !important;
          text-transform: uppercase;
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
          background: rgba(255, 255, 255, 0.03) !important;
        }

        .q-btn--outline .q-btn__content,
        .q-btn--outline .q-icon {
          color: var(--lp-text);
        }

        .q-btn--outline:hover {
          border-color: var(--lp-border-strong) !important;
          background: rgba(255, 255, 255, 0.05) !important;
        }

        .q-btn--standard {
          background: var(--lp-primary) !important;
          color: #f8fbff !important;
        }

        .q-btn--standard:hover {
          box-shadow: 0 6px 16px rgba(79, 152, 212, 0.18);
        }

        :is(button, .q-btn, .q-field__control, .q-item, a, input, textarea, select):focus-visible {
          outline: none !important;
          box-shadow: var(--lp-focus-ring) !important;
        }

        :is(.q-btn-dropdown, .q-btn-dropdown .q-btn, .q-dialog .q-btn):focus-visible {
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

        .lp-courses-filter-drawer {
          width: min(92vw, 360px);
          min-height: 72vh;
          border-radius: 18px !important;
          display: flex;
          flex-direction: column;
          gap: var(--lp-space-3);
          transform: translateX(0);
          transition: transform 180ms ease, box-shadow 180ms ease;
        }

        body .q-dialog__inner--right .lp-courses-filter-drawer {
          animation: lp-drawer-slide-in 180ms ease both;
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

        body .q-menu .q-item:focus-visible,
        body .q-menu .q-item.q-manual-focusable--focused {
          outline: none !important;
          box-shadow: inset 0 0 0 1px rgba(124, 192, 251, 0.44), var(--lp-focus-ring) !important;
          background: rgba(79, 152, 212, 0.16) !important;
        }

        body .q-dialog .q-card.lp-dialog .q-btn:focus-visible,
        body .q-dialog .q-card.lp-dialog .q-field__control:focus-visible {
          outline: none !important;
          box-shadow: var(--lp-focus-ring) !important;
        }

        .lp-home-scope {
          --lp-page-accent-soft: rgba(88, 166, 232, 0.08);
          --lp-page-glow-1: rgba(88, 166, 232, 0.03);
          --lp-page-glow-2: rgba(45, 175, 150, 0.02);
        }

        .lp-home-scope::before {
          opacity: 0.22;
        }

        .lp-home-topbar {
          margin-top: 0;
          margin-bottom: 0;
        }

        .lp-home-topbar-prompt {
          font-size: 0.92rem;
          color: rgba(226, 232, 240, 0.8);
          font-weight: 600;
          letter-spacing: 0.01em;
        }

        .lp-home-overview-strip {
          border-color: rgba(186, 204, 227, 0.13);
          background:
            radial-gradient(120% 140% at 12% 0%, rgba(116, 176, 228, 0.12), transparent 62%),
            linear-gradient(140deg, rgba(16, 26, 42, 0.76), rgba(12, 21, 34, 0.68));
        }

        .lp-home-overview-title {
          font-family: var(--lp-font-display);
          font-size: var(--lp-type-sm);
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: rgba(210, 220, 234, 0.82);
        }

        .lp-home-overview-divider {
          margin: 4px 0 2px;
          opacity: 0.42;
        }

        .lp-home-overview-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
        }

        .lp-home-overview-stat {
          min-width: 74px;
          padding: 3px 8px;
          border-radius: 10px;
          background: rgba(7, 16, 32, 0.34);
          border: 1px solid rgba(186, 204, 227, 0.1);
        }

        .lp-home-overview-label {
          font-size: var(--lp-type-xs);
          color: rgba(206, 218, 233, 0.68);
          letter-spacing: 0.015em;
        }

        .lp-home-overview-value {
          font-family: var(--lp-font-display);
          font-size: clamp(1.18rem, 1.4vw, 1.42rem);
          font-weight: 700;
          letter-spacing: 0.02em;
          line-height: 1.1;
          color: rgba(236, 242, 249, 0.98);
        }

        .lp-home-row-grid {
          width: 100%;
          display: grid;
          grid-template-columns: minmax(0, 1fr) 340px;
          gap: var(--lp-space-5);
          align-items: start;
        }

        .lp-home-grid-12 {
          width: 100%;
          display: grid;
          grid-template-columns: repeat(12, minmax(0, 1fr));
          gap: var(--lp-space-6);
          align-items: start;
        }

        .lp-home-span-3 { grid-column: span 3; }
        .lp-home-span-4 { grid-column: span 4; }
        .lp-home-span-5 { grid-column: span 5; }
        .lp-home-span-8 { grid-column: span 8; }
        .lp-home-span-12 { grid-column: span 12; }

        .lp-home-col-stack {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .lp-home-row-grid--primary {
          grid-template-columns: minmax(0, 1fr) 340px;
        }

        .lp-home-row-grid--single {
          grid-template-columns: minmax(0, 1fr);
        }

        .lp-home-row-grid--social {
          grid-template-columns: minmax(0, 1.02fr) minmax(0, 1.18fr);
        }

        .lp-home-row-grid--balanced {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .lp-home-main-grid--top {
          grid-template-columns: minmax(0, 1fr) 340px;
        }

        .lp-home-main-grid--middle {
          grid-template-columns: minmax(0, 1fr) 420px;
        }

        .lp-home-main-grid--footer {
          grid-template-columns: minmax(0, 1fr);
        }

        .lp-home-main-col {
          min-width: 0;
        }

        .lp-home-workspace-grid {
          width: 100%;
          display: grid;
          grid-template-columns: minmax(0, 1fr) 420px;
          gap: var(--lp-space-5);
          align-items: start;
        }

        .lp-home-workspace-grid--balanced {
          grid-template-columns: minmax(0, 1fr) minmax(320px, 0.86fr);
        }

        .lp-home-workspace-col {
          min-width: 0;
        }

        .lp-home-focus-card,
        .lp-home-actions-card,
        .lp-home-convo-shell,
        .lp-home-track-shell,
        .lp-home-path-shell,
        .lp-home-secondary-shell {
          border-color: rgba(186, 204, 227, 0.1) !important;
          background: rgba(17, 28, 44, 0.72) !important;
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1) !important;
        }

        .lp-home-focus-card {
          padding: 16px 18px 14px !important;
        }

        .lp-home-focus-card-body {
          min-height: 112px;
          justify-content: space-between;
        }

        .lp-home-focus-summary {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 8px;
        }

        .lp-home-focus-summary-item {
          min-width: 0;
          padding: 8px 10px;
          border-radius: 12px;
          background: rgba(8, 16, 30, 0.28);
          border: 1px solid rgba(186, 204, 227, 0.08);
        }

        .lp-home-focus-summary-label {
          font-size: 0.72rem;
          color: rgba(203, 216, 232, 0.62);
        }

        .lp-home-focus-summary-value {
          font-family: var(--lp-font-display);
          font-size: 0.96rem;
          font-weight: 600;
          line-height: 1.15;
        }

        .lp-home-hero-eyebrow {
          font-size: 0.84rem;
          letter-spacing: 0.01em;
          color: rgba(183, 214, 246, 0.82);
          font-weight: 500;
          text-transform: none;
        }

        .lp-home-hero-heading {
          font-family: var(--lp-font-display);
          font-size: clamp(1rem, 1.3vw, 1.18rem);
          font-weight: 500;
          line-height: 1.2;
          letter-spacing: 0.01em;
        }

        .lp-home-hero-meta {
          color: var(--lp-muted);
          font-size: 0.8rem;
          opacity: 0.72;
        }

        .lp-home-hero-avatars {
          margin-top: 2px;
        }

        .lp-home-hero-focus {
          border: 1px solid rgba(186, 204, 227, 0.17);
          background: rgba(7, 16, 32, 0.44);
        }

        .lp-home-actions-card {
          padding: 16px 16px 14px !important;
        }

        .lp-home-track-shell {
          padding: 16px 18px 16px !important;
        }

        .lp-home-intro-title {
          line-height: 1.15;
        }

        .lp-home-intro-dismiss {
          align-self: flex-start;
          color: rgba(186, 213, 237, 0.84) !important;
        }

        .lp-home-intro-steps {
          width: 100%;
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
          margin-top: 4px;
        }

        .lp-home-intro-step {
          display: flex;
          gap: 10px;
          align-items: flex-start;
          min-width: 0;
          padding: 10px 11px;
          border: 1px solid rgba(186, 204, 227, 0.08);
          border-radius: 16px;
          background: rgba(9, 18, 31, 0.22);
        }

        .lp-home-queue-title {
          font-family: var(--lp-font-display);
          font-size: clamp(0.92rem, 1.05vw, 1.02rem);
          line-height: 1.2;
          font-weight: 500;
          letter-spacing: 0.01em;
        }

        .lp-home-action-stats {
          border: 1px solid rgba(186, 204, 227, 0.12);
          border-radius: 10px;
          background: rgba(8, 16, 30, 0.46);
          padding: 10px 12px;
        }

        .lp-home-action-stat-label {
          font-size: 0.8rem;
          font-weight: 500;
          color: rgba(203, 216, 232, 0.66);
        }

        .lp-home-action-stat-value {
          font-family: var(--lp-font-display);
          font-size: 0.84rem;
          font-weight: 600;
          color: rgba(236, 242, 249, 0.86);
        }

        .lp-home-next-action-row {
          width: 100%;
          min-height: 62px !important;
          border: 1px solid rgba(186, 204, 227, 0.14) !important;
          border-radius: 11px !important;
          background: linear-gradient(160deg, rgba(22, 36, 56, 0.8), rgba(12, 23, 38, 0.7)) !important;
          padding: 9px 11px !important;
          text-align: left;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
          transition: transform 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
        }

        .lp-home-next-action-row:hover {
          border-color: rgba(186, 204, 227, 0.28) !important;
          background: linear-gradient(160deg, rgba(25, 42, 64, 0.84), rgba(14, 28, 45, 0.74)) !important;
          transform: translateY(var(--lp-hover-lift));
          box-shadow: var(--lp-hover-shadow);
        }

        .lp-home-next-action-icon {
          font-size: 16px;
          color: rgba(168, 205, 245, 0.92);
        }

        .lp-home-next-action-title {
          font-size: 0.96rem;
          font-weight: 700;
          letter-spacing: 0.01em;
          color: rgba(236, 242, 249, 0.95);
          line-height: 1.22;
        }

        .lp-home-next-action-subtitle {
          font-size: 0.78rem;
          color: rgba(204, 216, 231, 0.72);
          letter-spacing: 0.01em;
          line-height: 1.25;
        }

        .lp-home-next-action-chevron {
          font-size: 18px;
          color: rgba(194, 211, 231, 0.76);
        }

        .lp-home-focus-actions .q-btn {
          min-width: 144px;
        }

        .lp-home-hero-primary,
        .lp-home-hero-secondary {
          letter-spacing: 0.02em;
        }

        .lp-home-hero-primary {
          background: rgba(104, 156, 214, 0.92) !important;
          color: rgba(10, 20, 33, 0.96) !important;
          border: 1px solid rgba(160, 209, 244, 0.3) !important;
          box-shadow: none !important;
        }

        .lp-home-hero-secondary {
          border-color: transparent !important;
          color: rgba(186, 213, 237, 0.86) !important;
          background: transparent !important;
          box-shadow: none !important;
          min-width: 0 !important;
          padding-left: 0 !important;
          padding-right: 0 !important;
        }

        .lp-home-focus-primary-action {
          width: 100%;
          justify-content: center;
          background: rgba(104, 156, 214, 0.92) !important;
          color: rgba(10, 20, 33, 0.96) !important;
          border: 1px solid rgba(160, 209, 244, 0.3) !important;
          box-shadow: none !important;
        }

        .lp-home-focus-secondary-action {
          width: 100%;
        }

        .lp-home-controls-simple {
          padding-top: 0;
          padding-bottom: 2px;
        }

        .lp-home-snapshot-panel .grid {
          grid-template-columns: repeat(1, minmax(0, 1fr));
        }

        .lp-home-stat-grid {
          width: 100%;
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
        }

        .lp-home-stat-grid--compact {
          gap: 8px;
        }

        .lp-home-stat-card {
          border: 1px solid rgba(186, 204, 227, 0.1) !important;
          border-radius: 14px;
          background: rgba(8, 16, 30, 0.4);
          padding: 10px 10px 9px;
          min-height: 58px;
        }

        .lp-home-team-chart-footer {
          padding-top: 2px;
        }

        .lp-home-team-chart-footer .q-btn {
          min-width: 0 !important;
          padding-right: 2px !important;
        }

        .lp-home-team-chart-footer--simple {
          margin-top: 2px;
        }

        .lp-home-stat-value {
          font-family: var(--lp-font-display);
          font-size: 1.08rem;
          font-weight: 600;
          line-height: 1.1;
          color: rgba(237, 243, 250, 0.96);
        }

        .lp-home-stat-label {
          font-size: 0.7rem;
          color: rgba(204, 216, 231, 0.66);
          letter-spacing: 0.01em;
        }

        .lp-home-section-title {
          font-family: var(--lp-font-display);
          font-size: 0.9rem;
          font-weight: 500;
          letter-spacing: 0.015em;
        }

        .lp-home-avatar-chip {
          width: 24px;
          height: 24px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          font-size: 0.68rem;
          font-weight: 700;
          color: rgba(232, 240, 249, 0.94);
          border: 1px solid rgba(186, 204, 227, 0.22);
          background: rgba(20, 35, 58, 0.72);
        }

        .lp-home-scope .lp-card {
          border-color: rgba(186, 204, 227, 0.08);
          border-radius: 20px;
        }

        .lp-home-scope .lp-card + .lp-card {
          margin-top: 8px;
        }

        .lp-home-empty-copy {
          opacity: 0.76;
        }

        .lp-home-empty-btn {
          opacity: 0.9;
        }

        .lp-home-passive-empty {
          background: rgba(10, 18, 30, 0.56);
          border-color: rgba(186, 204, 227, 0.08);
          padding-top: 10px !important;
          padding-bottom: 10px !important;
        }

        .lp-home-path-empty {
          min-height: 160px;
          justify-content: center;
        }

        .lp-home-scope .q-btn {
          min-height: 35px !important;
          border-radius: 10px !important;
          font-size: 0.78rem !important;
          letter-spacing: 0.01em;
          font-weight: 600 !important;
          text-transform: none;
        }

        .lp-home-track-actions .q-btn {
          opacity: 0.88;
        }

        .lp-home-track-actions .q-btn:hover {
          opacity: 1;
        }

        .lp-home-track-status-select {
          min-width: 108px;
        }

        .lp-home-track-status-select .q-field__control {
          min-height: 32px !important;
        }

        .lp-home-row-overflow .q-btn {
          min-width: 26px !important;
          padding-left: 4px !important;
          padding-right: 4px !important;
          opacity: 0.84;
        }

        .lp-home-row-overflow .q-btn--outline {
          border-color: rgba(186, 204, 227, 0.14) !important;
        }

        .lp-home-row-overflow .q-btn-dropdown__arrow {
          display: none !important;
        }

        .lp-home-track-table {
          width: 100%;
          border: none;
          border-radius: 0;
          overflow: hidden;
          background: transparent;
        }

        .lp-home-track-head {
          padding: 8px 10px;
          border-bottom: 1px solid rgba(186, 204, 227, 0.11);
          color: rgba(206, 218, 233, 0.62);
          font-size: 0.68rem;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          font-weight: 500;
        }

        .lp-home-track-head-course { flex: 1 1 auto; min-width: 0; }
        .lp-home-track-head-status { width: 124px; }
        .lp-home-track-head-progress { width: 172px; text-align: right; }
        .lp-home-track-head-actions { width: 44px; }

        .lp-home-track-row {
          padding: 12px 12px;
          border: 1px solid rgba(186, 204, 227, 0.08);
          border-radius: 10px;
          background: rgba(11, 20, 34, 0.48);
          margin-bottom: 8px;
        }

        .lp-home-track-row:last-child {
          margin-bottom: 0;
        }

        .lp-home-convo-shell {
          padding: 16px 18px !important;
        }

        .lp-home-convo-row {
          padding: 11px 12px;
          border: 1px solid rgba(186, 204, 227, 0.08);
          border-radius: 12px;
          background: rgba(10, 20, 33, 0.22);
          margin-bottom: 8px;
          transition: border-color 140ms ease, background-color 140ms ease;
        }

        .lp-home-convo-row:last-child {
          margin-bottom: 0;
        }

        .lp-home-convo-row:hover {
          border-color: rgba(186, 204, 227, 0.2);
          background: rgba(13, 24, 39, 0.52);
        }

        .lp-home-convo-main {
          min-height: 42px;
        }

        .lp-home-convo-who {
          font-size: 0.84rem;
          font-weight: 600;
          letter-spacing: 0.01em;
          color: rgba(238, 243, 250, 0.95);
          line-height: 1.15;
        }

        .lp-home-convo-title {
          max-width: 64ch;
          font-size: 0.82rem;
          color: rgba(206, 219, 235, 0.84);
          line-height: 1.25;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
          overflow: hidden;
        }

        .lp-home-convo-time {
          font-size: 0.7rem;
          color: rgba(192, 206, 224, 0.66);
          letter-spacing: 0.015em;
          text-transform: lowercase;
          white-space: nowrap;
          margin-top: 1px;
        }

        .lp-home-convo-open {
          min-height: 26px !important;
          min-width: 54px !important;
          font-size: 0.74rem !important;
          letter-spacing: 0.01em !important;
          text-transform: none !important;
          color: rgba(179, 208, 236, 0.88) !important;
          opacity: 0.9;
        }

        .lp-home-track-col-course { flex: 1 1 auto; min-width: 0; }
        .lp-home-track-col-status { width: 124px; align-items: flex-start; }
        .lp-home-track-col-progress { width: 172px; align-items: stretch; }
        .lp-home-track-col-actions { width: 44px; align-items: flex-end; }

        .lp-home-status-dot {
          transform: translateY(1px);
        }

        .lp-home-track-status {
          color: rgba(220, 227, 238, 0.8);
        }

        .lp-home-status--active {
          color: rgba(129, 192, 250, 0.82);
        }

        .lp-home-status--done {
          color: rgba(74, 222, 172, 0.84);
        }

        .lp-home-status--idle {
          color: rgba(196, 208, 223, 0.78);
        }

        .lp-home-track-progress {
          margin-top: 0;
          opacity: 0.9;
          transition: opacity 140ms ease;
          height: 5px;
          width: 100%;
        }

        .lp-home-track-progress-value {
          align-self: center;
          margin-bottom: 0;
        }

        .lp-home-track-meta {
          opacity: 0.64;
          line-height: 1.25;
        }

        .lp-home-track-title {
          font-weight: 600;
        }

        .lp-home-track-separator {
          margin: 6px 0 10px;
          opacity: 0.16;
        }

        .lp-tracked-grid {
          width: 100%;
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 14px;
          align-items: stretch;
        }

        .lp-tracked-grid--single {
          grid-template-columns: 1fr;
        }

        .lp-track-card {
          display: block;
          width: 100%;
          min-width: 100%;
          flex: 0 0 auto;
          align-self: auto;
          box-sizing: border-box;
          padding: 13px 14px 11px;
          border-radius: 14px;
          border: 1px solid rgba(186, 204, 227, 0.08);
          background: rgba(10, 20, 33, 0.3);
          box-shadow: none;
          margin-bottom: 0;
          transition: border-color 140ms ease, background-color 140ms ease;
        }

        .lp-tracked-grid .lp-track-card {
          height: 100%;
          min-height: 124px;
        }

        .lp-track-card:hover {
          border-color: rgba(186, 204, 227, 0.13);
          background: rgba(12, 24, 39, 0.42);
        }

        .lp-track-card--primary {
          border-color: rgba(186, 204, 227, 0.1);
        }

        .lp-track-card--secondary {
          border-color: rgba(186, 204, 227, 0.08);
        }

        .lp-track-card--major {
          grid-column: span 1;
        }

        .lp-track-card--minor {
          grid-column: span 1;
        }

        .lp-home-path-shell .lp-path-card {
          width: 100% !important;
          min-width: 100% !important;
          flex: 0 0 auto !important;
          align-self: auto !important;
          display: block !important;
          height: auto !important;
          min-height: 0 !important;
          max-height: none !important;
          overflow: visible !important;
        }

        .lp-track-avatar {
          width: 24px;
          height: 24px;
          border-radius: 999px;
          border: 1px solid rgba(186, 204, 227, 0.18);
          background: rgba(11, 24, 42, 0.52);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          color: rgba(189, 213, 239, 0.92);
          font-size: 14px;
          padding: 4px;
        }

        .lp-track-title-block .text-sm {
          margin-bottom: 1px;
        }

        .lp-track-actions .q-btn {
          min-height: 28px !important;
        }

        .lp-track-identity {
          min-width: 0;
          flex: 1 1 auto;
        }

        .lp-track-head-row {
          display: grid !important;
          grid-template-columns: minmax(0, 1fr) auto;
          align-items: start;
          column-gap: 10px;
        }

        .lp-track-title-block {
          min-width: 0;
        }

        .lp-track-title {
          width: 100%;
          max-width: 100%;
          white-space: normal;
          overflow-wrap: anywhere;
          line-height: 1.2;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 2;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .lp-track-actions-group {
          border: none;
          border-radius: 0;
          padding: 0;
          background: transparent;
          flex: 0 0 auto;
          align-self: flex-start;
        }

        .lp-track-continue-btn {
          min-width: 96px !important;
        }

        .lp-track-actions-group .lp-home-row-overflow .q-btn {
          min-width: 32px !important;
          width: 32px !important;
          padding-left: 0 !important;
          padding-right: 0 !important;
        }

        .lp-track-progress-meta {
          margin-top: 4px;
          margin-bottom: 0;
        }

        .lp-track-progress-inline {
          margin-top: 0 !important;
        }

        .lp-track-status-line {
          margin-top: 0;
        }

        .lp-track-status-text {
          font-weight: 500;
        }

        .lp-home-path-shell {
          padding: 16px 18px 14px !important;
          margin-top: 0 !important;
        }

        .lp-home-path-empty-shell {
          display: flex;
          flex-direction: column;
          gap: 12px;
          padding-top: 0;
          min-height: 132px;
          justify-content: center;
        }

        .lp-home-secondary-shell {
          min-height: 0;
          padding: 14px 16px !important;
        }

        .lp-home-grid-footer .lp-home-recent-shell {
          padding-top: 4px !important;
        }

        .lp-home-path-separator {
          margin: 6px 0 10px;
          opacity: 0.24;
        }

        @media (max-width: 1080px) {
          .lp-home-workspace-grid {
            grid-template-columns: 1fr;
          }

          .lp-home-workspace-grid--balanced {
            grid-template-columns: 1fr;
          }

          .lp-home-main-grid--top,
          .lp-home-main-grid--middle {
            grid-template-columns: 1fr;
          }

          .lp-tracked-grid {
            grid-template-columns: 1fr;
          }
          .lp-catalog--explore .lp-explore-path-grid,
          .lp-catalog--explore .lp-explore-path-grid--pair,
          .lp-catalog--explore .lp-explore-path-grid--single {
            grid-template-columns: 1fr;
          }
          .lp-catalog--explore .lp-explore-row-card .row.no-wrap {
            flex-wrap: wrap;
          }
          .lp-catalog--explore .lp-explore-row-actions {
            width: 100%;
            justify-content: flex-start;
          }
          .lp-home-intro-steps {
            grid-template-columns: 1fr;
          }
          .lp-home-grid-12 {
            grid-template-columns: repeat(1, minmax(0, 1fr));
          }
          .lp-home-span-3,
          .lp-home-span-4,
          .lp-home-span-5,
          .lp-home-span-8,
          .lp-home-span-12 {
            grid-column: span 1;
          }
          .lp-home-stat-grid {
            grid-template-columns: repeat(1, minmax(0, 1fr));
          }

          .lp-home-focus-summary {
            grid-template-columns: 1fr;
          }
        }

        .lp-home-snapshot-shell,
        .lp-home-recent-shell,
        .lp-home-reco-shell {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          padding: 0 !important;
        }

        .lp-home-snapshot-separator,
        .lp-home-recent-separator,
        .lp-home-reco-separator,
        .lp-shared-separator {
          margin: 6px 0 10px;
          opacity: 0.22;
        }

        .lp-shared-card {
          border-color: rgba(186, 204, 227, 0.08);
          background: rgba(10, 20, 33, 0.22);
          box-shadow: none;
          margin-bottom: 8px;
          min-height: 0;
        }

        .lp-shared-meta-line {
          margin-top: 4px;
        }

        .lp-shared-tab-shell {
          align-items: flex-start;
        }

        .lp-shared-content-column {
          width: min(100%, 960px);
        }

        .lp-shared-summary-row {
          margin-top: -2px;
        }

        .lp-shared-summary-card {
          min-width: 148px;
          padding: 14px 16px !important;
          border-radius: 18px !important;
          background: rgba(23, 35, 52, 0.62) !important;
          box-shadow: none !important;
        }

        .lp-shared-summary-label {
          font-size: 0.8rem;
          color: rgba(220, 225, 235, 0.68);
        }

        .lp-shared-summary-value {
          font-family: var(--lp-font-display);
          font-size: 1.4rem;
          font-weight: 700;
          line-height: 1.1;
        }

        .lp-shared-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
          align-items: start;
        }

        .lp-shared-grid--single {
          grid-template-columns: minmax(0, 760px);
        }

        .lp-shared-actions {
          flex-wrap: wrap;
          justify-content: flex-end;
          max-width: 220px;
        }

        .lp-shared-primary-btn,
        .lp-shared-secondary-btn {
          min-width: 96px !important;
        }

        .lp-catalog--explore .lp-explore-header {
          padding-top: 2px;
          padding-bottom: 2px;
          gap: 6px;
        }

        .lp-catalog--explore .lp-explore-header-subtitle {
          max-width: 40rem;
          font-size: 1rem;
          opacity: 0.78;
        }

        .lp-catalog--explore .lp-explore-control-card {
          border: 1px solid rgba(186, 204, 227, 0.08);
          border-radius: 20px;
          padding: 16px 18px;
          background: rgba(14, 24, 38, 0.34);
          box-shadow: none;
        }

        .lp-catalog--explore .lp-explore-control-card .lp-topbar-search {
          min-width: 0;
        }

        .lp-catalog--explore .lp-explore-control-card .lp-topbar-search .q-field__control {
          background: rgba(9, 18, 30, 0.54);
          border-radius: 14px !important;
        }

        .lp-catalog--explore .lp-explore-control-card .lp-topbar-group--secondary {
          padding-left: 0;
          border-left: none;
        }

        .lp-catalog--explore .lp-explore-control-card .lp-topbar-meta {
          white-space: nowrap;
        }

        .lp-catalog--explore .lp-explore-section-block {
          border-top: none;
          margin-top: 6px;
          padding-top: 0;
        }

        .lp-catalog--explore .lp-explore-section-head {
          margin-bottom: 4px;
        }

        .lp-catalog--explore .lp-explore-results-list {
          gap: 12px;
        }

        .lp-catalog--explore .lp-explore-results-list-item {
          width: 100%;
        }

        .lp-catalog--explore .lp-explore-row-card {
          border: 1px solid rgba(186, 204, 227, 0.08) !important;
          border-radius: 18px !important;
          background: rgba(11, 20, 34, 0.28) !important;
          box-shadow: none !important;
          padding: 14px 16px !important;
        }

        .lp-catalog--explore .lp-explore-row-icon {
          width: 42px;
          height: 42px;
          border-radius: 999px;
          border: 1px solid rgba(186, 204, 227, 0.14);
          background: rgba(10, 19, 31, 0.5);
          color: rgba(175, 208, 241, 0.9);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex: 0 0 auto;
        }

        .lp-catalog--explore .lp-explore-row-thumb {
          width: 84px;
          height: 56px;
          border-radius: 14px;
          overflow: hidden;
          border: 1px solid rgba(186, 204, 227, 0.12);
          background: rgba(10, 19, 31, 0.44);
          flex: 0 0 auto;
        }

        .lp-catalog--explore .lp-explore-row-thumb .q-img,
        .lp-catalog--explore .lp-explore-row-thumb-img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          display: block;
        }

        .lp-catalog--explore .lp-explore-row-title {
          font-family: var(--lp-font-display);
          font-size: 1rem;
          font-weight: 600;
          line-height: 1.22;
          color: rgba(239, 244, 250, 0.96);
          max-width: 100%;
          white-space: normal;
          overflow-wrap: anywhere;
        }

        .lp-catalog--explore .lp-explore-row-subtitle {
          font-size: 0.86rem;
          color: rgba(205, 217, 232, 0.72);
          line-height: 1.2;
        }

        .lp-catalog--explore .lp-explore-row-meta {
          font-size: 0.82rem;
          color: rgba(185, 200, 219, 0.62);
          line-height: 1.2;
        }

        .lp-catalog--explore .lp-explore-row-actions {
          flex: 0 0 auto;
          min-width: 0;
        }

        .lp-catalog--explore .lp-explore-row-actions .q-btn {
          min-width: 112px !important;
        }

        .lp-catalog--explore .lp-explore-path-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 14px;
          align-items: start;
        }

        .lp-catalog--explore .lp-explore-path-grid--pair {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .lp-catalog--explore .lp-explore-path-grid--single {
          grid-template-columns: minmax(0, 360px);
        }

        .lp-catalog--explore .lp-explore-path-compact {
          border: 1px solid rgba(186, 204, 227, 0.08) !important;
          border-radius: 18px !important;
          background: rgba(11, 20, 34, 0.28) !important;
          box-shadow: none !important;
          padding: 16px !important;
          min-height: 180px;
        }

        .lp-catalog--explore .lp-explore-path-compact .q-btn {
          min-width: 112px !important;
        }

        .lp-share-scope {
          --lp-page-glow-1: rgba(88, 166, 232, 0.12);
          --lp-page-glow-2: rgba(45, 175, 150, 0.1);
        }

        .lp-share-header {
          margin-bottom: 2px;
        }

        .lp-share-surface {
          border-color: rgba(186, 204, 227, 0.11) !important;
          background:
            radial-gradient(120% 140% at 8% 0%, rgba(88, 166, 232, 0.08), transparent 58%),
            linear-gradient(150deg, rgba(16, 28, 44, 0.76), rgba(12, 22, 36, 0.7)) !important;
        }

        .lp-share-columns {
          gap: 24px !important;
        }

        .lp-share-form .q-separator {
          margin: 6px 0 8px;
          opacity: 0.28;
        }

        .lp-share-input .q-field__control {
          border-radius: 10px !important;
          background: rgba(255, 255, 255, 0.03);
          border-color: rgba(255, 255, 255, 0.08) !important;
        }

        .lp-share-input .q-field__native,
        .lp-share-input input,
        .lp-share-input textarea {
          color: rgba(255, 255, 255, 0.9) !important;
        }

        .lp-share-input.q-field--focused .q-field__control {
          border-color: rgba(106, 168, 255, 0.9) !important;
          box-shadow: 0 0 0 2px rgba(106, 168, 255, 0.2);
        }

        .lp-share-import-btn,
        .lp-share-publish-btn {
          min-width: 152px;
        }

        .lp-share-save-btn {
          min-width: 128px;
          opacity: 0.9;
        }

        .lp-share-preview-card {
          min-height: 220px;
          border-color: rgba(186, 204, 227, 0.1) !important;
          background:
            radial-gradient(120% 140% at 86% 8%, rgba(88, 166, 232, 0.08), transparent 56%),
            linear-gradient(150deg, rgba(13, 24, 39, 0.8), rgba(10, 19, 31, 0.72)) !important;
        }

        .lp-home-overview-shell,
        .lp-home-focus-shell,
        .lp-home-review-shell {
          border-radius: var(--lp-radius-md);
        }

        .lp-home-review-shell {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          padding: 2px 0 0 !important;
        }

        .lp-home-flat-section {
          padding: 2px 0 0;
        }

        .lp-home-activity-shell {
          border: none;
          border-radius: 0;
          background: transparent;
          padding: 2px 0 0;
        }

        .lp-home-activity-item {
          padding: 8px 0 9px;
          border-bottom: 1px solid rgba(186, 204, 227, 0.1);
        }

        .lp-home-activity-item:last-child {
          border-bottom: none;
        }

        .lp-home-live-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: rgba(116, 176, 228, 0.9);
          box-shadow: 0 0 0 0 rgba(116, 176, 228, 0.38);
          animation: lp-home-live-pulse 1.8s ease-out infinite;
          margin-left: 3px;
        }

        @keyframes lp-home-live-pulse {
          0% { box-shadow: 0 0 0 0 rgba(116, 176, 228, 0.38); }
          70% { box-shadow: 0 0 0 8px rgba(116, 176, 228, 0); }
          100% { box-shadow: 0 0 0 0 rgba(116, 176, 228, 0); }
        }

        .lp-profile-scope {
          --lp-page-accent-soft: rgba(88, 166, 232, 0.2);
        }

        .lp-profile-meta {
          opacity: 0.72;
        }

        .lp-profile-section-title {
          font-family: var(--lp-font-display);
          font-size: clamp(1.06rem, 1.3vw, 1.22rem);
          font-weight: 700;
          letter-spacing: 0.01em;
          margin-top: 2px;
        }

        .lp-profile-card-title {
          font-family: var(--lp-font-display);
          font-size: 0.98rem;
          font-weight: 700;
          letter-spacing: 0.01em;
          color: rgba(236, 242, 249, 0.95);
        }

        .lp-profile-card-subtitle {
          font-size: 0.8rem;
          color: rgba(204, 216, 231, 0.68);
          margin-top: 2px;
          margin-bottom: 10px;
        }

        .lp-profile-user-name {
          font-size: 1.18rem;
          font-weight: 700;
          letter-spacing: 0.01em;
          line-height: 1.2;
        }

        .lp-profile-muted {
          font-size: 0.82rem;
          color: rgba(204, 216, 231, 0.74);
        }

        .lp-profile-stat-line {
          font-size: 0.92rem;
          color: rgba(220, 228, 238, 0.88);
          line-height: 1.35;
        }

        .lp-profile-summary-card,
        .lp-profile-chart-card,
        .lp-profile-table-card {
          position: relative;
          overflow: hidden;
          border-color: rgba(186, 204, 227, 0.12);
          background: linear-gradient(160deg, rgba(18, 31, 50, 0.74), rgba(12, 23, 38, 0.68));
          box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
          padding: 14px 16px 12px !important;
        }

        .lp-profile-chart-card,
        .lp-profile-table-card {
          padding: 16px 18px 14px !important;
        }

        .lp-profile-summary-card::before,
        .lp-profile-chart-card::before,
        .lp-profile-table-card::before {
          content: "";
          position: absolute;
          top: 0;
          left: 16%;
          width: 68%;
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(182, 220, 255, 0.72), transparent);
          opacity: 0.92;
          pointer-events: none;
        }

        .lp-profile-head {
          margin-top: 2px;
          margin-bottom: 2px;
        }

        .lp-profile-summary-card {
          padding: 14px 16px !important;
        }

        .lp-profile-summary-rail {
          flex-wrap: wrap;
        }

        .lp-profile-summary-meta {
          min-width: 170px;
        }

        .lp-profile-avatar-img,
        .lp-profile-avatar-fallback {
          width: 60px;
          height: 60px;
          border-radius: 999px;
          border: 1px solid rgba(186, 204, 227, 0.26);
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }

        .lp-profile-avatar-img {
          object-fit: cover;
          background: rgba(18, 33, 52, 0.76);
        }

        .lp-profile-avatar-fallback {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-family: var(--lp-font-display);
          font-size: 1.72rem;
          font-weight: 700;
          color: rgba(233, 241, 250, 0.96);
          background:
            radial-gradient(120% 120% at 20% 14%, rgba(89, 166, 232, 0.32), transparent 58%),
            linear-gradient(145deg, rgba(38, 88, 184, 0.86), rgba(47, 141, 206, 0.76));
        }

        .lp-profile-mode-toggle {
          width: fit-content;
          max-width: 100%;
          padding: 4px;
          border-radius: 10px;
          border: 1px solid rgba(186, 204, 227, 0.16);
          background: rgba(11, 22, 36, 0.46);
          display: inline-flex;
          gap: 4px !important;
        }

        .lp-profile-mode-toggle .q-btn {
          margin: 0 !important;
          padding: 7px 14px !important;
          border-radius: 8px;
          min-width: 124px;
          min-height: 34px !important;
          justify-content: center !important;
          text-transform: none !important;
          letter-spacing: 0.01em !important;
          font-size: 0.84rem !important;
          font-weight: 600 !important;
          color: rgba(208, 220, 236, 0.82) !important;
          background: rgba(12, 24, 39, 0.36) !important;
          border: 1px solid transparent !important;
        }

        .lp-profile-mode-toggle .q-btn:hover {
          color: rgba(229, 238, 249, 0.92) !important;
          border-color: rgba(186, 204, 227, 0.2) !important;
          background: rgba(14, 27, 44, 0.48) !important;
        }

        .lp-profile-mode-toggle .q-btn--active {
          background: linear-gradient(160deg, rgba(70, 120, 196, 0.42), rgba(45, 87, 152, 0.32));
          box-shadow: inset 0 0 0 1px rgba(120, 178, 237, 0.32);
          color: rgba(236, 243, 250, 0.96) !important;
        }

        .lp-profile-metric-card {
          border-color: rgba(186, 204, 227, 0.14);
          background: linear-gradient(160deg, rgba(20, 34, 54, 0.78), rgba(12, 24, 39, 0.7));
          box-shadow: 0 8px 20px rgba(0, 0, 0, 0.16);
          padding: 12px 14px !important;
          min-height: 148px;
          transition: transform 140ms ease, box-shadow 160ms ease;
        }

        .lp-profile-metric-card:hover {
          transform: translateY(var(--lp-hover-lift));
          box-shadow: var(--lp-hover-shadow);
        }

        .lp-profile-metric-icon {
          color: rgba(156, 205, 247, 0.92);
          font-size: 1.02rem;
        }

        .lp-profile-metric-value {
          font-family: var(--lp-font-display);
          font-size: clamp(1.8rem, 2.4vw, 2.1rem);
          font-weight: 700;
          line-height: 1.1;
          margin-top: 6px;
          color: rgba(239, 244, 250, 0.97);
        }

        .lp-profile-team-table .q-table thead tr th:first-child,
        .lp-profile-team-table .q-table tbody tr td:first-child {
          min-width: 180px;
        }

        .lp-profile-team-table .q-table thead tr th {
          font-size: 0.76rem;
          letter-spacing: 0.02em;
          padding-top: 8px;
          padding-bottom: 8px;
        }

        .lp-profile-team-table .q-table tbody tr td {
          font-size: 0.84rem;
          padding-top: 10px;
          padding-bottom: 10px;
        }

        .lp-teams-subtitle {
          opacity: 0.8;
        }

        .lp-teams-header {
          padding-top: 6px;
          padding-bottom: 4px;
        }

        .lp-teams-header-subtitle {
          max-width: 46rem;
          opacity: 0.84;
        }

        .lp-teams-topbar {
          margin-top: 0;
          margin-bottom: 2px;
          min-height: 34px;
        }

        .lp-teams-overview-strip {
          border-color: rgba(186, 204, 227, 0.1);
          background:
            radial-gradient(120% 120% at 10% 6%, rgba(88, 166, 232, 0.1), transparent 58%),
            linear-gradient(160deg, rgba(17, 30, 48, 0.68), rgba(11, 23, 38, 0.6));
          box-shadow: 0 8px 18px rgba(0, 0, 0, 0.14);
          padding: 10px 12px !important;
        }

        .lp-teams-overview-title {
          font-family: var(--lp-font-display);
          font-size: 1.02rem;
          font-weight: 700;
          letter-spacing: 0.01em;
        }

        .lp-teams-overview-body {
          font-size: 0.86rem;
          color: rgba(206, 219, 235, 0.78);
        }

        .lp-teams-overview-actions {
          min-height: 0;
        }

        .lp-teams-tabs .q-radio__label {
          font-weight: 600;
          letter-spacing: 0.01em;
        }

        .lp-teams-refresh {
          opacity: 0.9;
        }

        .lp-teams-feed {
          margin-top: 2px;
        }

        .lp-teams-workspace-grid {
          width: 100%;
          display: grid;
          grid-template-columns: 220px minmax(260px, 0.72fr) minmax(0, 1.28fr);
          gap: 16px;
          align-items: start;
        }

        .lp-teams-sidebar {
          position: sticky;
          top: 82px;
          padding-top: 2px;
        }

        .lp-teams-sidebar-title {
          letter-spacing: 0.04em;
          text-transform: uppercase;
          color: var(--lp-muted);
          opacity: 0.84;
        }

        .lp-teams-side-nav {
          width: 100%;
        }

        .lp-teams-side-nav .q-radio {
          width: 100%;
          margin: 0 !important;
          padding: 6px 10px;
          border-radius: 10px;
          transition: background-color 140ms ease;
        }

        .lp-teams-side-nav .q-radio:hover {
          background: rgba(255, 255, 255, 0.03);
        }

        .lp-teams-side-nav .q-radio__label {
          font-weight: 600;
        }

        .lp-teams-side-link {
          justify-content: flex-start !important;
          padding-left: 8px !important;
          color: var(--lp-muted);
        }

        .lp-teams-shell {
          border-color: rgba(186, 204, 227, 0.1);
          background: linear-gradient(160deg, rgba(29, 41, 61, 0.44), rgba(18, 29, 46, 0.38));
          box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
          border-radius: 20px;
        }

        .lp-teams-list-shell {
          padding: 14px 16px 10px !important;
        }

        .lp-teams-workspace-shell {
          padding: 14px 18px 12px !important;
        }

        .lp-teams-empty-workspace {
          display: grid;
          grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
          gap: 18px;
          align-items: start;
          width: 100%;
          margin-top: 4px;
          margin-bottom: 10px;
        }

        .lp-teams-empty-main {
          min-height: 0;
          padding: 6px 0;
        }

        .lp-teams-empty-title {
          font-family: var(--lp-font-display);
          font-size: 1.12rem;
          font-weight: 600;
          letter-spacing: 0.01em;
        }

        .lp-teams-empty-copy {
          max-width: 36rem;
        }

        .lp-teams-empty-hints {
          display: grid;
          grid-template-columns: 1fr;
          gap: 10px;
        }

        .lp-teams-empty-hint {
          display: flex;
          gap: 10px;
          align-items: flex-start;
          padding: 12px 13px;
          border: 1px solid rgba(186, 204, 227, 0.08);
          border-radius: 16px;
          background: rgba(10, 19, 33, 0.22);
        }

        .lp-teams-empty-inbox {
          width: 100%;
          margin-top: 4px;
        }

        .lp-teams-list-title {
          letter-spacing: 0.01em;
        }

        .lp-teams-list-count {
          opacity: 0.78;
          font-weight: 600;
        }

        .lp-teams-list {
          border-top: 1px solid rgba(186, 204, 227, 0.08);
          margin-top: 2px;
        }

        .lp-teams-list-row {
          padding: 10px 4px;
          border-bottom: 1px solid rgba(186, 204, 227, 0.08);
          transition: background-color 120ms ease, transform 140ms ease, box-shadow 140ms ease;
        }

        .lp-teams-list-row:hover {
          background: rgba(255, 255, 255, 0.02);
          transform: translateY(var(--lp-hover-lift));
          box-shadow: var(--lp-hover-shadow);
        }

        .lp-teams-list-row--active {
          background: linear-gradient(145deg, rgba(54, 92, 136, 0.18), rgba(24, 44, 70, 0.1));
          box-shadow: inset 0 0 0 1px rgba(116, 176, 228, 0.2);
          border-radius: 10px;
          padding-left: 10px;
          padding-right: 10px;
        }

        .lp-teams-list-row-title {
          letter-spacing: 0.01em;
        }

        .lp-teams-list-row-meta {
          opacity: 0.82;
        }

        .lp-teams-list-row-preview {
          opacity: 0.64;
        }

        .lp-teams-open-link {
          color: var(--lp-primary-strong);
          opacity: 0.95;
          font-size: 0.84rem !important;
          font-weight: 600 !important;
          text-transform: none !important;
          letter-spacing: 0.01em !important;
        }

        .lp-teams-member-row {
          padding: 8px 0;
          border-bottom: 1px solid rgba(186, 204, 227, 0.1);
        }

        .lp-teams-member-row:last-child {
          border-bottom: none;
        }

        .lp-teams-workspace-title {
          letter-spacing: 0.01em;
          line-height: 1.12;
        }

        .lp-teams-workspace-meta {
          margin-top: 1px;
        }

        .lp-teams-activity-feed {
          max-height: 440px;
          overflow-y: auto;
          border-top: 1px solid rgba(186, 204, 227, 0.09);
          margin-top: 2px;
        }

        .lp-teams-feed-row {
          padding: 11px 4px;
          border-bottom: 1px solid rgba(186, 204, 227, 0.09);
          transition: background-color 140ms ease, transform 140ms ease, box-shadow 140ms ease;
        }

        .lp-teams-feed-row:hover {
          background: rgba(255, 255, 255, 0.02);
          transform: translateY(var(--lp-hover-lift));
          box-shadow: var(--lp-hover-shadow);
        }

        .lp-teams-workspace-shell .lp-empty-compact {
          border-color: rgba(186, 204, 227, 0.08) !important;
          background: rgba(8, 16, 30, 0.44) !important;
          box-shadow: none !important;
        }

        .lp-teams-feed-row-title {
          line-height: 1.28;
          font-weight: 500;
        }

        .lp-teams-feed-row-meta {
          opacity: 0.74;
        }

        .lp-teams-item {
          border-color: rgba(186, 204, 227, 0.1);
          background: linear-gradient(160deg, rgba(29, 41, 61, 0.56), rgba(18, 29, 46, 0.5));
          box-shadow: 0 3px 8px rgba(0, 0, 0, 0.13);
        }

        .lp-teams-item-head {
          align-items: flex-start;
        }

        .lp-teams-item-title {
          font-weight: 600;
        }

        .lp-teams-item-time {
          opacity: 0.75;
        }

        .lp-teams-item-meta {
          opacity: 0.74;
        }

        .lp-teams-open-btn {
          min-width: 86px;
        }

        .lp-home-focus-separator,
        .lp-home-review-separator {
          margin: 4px 0 6px;
          opacity: 0.28;
        }

        .lp-home-review-table .lp-home-track-row {
          padding-top: 8px;
          padding-bottom: 8px;
        }

        .lp-home-snapshot-table .lp-home-track-row {
          padding-top: 8px;
          padding-bottom: 8px;
        }

        .lp-home-track-row {
          transition: background-color 140ms ease, transform 140ms ease, box-shadow 140ms ease;
        }

        .lp-home-track-row:hover {
          background: rgba(255, 255, 255, 0.03);
          transform: translateY(-1px);
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.14);
        }

        .lp-home-track-row:hover .lp-home-track-progress {
          opacity: 1;
        }

        .lp-home-track-row:hover .lp-home-row-overflow .q-btn {
          opacity: 1;
        }

        @media (max-width: 920px) {
          .lp-home-track-head-status,
          .lp-home-track-col-status {
            width: 108px;
          }

          .lp-home-track-head-progress,
          .lp-home-track-col-progress {
            width: 132px;
          }
        }

        @media (max-width: 1100px) {
          .lp-home-row-grid {
            grid-template-columns: 1fr;
          }

          .lp-teams-workspace-grid {
            grid-template-columns: 1fr;
          }

          .lp-teams-empty-workspace {
            grid-template-columns: 1fr;
          }

          .lp-home-row-grid--social {
            grid-template-columns: 1fr;
          }

          .lp-home-overview-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

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
          background: rgba(255, 255, 255, 0.014) !important;
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

        .lp-transition-field .q-field__control,
        .lp-transition-field .q-field__native,
        .lp-transition-field .q-select__dropdown-icon,
        .lp-topbar .q-btn,
        .lp-topbar .q-radio {
          transition: background-color 140ms ease, border-color 140ms ease, color 140ms ease, box-shadow 140ms ease,
            transform 140ms ease;
        }

        .lp-refresh-region > * {
          animation: lp-refresh-fade 200ms ease both;
        }

        .lp-refresh-region > *:nth-child(2) {
          animation-delay: 24ms;
        }

        .lp-refresh-region > *:nth-child(3) {
          animation-delay: 48ms;
        }

        .lp-refresh-region > *:nth-child(4) {
          animation-delay: 72ms;
        }

        .lp-refresh-region > *:nth-child(5) {
          animation-delay: 96ms;
        }

        .lp-refresh-region > *:nth-child(6) {
          animation-delay: 120ms;
        }

        @keyframes lp-refresh-fade {
          from {
            opacity: 0;
            transform: translateY(4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes lp-drawer-slide-in {
          from {
            opacity: 0;
            transform: translateX(10px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .lp-explore-detail {
          --lp-max-content: 1380px;
        }

        .lp-explore-detail-breadcrumb {
          color: var(--lp-muted);
          opacity: 0.92;
        }

        .lp-explore-detail-breadcrumb a {
          color: rgba(212, 226, 243, 0.86);
          text-decoration: none;
        }

        .lp-explore-detail-main {
          flex: 1 1 0%;
          min-width: 0;
          gap: 12px;
          padding: 14px 16px 8px;
          border-radius: var(--lp-radius-md);
          border: 1px solid var(--lp-border-soft);
          background:
            linear-gradient(180deg, rgba(18, 30, 48, 0.72), rgba(12, 22, 38, 0.64)),
            radial-gradient(720px 360px at 24% -12%, rgba(124, 184, 235, 0.12), transparent 60%);
          box-shadow: var(--lp-shadow-sm);
        }

        .lp-explore-detail-hero {
          padding: 4px 0 6px;
          border-bottom: 1px solid rgba(186, 204, 227, 0.1);
          margin-bottom: 0;
        }

        .lp-explore-detail-eyebrow {
          font-size: var(--lp-type-xs);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          font-weight: 700;
          color: color-mix(in srgb, var(--lp-page-accent-strong) 74%, rgba(220, 225, 235, 0.92));
        }

        .lp-explore-rating-stars {
          letter-spacing: 0.03em;
          color: rgba(255, 206, 110, 0.94);
          font-weight: 700;
        }

        .lp-explore-rating-score {
          font-size: var(--lp-type-sm);
          font-weight: 600;
          color: rgba(235, 241, 249, 0.92);
        }

        .lp-explore-detail-card {
          border-radius: 12px;
          border: 1px solid rgba(186, 204, 227, 0.13);
          background: linear-gradient(160deg, rgba(18, 30, 47, 0.64), rgba(11, 22, 36, 0.58));
          box-shadow: 0 8px 18px rgba(0, 0, 0, 0.2);
        }

        .lp-explore-reviews-grid {
          display: grid;
          grid-template-columns: minmax(0, 0.75fr) minmax(0, 1.25fr);
          gap: 12px;
          width: 100%;
        }

        .lp-explore-reviews-summary {
          min-height: 164px;
        }

        .lp-explore-reviews-panel {
          min-height: 0;
          padding-top: 14px;
          padding-bottom: 14px;
        }

        .lp-explore-info-card {
          border-color: rgba(186, 204, 227, 0.15);
          background: linear-gradient(165deg, rgba(11, 24, 40, 0.78), rgba(8, 19, 31, 0.7));
          box-shadow: 0 7px 18px rgba(0, 0, 0, 0.18);
        }

        .lp-explore-info-card .text-base.font-semibold {
          letter-spacing: 0.015em;
          margin-bottom: 2px;
        }

        .lp-explore-info-card .lp-explore-detail-muted {
          margin-top: -2px;
          margin-bottom: 2px;
        }

        .lp-explore-info-card .q-btn {
          width: 100%;
          min-height: 36px !important;
          border-radius: 10px !important;
          justify-content: center;
          text-align: center;
          padding-left: 12px !important;
          padding-right: 12px !important;
          font-size: 0.8rem !important;
          letter-spacing: 0.015em;
        }

        .lp-explore-info-card .q-btn .q-icon {
          margin-right: 6px;
        }

        .lp-explore-info-card .q-btn--flat {
          opacity: 0.9;
        }

        .lp-explore-info-card .q-btn--standard {
          box-shadow: 0 8px 18px rgba(72, 142, 203, 0.24) !important;
        }

        .lp-explore-info-card .q-separator {
          margin: 4px 0;
          opacity: 0.32;
        }

        .lp-explore-detail-side {
          flex: 0 0 288px;
          gap: 10px;
          padding: 14px;
          border-radius: var(--lp-radius-md);
          border: 1px solid var(--lp-border-soft);
          background: rgba(9, 18, 32, 0.64);
          box-shadow: var(--lp-shadow-sm);
        }

        .lp-explore-detail-title {
          font-family: var(--lp-font-display);
          font-size: clamp(1.42rem, 2.1vw, 2.06rem);
          font-weight: 700;
          letter-spacing: 0.01em;
          line-height: 1.1;
        }

        .lp-explore-detail-body {
          font-size: var(--lp-type-sm);
          color: rgba(222, 230, 242, 0.88);
          line-height: 1.55;
          max-width: 78ch;
        }

        .lp-explore-detail-muted {
          font-size: var(--lp-type-xs);
          color: var(--lp-muted);
          line-height: 1.5;
        }

        .lp-explore-detail-meta-row {
          margin-top: -2px;
          margin-bottom: -1px;
        }

        .lp-explore-main-surface {
          padding: 12px 14px;
        }

        .lp-explore-main-surface .text-base.font-semibold {
          letter-spacing: 0.012em;
          margin-bottom: 1px;
        }

        .lp-explore-main-surface .lp-explore-detail-muted {
          margin-top: 1px;
        }

        .lp-explore-main-surface .q-separator {
          margin: 4px 0;
          opacity: 0.3;
        }

        .lp-explore-reviews-panel .lp-review-panel-title {
          margin-top: 2px;
          margin-bottom: 2px;
          letter-spacing: 0.01em;
        }

        .lp-explore-reviews-panel .lp-review-entry {
          border-radius: 16px;
          border-color: rgba(186, 204, 227, 0.11);
          background: linear-gradient(160deg, rgba(26, 38, 58, 0.58), rgba(17, 29, 47, 0.5));
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
          padding: 12px 14px 10px !important;
        }

        .lp-explore-reviews-panel .lp-review-entry-title {
          letter-spacing: 0.01em;
        }

        .lp-explore-reviews-panel .lp-review-entry-date {
          margin-top: 1px;
          margin-bottom: 3px;
        }

        .lp-explore-reviews-panel .lp-review-entry-body {
          line-height: 1.5;
        }

        .lp-explore-reviews-panel .lp-review-form-title {
          margin-top: 8px;
          margin-bottom: 2px;
        }

        .lp-explore-reviews-panel .lp-review-rating {
          max-width: 132px;
        }

        .lp-explore-reviews-panel .lp-review-rating .q-field__control,
        .lp-explore-reviews-panel .lp-review-text .q-field__control {
          background: rgba(10, 18, 31, 0.34);
          border-radius: 10px;
        }

        .lp-explore-reviews-panel .lp-review-text {
          margin-top: 4px;
        }

        .lp-explore-reviews-panel .lp-review-actions {
          margin-top: 4px;
        }

        .lp-explore-reviews-panel .lp-review-save {
          min-width: 136px;
        }

        .lp-path-sequence-card .lp-path-sequence-item {
          border: 1px solid rgba(186, 204, 227, 0.14);
          border-radius: 10px;
          padding: 10px 12px;
          background: linear-gradient(155deg, rgba(17, 30, 47, 0.56), rgba(11, 22, 36, 0.5));
          min-height: 114px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
        }

        .lp-path-sequence-card .q-linear-progress {
          margin-top: 6px;
        }

        .lp-path-sequence-card .lp-path-sequence-item .q-btn {
          min-width: 168px !important;
          justify-content: center !important;
        }

        @media (max-width: 1040px) {
          .lp-explore-detail-side {
            flex-basis: 100%;
          }
          .lp-explore-reviews-grid {
            grid-template-columns: minmax(0, 1fr);
          }
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
