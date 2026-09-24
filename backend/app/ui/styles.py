"""Design tokens + component styling, ported verbatim from the frontend's
`src/index.css` (Tailwind v4 `@theme` block) - see doc/design-tokens.md.
NiceGUI ships Tailwind by default (`ui.run_with(..., tailwind=True)`), so
the same utility classes used in the former JSX (`rounded-card`,
`bg-panel`, `text-subtext`, ...) work unchanged against `.classes(...)`
once these custom properties are registered the same way Tailwind v4's
`@theme` block registers them.

Responsive layout: the mobile layout comes from screen width (Tailwind's
`md` breakpoint, 768px), not from user-agent sniffing. Watch out when
hiding a NiceGUI container: `nicegui.css` sets `display: flex` on
`.nicegui-row`/`.nicegui-column` *unlayered*, which beats Tailwind's
layered `hidden` - use the important modifier (`max-md:hidden!`) there.
"""

from nicegui import ui

CSS = """
@theme {
  --color-bg: oklch(0.975 0.012 75);
  --color-panel: oklch(0.995 0.004 75);
  --color-panel-2: oklch(0.95 0.015 75);
  --color-text: oklch(0.27 0.02 55);
  --color-subtext: oklch(0.52 0.02 55);
  --color-border: oklch(0.9 0.015 70);
  --color-accent: oklch(0.58 0.15 250);
  --color-accent-soft: oklch(0.58 0.15 250 / 0.14);
  --color-accent-text: oklch(0.99 0.005 75);
  --color-flag: oklch(0.55 0.15 40);
  --color-flag-bg: oklch(0.55 0.15 40 / 0.12);
  --color-ai-bubble: oklch(0.95 0.035 235);

  --radius-card: 18px;
  --radius-control: 10px;

  --shadow-card: 0 6px 18px oklch(0.4 0.02 60 / 0.12);

  --animate-fade-in: cf-fade-in 0.4s ease-out;
  --animate-flash: cf-flash 1.6s ease-out;
}

@keyframes cf-fade-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes cf-flash {
  0% {
    background-color: var(--color-accent-soft);
  }
  100% {
    background-color: transparent;
  }
}

body {
  margin: 0;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  background: var(--color-bg);
}

/* NiceGUI wraps page content in its own root elements - match the
   full-height, no-default-padding layout the React app's <div
   className="h-screen w-full ..."> relied on. */
.nicegui-content {
  padding: 0;
  height: 100dvh;
}

/* Mobile (below Tailwind's `md` breakpoint). iOS Safari zooms the whole
   page when a focused input's font is under 16px - pin every form control
   to 16px there instead of each component's desktop 13px. */
@media (max-width: 767.98px) {
  input,
  textarea,
  select {
    font-size: 16px !important;
  }

  /* Opt-in (`.classes("dialog-mobile-full")` on a `ui.dialog`): the
     dialog covers the whole screen instead of floating with Quasar's
     24px inset and 560px max-width. */
  .dialog-mobile-full .q-dialog__inner--minimized {
    padding: 0;
  }
  .dialog-mobile-full .q-dialog__inner--minimized > div {
    width: 100vw;
    max-width: 100vw;
    height: 100dvh;
    max-height: 100dvh;
    border-radius: 0;
    border: 0;
  }
}

/* Touch screens: 44px minimum tap targets (Apple HIG / WCAG 2.5.5), and
   hover-only affordances made permanently visible. */
@media (pointer: coarse) {
  .q-btn {
    min-height: 44px;
  }
  .touch-underline {
    text-decoration: underline;
  }
}
"""


def register_styles() -> None:
    """Injects the design-token stylesheet once, shared across the app.

    Call this before building any page content (see `app/ui/pages.py`) -
    it only needs to run once per process, not once per connection.
    """
    ui.add_head_html(f'<style type="text/tailwindcss">{CSS}</style>')
