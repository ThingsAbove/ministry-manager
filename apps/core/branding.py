"""Default church branding (Be Renewed Church demo)."""

DEFAULT_BRANDING_CSS = """\
@import url("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Open+Sans:wght@400;500;600&display=swap");

:root {
  --mm-brand: #332f2e;
  --mm-brand-dark: #262322;
  --mm-brand-muted: #5c5654;
  --mm-brand-accent: #c9b8a8;
  --mm-brand-bg: #faf8f6;
  --mm-brand-surface: #ffffff;
}

body {
  font-family: "Open Sans", Arial, sans-serif;
  background-color: var(--mm-brand-bg) !important;
}

.mm-brand-heading {
  font-family: "Cormorant Garamond", Georgia, serif;
}

.mm-sidebar {
  background-color: var(--mm-brand) !important;
  border-color: var(--mm-brand-dark) !important;
}

.mm-sidebar-brand {
  overflow: hidden;
}

.mm-sidebar .mm-brand-heading,
.mm-sidebar .mm-brand-text {
  color: #ffffff !important;
}

.mm-sidebar nav a {
  color: rgba(255, 255, 255, 0.9);
}

.mm-sidebar nav a:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: #ffffff;
}

.mm-sidebar hr,
.mm-sidebar .border-slate-200 {
  border-color: rgba(255, 255, 255, 0.15) !important;
}

.mm-sidebar .text-slate-400,
.mm-sidebar .text-slate-700 {
  color: rgba(255, 255, 255, 0.65) !important;
}

.mm-sidebar .mm-brand-link {
  color: var(--mm-brand-accent) !important;
}

.mm-sidebar .mm-brand-link:hover {
  color: #ffffff !important;
}

.mm-mobile-header {
  background-color: var(--mm-brand-surface) !important;
  border-color: #e8e4e0 !important;
}

.mm-mobile-header .mm-brand-text,
.mm-mobile-header .mm-brand-link {
  color: var(--mm-brand) !important;
}

.btn-primary {
  background-color: var(--mm-brand) !important;
}

.btn-primary:hover {
  background-color: var(--mm-brand-dark) !important;
}

.text-indigo-600,
.text-indigo-700,
.text-indigo-800 {
  color: var(--mm-brand) !important;
}

.hover\\:text-indigo-800:hover {
  color: var(--mm-brand-dark) !important;
}

.border-indigo-200 {
  border-color: #e8e0d8 !important;
}

.bg-indigo-50 {
  background-color: #f5f0eb !important;
}

.input:focus,
.checkbox-row input[type="checkbox"]:focus,
.checkbox-list input[type="checkbox"]:focus {
  border-color: var(--mm-brand-muted) !important;
  --tw-ring-color: var(--mm-brand-muted) !important;
}

.checkbox-row input[type="checkbox"],
.checkbox-list input[type="checkbox"] {
  color: var(--mm-brand) !important;
}
"""
