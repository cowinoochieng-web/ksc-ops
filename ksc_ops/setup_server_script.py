"""
Scratch copy kept in the Flask repo for reference — the real file
runs inside the Frappe app at apps/ksc_ops/ksc_ops/setup_server_script.py,
executed via:

    bench --site ksc.localhost execute ksc_ops.setup_server_script.execute

Creates a Server Script on Collection Run (Before Save) that ports the
SLA-breach logic from collection_tracker.py's complete_run() into real
ERPNext: same SLA_MINUTES thresholds, same "tightest window across the
run's products" rule, now running server-side on every save instead of
in a Flask route.
"""

import frappe

SCRIPT_NAME = "KSC Collection Run SLA Check"

SCRIPT_BODY = '''\
# Mirrors collection_tracker.py's complete_run(): once a run has both a
# start_time and a delivery_time, check elapsed time against the
# tightest SLA window among the products actually collected on this
# run, and set status accordingly. Illustrative thresholds — a real
# deployment would source these from KSC's quality/ops team, same as
# the original prototype's SLA_MINUTES comment says.

SLA_MINUTES = {"Dairy": 120, "Vegetable": 300, "Banana": 480}

if doc.delivery_time and doc.start_time:
	products = {item.product for item in doc.items if item.product}
	windows = [SLA_MINUTES[p] for p in products if p in SLA_MINUTES]

	if windows:
		tightest = min(windows)
		elapsed_minutes = frappe.utils.time_diff_in_seconds(doc.delivery_time, doc.start_time) / 60
		doc.status = "SLA Breach" if elapsed_minutes > tightest else "Delivered"
	else:
		doc.status = "Delivered"
'''


def execute():
    if frappe.db.exists("Server Script", SCRIPT_NAME):
        print(f"Server Script already exists: {SCRIPT_NAME}")
        return

    doc = frappe.get_doc({
        "doctype": "Server Script",
        "name": SCRIPT_NAME,
        "script_type": "DocType Event",
        "reference_doctype": "Collection Run",
        "doctype_event": "Before Save",
        "script": SCRIPT_BODY,
        "disabled": 0,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"Created Server Script: {SCRIPT_NAME}")
