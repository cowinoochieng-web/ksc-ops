# KSC Operations (ERPNext / Frappe)

A custom Frappe app that ports the [First-Mile Collection & Fleet
Dispatch Tracker](https://github.com/cowinoochieng-web/ksc-collection-tracker)
— a standalone Flask/SQLite prototype built to understand Kisii Smart
Community's operational problem — into real ERPNext doctypes, on the
actual framework.

## Why this exists alongside the Flask prototype

The Flask app proves the workflow logic and the general full-stack
skill set. It doesn't prove ERPNext/Frappe development specifically,
because it isn't ERPNext — it's a from-scratch tool designed to be
*easy to demo* without a provisioned Frappe/MariaDB stack. This app is
the other half: the same domain, rebuilt as customised DocTypes,
fields, and a server-side script inside a real bench, to close that
gap with working code instead of a "self-directed, in progress" note.

## What's in it

- **Station** — a first-mile collection hub (name, county, coordinates).
  Maps 1:1 to `hubs` in the Flask prototype's `db.py`.
- **Farmer** — name, phone, home station, value chain (Dairy / Banana
  / Vegetable).
- **KSC Vehicle** — plate/tag, Traccar device ID, home station. Named
  `KSC Vehicle` rather than `Vehicle` since ERPNext's Assets module
  already owns that name.
- **Collection Run** — a vehicle dispatched from a station, with a
  child table of **Collection Item** rows (farmer, product, quantity,
  unit), start/delivery timestamps, and a status field (In Progress /
  Delivered / SLA Breach).
- **Server Script — "KSC Collection Run SLA Check"** (`Before Save` on
  Collection Run) — ports `collection_tracker.py`'s `complete_run()`
  logic directly: once a run has both a start and delivery time, it
  checks elapsed time against the tightest SLA window among the
  products actually collected (same `SLA_MINUTES` thresholds: Dairy
  120, Vegetable 300, Banana 480), and sets the status accordingly —
  now running inside ERPNext on every save, not in a Flask route.

`ksc_ops/setup_doctypes.py` and `ksc_ops/setup_server_script.py` are
the scripts that created all of the above — kept in the repo as a
record of *how* it was built, since with `developer_mode` on, running
them is what generated the actual `.json`/`.py`/`.js` files under
`ksc_ops/ksc_operations/doctype/` that ship with the app.

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/cowinoochieng-web/ksc-ops --branch version-16
bench --site your-site install-app ksc_ops
```

Built and tested against Frappe `version-16` / ERPNext `version-16`,
Python 3.14, Node 24, on a local WSL2 Ubuntu bench.

## What I'd build next with real access

- A Workflow on Collection Run for the human-driven parts (dispatch →
  in-transit → received at hub) alongside the automatic SLA check,
  matching how a real ops team would actually move a run through
  hand-offs.
- Whitelisted API endpoints (`@frappe.whitelist()`) exposing Collection
  Run creation to the Traccar-integrated fleet dashboard, so the two
  projects talk to each other instead of living side by side.
- Fixtures for the Server Script (and Workflow, once added) exported
  via `bench --site your-site export-fixtures`, so a fresh install
  gets them automatically instead of needing the setup scripts run
  by hand.
