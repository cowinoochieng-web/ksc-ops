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

## Screenshots

A Collection Run that breached its SLA — real doctype form, real data:

![Collection Run form showing an SLA Breach](screenshots/collection_run.jpg)

The SLA-check logic as an actual Server Script inside ERPNext, not a Flask route:

![KSC Collection Run SLA Check server script](screenshots/server_script.jpg)

## Technologies used

| Layer | Choice | Why |
|---|---|---|
| Framework | Frappe `version-16` / ERPNext `version-16` | The actual framework a Frappe-stack IT/systems role runs on, not a from-scratch imitation of it |
| Language | Python 3.14 | Matches the bench's pinned runtime |
| Frontend | Frappe's desk UI, Node 24 build tooling | Standard Frappe doctype forms/list views — no custom frontend was built, since the point was proving doctype/server-script fluency, not rebuilding the desk UI |
| Data | MariaDB (via bench), Redis (cache/queue) | Frappe's standard stack, run as systemd services |
| Dev environment | WSL2 Ubuntu, pyenv, nvm | Local bench for development and this README's screenshots |

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

## Challenges encountered

Renaming the vehicle doctype turned out to be the real lesson in this
build. It started life as `Vehicle`, which collides with a doctype
ERPNext's own Assets module already owns — installing broke in a way
that made the naming conflict obvious. Fixing it wasn't a single
rename:

- **`fix_vehicle.py`** deleted the stale `Vehicle` doctype and
  re-exported it correctly as `KSC Vehicle` under the `KSC Operations`
  module.
- **`fix_collection_run_link.py`** then had to separately correct
  Collection Run's `vehicle` field, whose Link target was still
  pointing at the old doctype name — renaming a doctype in Frappe
  doesn't cascade to every field that references it by name.
- **`fix_server_script.py`** corrected the Server Script's body after
  an earlier version existed but wasn't actually evaluating the SLA
  logic correctly — it took deliberately seeding one in-SLA and one
  breaching run and checking the *actual* resulting status, not just
  confirming the script existed, to catch it.

Those three scripts aren't in the repo (they were one-off fixes run
via `bench execute` and cleaned up after), but the doctype/field
structure they corrected is what ships today.

## What I learned

- **A doctype name is a public API the moment anything links to it.**
  The `Vehicle` → `KSC Vehicle` rename touched more than the doctype
  itself — every Link field pointing at the old name needed a
  follow-up fix. Worth checking a proposed doctype name against core
  ERPNext modules *before* building fields on top of it, not after.
- **"The script exists" and "the script works" are different claims.**
  The SLA Server Script's first version was present and enabled but
  wasn't producing correct output — only caught by seeding a
  deliberately-breaching run and checking its actual status field,
  not by confirming the script saved without error.
- **Frappe's server scripts are a legitimate place to port real
  business logic**, not just a scripting toy — the same
  `SLA_MINUTES`/tightest-window logic from the Flask prototype's
  Python function ports directly into a `Before Save` script with
  almost no translation, which says something about how close
  Frappe's scripting model is to plain Python.

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
