"""
setup_driver_leave_check.py

Creates a Server Script on Collection Run (Before Save) that blocks
scheduling a run for a driver who has an Approved Leave Application
covering the run's date — the HR/Ops guardrail counterpart to
setup_server_script.py's SLA check.

    bench --site ksc.localhost execute ksc_ops.setup_driver_leave_check.execute
"""

import frappe

SCRIPT_NAME = "KSC Driver Leave Check"

SCRIPT_BODY = '''\
# Blocks saving a Collection Run against a driver who is on approved
# leave for that run's date - the counterpart, on the HR side, to the
# SLA check on the ops side.

if doc.driver and doc.run_date:
	on_leave = frappe.db.exists(
		"Leave Application",
		{
			"employee": doc.driver,
			"status": "Approved",
			"from_date": ["<=", doc.run_date],
			"to_date": [">=", doc.run_date],
		},
	)
	if on_leave:
		frappe.throw(
			f"{doc.driver} has approved leave on {doc.run_date} and cannot be assigned to this run."
		)
'''


def execute():
	if frappe.db.exists("Server Script", SCRIPT_NAME):
		print(f"Server Script already exists: {SCRIPT_NAME}")
		return

	doc = frappe.get_doc(
		{
			"doctype": "Server Script",
			"name": SCRIPT_NAME,
			"script_type": "DocType Event",
			"reference_doctype": "Collection Run",
			"doctype_event": "Before Save",
			"script": SCRIPT_BODY,
			"disabled": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	print(f"Created Server Script: {SCRIPT_NAME}")
