# Stockroom Retail Management — Implementation Plan

## Product direction
A focused retail operations console for small shops: fast at the till, legible for inventory work, and calm enough for daily use.

### Design options
- **Quiet Mercantile (0.06):** warm paper surfaces, deep ink, moss green, and a brass action color.
- **Industrial Ledger (0.04):** cool gray, signal orange, dense tables, and mono labels.
- **Fresh Market Utility (0.08):** white, botanical green, and bright citrus with softer cards.

Chosen: **Quiet Mercantile**.

**Design movement:** contemporary independent-grocer back office, combining editorial whitespace with ledger-like operational tables.
**Core principles:** immediate context, confident actions, low visual noise, and useful alerts.
**Color philosophy:** paper reduces screen fatigue; ink anchors important data; moss signals safe operational actions; brass calls attention to money and next steps.
**Layout paradigm:** a persistent left rail and asymmetric dashboard panels, with dense work surfaces only where data requires them.
**Signature elements:** brass “quick action” panels, rounded ink navigation, and reorder alerts that use restrained red only for exceptions.
**Interaction philosophy:** every workflow ends in a clear action; destructive or ambiguous states are avoided in the MVP.
**Animation:** minimal; use hover transitions only, preserving a calm operations feel.
**Typography system:** system sans for speed, heavy numeric hierarchy for money and counts, compact uppercase labels for navigation context.
**Brand essence:** a dependable control room for independent retailers; practical, warm, decisive.
**Brand voice:** direct and useful. Example: “Open the till” and “Inventory levels look healthy.”
**Wordmark:** “Stockroom.” with a brass period as the signature mark.
**Signature brand color:** brass `#E8B14A`.

## Implementation
Django 5 with a single `store` app, server-rendered templates, SQLite locally, and PostgreSQL via `DATABASE_URL` in production. Core models are Category, Product, Sale, and SaleItem. Checkout is transaction-wrapped with row-level locking to avoid stock races. WhiteNoise serves static assets and Gunicorn runs the production web process.

## Project structure
- `config/`: Django settings, URL routing, and WSGI entrypoint.
- `store/`: retail models, admin, views, URLs, templates, and demo seed command.
- `static/`: reserved for static assets.
- `render.yaml`: Render web service and managed PostgreSQL definition.
