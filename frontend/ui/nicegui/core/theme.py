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
          --lp-primary-shadow: rgba(88, 166, 232, 0.32);
          --lp-success: #34d399;
          --lp-warning: #fbbf24;
          --lp-danger: #fb7185;
          --lp-page-accent: var(--lp-primary);
          --lp-page-accent-strong: var(--lp-primary-strong);
          --lp-page-accent-soft: rgba(88, 166, 232, 0.24);
          --lp-page-glow-1: rgba(88, 166, 232, 0.16);
          --lp-page-glow-2: rgba(52, 211, 153, 0.1);
          --lp-page-surface: rgba(16, 25, 40, 0.82);
          --lp-section-title: rgba(220, 225, 235, 0.86);

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
          inset: -22px -16px;
          z-index: -1;
          pointer-events: none;
          border-radius: 28px;
          background:
            radial-gradient(780px 420px at 8% 14%, var(--lp-page-glow-1), transparent 58%),
            radial-gradient(700px 360px at 88% 26%, var(--lp-page-glow-2), transparent 62%);
          opacity: 0.95;
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
          background:
            radial-gradient(130% 130% at 8% 8%, color-mix(in srgb, var(--lp-page-accent-soft) 76%, transparent), transparent 58%),
            linear-gradient(145deg, rgba(17, 28, 44, 0.84), rgba(14, 24, 39, 0.76));
          box-shadow: var(--lp-shadow-sm);
        }

        .lp-catalog-hero::after {
          content: "";
          position: absolute;
          inset: 0;
          pointer-events: none;
          background: linear-gradient(
            110deg,
            rgba(255, 255, 255, 0.07) 0%,
            rgba(255, 255, 255, 0.02) 24%,
            transparent 44%,
            transparent 100%
          );
          opacity: 0.5;
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
          background: linear-gradient(180deg, rgba(16, 25, 40, 0.9), rgba(15, 24, 39, 0.78));
          border: 1px solid rgba(186, 204, 227, 0.12);
          border-radius: 20px;
          backdrop-filter: blur(10px);
          box-shadow: var(--lp-shadow-sm);
        }

        .lp-catalog-scope .lp-sticky-controls {
          background:
            radial-gradient(120% 130% at 6% 10%, var(--lp-page-accent-soft), transparent 58%),
            linear-gradient(180deg, rgba(16, 25, 40, 0.9), rgba(15, 24, 39, 0.78));
          border-color: color-mix(in srgb, var(--lp-page-accent-soft) 55%, rgba(186, 204, 227, 0.12));
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
          background: rgba(15, 24, 39, 0.46);
          border: 1px solid rgba(186, 204, 227, 0.075);
          border-radius: 22px;
          backdrop-filter: blur(8px);
          box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
        }

        .lp-catalog-scope .lp-rail {
          background:
            radial-gradient(140% 140% at 10% 8%, color-mix(in srgb, var(--lp-page-accent-soft) 32%, transparent), transparent 64%),
            rgba(15, 24, 39, 0.46);
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
          grid-auto-columns: minmax(212px, 212px);
          justify-content: start;
          align-content: start;
          gap: 10px;
          overflow-x: auto;
          overflow-y: hidden;
          scroll-snap-type: x mandatory;
          padding: 4px 2px 12px;
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
        }

        .lp-catalog--explore .lp-courses-grid-item--featured {
          grid-column: auto;
          width: 212px;
          flex: 0 0 212px;
        }

        .lp-catalog--explore .lp-course-card,
        .lp-catalog--explore .lp-path-card,
        .lp-catalog--explore .lp-article-card {
          width: 212px;
          min-height: 258px;
          border-radius: 12px;
          overflow: hidden;
          border: none !important;
          box-shadow: 0 7px 20px rgba(0, 0, 0, 0.34);
          transition: transform 160ms ease, box-shadow 180ms ease;
        }

        .lp-catalog--explore .lp-course-card--surface,
        .lp-catalog--explore .lp-accent-card {
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
          transform: translateY(-3px);
          box-shadow: 0 14px 40px rgba(0, 0, 0, 0.45);
          z-index: 5;
        }

        .lp-catalog--explore .lp-card-title {
          font-size: 0.94rem;
          line-height: 1.22;
          padding-right: 0;
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
        }

        .lp-catalog--explore .lp-course-card-content,
        .lp-catalog--explore .lp-article-card-content {
          order: 2;
          padding-right: 0;
          display: flex;
          flex-direction: column;
          min-height: 120px;
        }

        .lp-catalog--explore .lp-path-card .lp-card-content {
          display: flex;
          flex-direction: column;
          min-height: 120px;
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
          height: 108px;
          border-radius: 9px;
          object-fit: cover;
          border: none;
          box-shadow: none;
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

        .lp-catalog--explore .lp-social-strip,
        .lp-catalog--explore .lp-card-subtitle {
          font-size: 0.74rem;
          opacity: 0.68;
        }

        .lp-catalog--explore .lp-course-card .lp-social-strip {
          min-height: 18px;
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

        .lp-catalog--explore .lp-course-context-line {
          display: block;
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

        .lp-catalog--explore .lp-path-card .lp-path-context-line {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .lp-catalog--explore .lp-path-card .lp-path-next-line {
          display: none;
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

        .lp-catalog--explore .lp-card-actions {
          margin-top: auto;
          min-height: 34px;
        }

        .lp-catalog--explore .lp-card-actions .q-btn {
          border-radius: 10px;
          min-height: 30px !important;
          padding: 4px 10px !important;
          font-size: 0.75rem !important;
          letter-spacing: 0.01em;
        }

        .lp-catalog--explore .lp-card-actions .lp-status-select,
        .lp-catalog--explore .lp-path-card .lp-card-actions .q-btn:nth-child(2) {
          display: none !important;
        }

        .lp-catalog--explore .lp-card-actions .q-btn--standard {
          background: #4f86c6 !important;
          color: #eef6ff !important;
          box-shadow: none !important;
        }

        .lp-catalog--explore .lp-card-actions .q-btn--standard:hover {
          background: #5c8fd8 !important;
          box-shadow: 0 8px 16px rgba(51, 98, 156, 0.34) !important;
        }

        .lp-catalog--explore .lp-explore-spotlight-strip .q-btn--standard,
        .lp-catalog--explore .lp-topbar .q-btn--standard {
          background: #4f86c6 !important;
          color: #eef6ff !important;
          box-shadow: none !important;
        }

        .lp-catalog--explore .lp-explore-spotlight-strip .q-btn--standard:hover,
        .lp-catalog--explore .lp-topbar .q-btn--standard:hover {
          background: #5c8fd8 !important;
          box-shadow: 0 8px 16px rgba(51, 98, 156, 0.34) !important;
        }

        .lp-catalog--explore .lp-card-actions .q-btn--outline {
          background: rgba(255, 255, 255, 0.04) !important;
          border-color: rgba(186, 204, 227, 0.16) !important;
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
          margin: 2px 0 6px;
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
          margin: 0 0 8px;
          padding: 8px 10px;
          background: linear-gradient(180deg, rgba(12, 21, 35, 0.68), rgba(11, 20, 33, 0.52));
          border-color: rgba(186, 204, 227, 0.08);
          box-shadow: 0 10px 28px rgba(0, 0, 0, 0.26);
        }

        .lp-catalog--explore .lp-topbar-group--secondary {
          opacity: 0.84;
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
          box-shadow: var(--lp-shadow-sm);
        }

        .lp-catalog--articles .lp-card {
          background:
            radial-gradient(110% 92% at 88% 10%, var(--lp-page-glow-1), transparent 62%),
            linear-gradient(145deg, rgba(20, 34, 46, 0.78), rgba(15, 26, 36, 0.74)) !important;
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
          background:
            radial-gradient(120% 96% at 88% 10%, var(--lp-page-glow-1), transparent 62%),
            linear-gradient(145deg, rgba(16, 35, 42, 0.8), rgba(13, 27, 32, 0.76)) !important;
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
            radial-gradient(110% 85% at 82% 6%, var(--lp-page-glow-1), transparent 62%),
            radial-gradient(120% 90% at 8% 100%, var(--lp-page-glow-2), transparent 68%),
            linear-gradient(140deg, rgba(24, 35, 52, 0.76), var(--lp-page-surface));
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
          background: linear-gradient(180deg, var(--lp-primary-strong), var(--lp-primary)) !important;
          color: #f8fbff !important;
        }

        .q-btn--standard:hover {
          box-shadow: 0 8px 20px var(--lp-primary-shadow);
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

        .lp-courses-filter-drawer {
          width: min(92vw, 360px);
          min-height: 72vh;
          border-radius: 18px !important;
          display: flex;
          flex-direction: column;
          gap: var(--lp-space-3);
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

        .lp-home-scope {
          --lp-page-accent-soft: rgba(88, 166, 232, 0.22);
          --lp-page-glow-1: rgba(88, 166, 232, 0.13);
          --lp-page-glow-2: rgba(45, 175, 150, 0.12);
        }

        .lp-home-title {
          font-family: var(--lp-font-display);
          font-size: clamp(1.44rem, 2.05vw, 1.88rem);
          font-weight: 700;
          letter-spacing: 0.01em;
          line-height: 1.15;
        }

        .lp-home-topbar {
          margin-top: 4px;
        }

        .lp-home-topbar-prompt {
          font-size: var(--lp-type-sm);
          color: rgba(220, 225, 235, 0.8);
          font-weight: 500;
          letter-spacing: 0.02em;
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

        .lp-home-row-grid--primary {
          grid-template-columns: minmax(0, 1fr) 340px;
        }

        .lp-home-row-grid--single {
          grid-template-columns: minmax(0, 1fr);
        }

        .lp-home-row-grid--social {
          grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
        }

        .lp-home-row-grid--balanced {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .lp-home-hero-panel {
          border-color: rgba(186, 204, 227, 0.12);
          border-left: 2px solid rgba(116, 176, 228, 0.52);
          background: linear-gradient(160deg, rgba(17, 28, 46, 0.72), rgba(13, 22, 36, 0.64));
          box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
        }

        .lp-home-hero-eyebrow {
          font-size: var(--lp-type-xs);
          letter-spacing: 0.05em;
          text-transform: uppercase;
          color: rgba(156, 205, 247, 0.92);
          font-weight: 700;
        }

        .lp-home-hero-heading {
          font-family: var(--lp-font-display);
          font-size: clamp(1.08rem, 1.6vw, 1.3rem);
          font-weight: 600;
          line-height: 1.2;
        }

        .lp-home-hero-meta {
          color: var(--lp-muted);
          font-size: var(--lp-type-xs);
          opacity: 0.78;
        }

        .lp-home-hero-focus {
          border: 1px solid rgba(186, 204, 227, 0.17);
          background: rgba(7, 16, 32, 0.44);
        }

        .lp-home-snapshot-panel .grid {
          grid-template-columns: repeat(1, minmax(0, 1fr));
        }

        .lp-home-stat-card {
          border-color: rgba(186, 204, 227, 0.14) !important;
          background: rgba(8, 16, 30, 0.64);
        }

        .lp-home-section-title {
          font-family: var(--lp-font-display);
          font-size: var(--lp-type-md);
          font-weight: 600;
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
          border-color: rgba(186, 204, 227, 0.12);
          border-radius: var(--lp-radius-md);
        }

        .lp-home-scope .lp-card + .lp-card {
          margin-top: 4px;
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

        .lp-home-scope .q-btn {
          min-height: 33px !important;
          border-radius: 10px !important;
          font-size: 0.76rem !important;
          letter-spacing: 0.03em;
          font-weight: 600 !important;
          text-transform: uppercase;
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
          opacity: 0.68;
        }

        .lp-home-track-title {
          font-weight: 600;
        }

        .lp-home-track-shell {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          padding: 2px 0 0 !important;
        }

        .lp-home-track-separator {
          margin: 2px 0 4px;
          opacity: 0.26;
        }

        .lp-tracked-grid {
          width: 100%;
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
          align-items: stretch;
        }

        .lp-track-card {
          display: block;
          width: 100%;
          min-width: 100%;
          flex: 0 0 auto;
          align-self: auto;
          box-sizing: border-box;
          padding: 11px 12px 9px;
          border-radius: 12px;
          border: 1px solid rgba(186, 204, 227, 0.08);
          background: linear-gradient(160deg, rgba(32, 45, 67, 0.6), rgba(19, 30, 48, 0.52));
          box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
          margin-bottom: 12px;
          transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
        }

        .lp-tracked-grid .lp-track-card {
          height: 100%;
          min-height: 136px;
        }

        .lp-track-card:hover {
          transform: translateY(-1px);
          box-shadow: 0 6px 14px rgba(0, 0, 0, 0.18);
          border-color: rgba(186, 204, 227, 0.13);
        }

        .lp-track-card--primary {
          padding-top: 13px;
          padding-bottom: 10px;
          border-color: rgba(186, 204, 227, 0.12);
          background: linear-gradient(160deg, rgba(37, 50, 73, 0.66), rgba(22, 34, 54, 0.58));
          box-shadow: 0 6px 14px rgba(0, 0, 0, 0.16);
        }

        .lp-track-card--secondary {
          border-color: rgba(186, 204, 227, 0.07);
          background: linear-gradient(160deg, rgba(30, 42, 63, 0.54), rgba(18, 29, 46, 0.48));
          box-shadow: 0 2px 6px rgba(0, 0, 0, 0.11);
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

        .lp-home-path-shell .lp-path-card--primary {
          border-color: rgba(186, 204, 227, 0.11);
          background: linear-gradient(160deg, rgba(35, 48, 69, 0.6), rgba(20, 32, 50, 0.52));
          box-shadow: 0 4px 10px rgba(0, 0, 0, 0.13);
        }

        .lp-home-path-shell .lp-path-card--secondary {
          border-color: rgba(186, 204, 227, 0.07);
          background: linear-gradient(160deg, rgba(29, 41, 61, 0.52), rgba(17, 28, 44, 0.46));
          box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        }

        .lp-track-avatar {
          width: 24px;
          height: 24px;
          border-radius: 999px;
          border: 1px solid rgba(186, 204, 227, 0.24);
          background: rgba(11, 24, 42, 0.8);
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

        .lp-track-title {
          width: 100%;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .lp-track-actions-group {
          border: 1px solid rgba(186, 204, 227, 0.12);
          border-radius: 11px;
          padding: 2px;
          background: rgba(11, 23, 40, 0.38);
          flex: 0 0 auto;
          align-self: flex-start;
        }

        .lp-track-continue-btn {
          min-width: 100px !important;
        }

        .lp-track-actions-group .lp-home-row-overflow .q-btn {
          min-width: 34px !important;
          width: 34px !important;
          padding-left: 0 !important;
          padding-right: 0 !important;
        }

        .lp-track-social-line {
          margin-top: 1px;
          margin-bottom: 2px;
        }

        .lp-track-progress-meta {
          margin-top: 1px;
          margin-bottom: 1px;
        }

        .lp-track-progress-inline {
          margin-top: 0 !important;
        }

        .lp-track-status-line {
          margin-top: -2px;
        }

        .lp-track-status-text {
          font-weight: 500;
        }

        .lp-home-path-shell {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          padding: 2px 0 0 !important;
          margin-top: 0 !important;
        }

        .lp-home-path-separator {
          margin: 2px 0 4px;
          opacity: 0.26;
        }

        @media (max-width: 1080px) {
          .lp-tracked-grid {
            grid-template-columns: 1fr;
          }
        }

        .lp-home-snapshot-shell,
        .lp-home-recent-shell,
        .lp-home-reco-shell,
        .lp-shared-shell {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          padding: 2px 0 0 !important;
        }

        .lp-home-snapshot-separator,
        .lp-home-recent-separator,
        .lp-home-reco-separator,
        .lp-shared-separator {
          margin: 2px 0 4px;
          opacity: 0.28;
        }

        .lp-shared-card {
          border-color: rgba(186, 204, 227, 0.08);
          background: linear-gradient(160deg, rgba(28, 40, 60, 0.52), rgba(17, 28, 44, 0.46));
          box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
          margin-bottom: 8px;
        }

        .lp-shared-meta-line {
          margin-top: 2px;
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
          gap: 10px;
          padding: 14px 16px 8px;
          border-radius: var(--lp-radius-md);
          border: 1px solid var(--lp-border-soft);
          background:
            linear-gradient(180deg, rgba(18, 30, 48, 0.72), rgba(12, 22, 38, 0.64)),
            radial-gradient(720px 360px at 24% -12%, rgba(124, 184, 235, 0.12), transparent 60%);
          box-shadow: var(--lp-shadow-sm);
        }

        .lp-explore-detail-side {
          flex: 0 0 300px;
          gap: 10px;
          padding: 14px;
          border-radius: var(--lp-radius-md);
          border: 1px solid var(--lp-border-soft);
          background: rgba(9, 18, 32, 0.72);
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
        }

        .lp-explore-detail-muted {
          font-size: var(--lp-type-xs);
          color: var(--lp-muted);
          line-height: 1.5;
        }

        @media (max-width: 1040px) {
          .lp-explore-detail-side {
            flex-basis: 100%;
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
