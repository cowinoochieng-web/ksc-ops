"""
setup_ops_assistant_page.py

Creates the "Ops Assistant" desk Page and wires it into the existing
"Fleet & HR" Workspace as a shortcut.

    bench --site ksc.localhost execute ksc_ops.setup_ops_assistant_page.execute
"""

import json

import frappe

PAGE_NAME = "ops-assistant"
WORKSPACE_NAME = "Fleet & HR"


def _create_page():
    if frappe.db.exists("Page", PAGE_NAME):
        print(f"Page already exists: {PAGE_NAME}")
        return
    frappe.get_doc({
        "doctype": "Page",
        "page_name": PAGE_NAME,
        "title": "Ops Assistant",
        "module": "KSC Operations",
        "standard": "Yes",
    }).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"Created Page: {PAGE_NAME}")


def _add_workspace_shortcut():
    ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
    if any(s.label == "Ops Assistant" for s in ws.shortcuts):
        print("Shortcut already present")
        return
    ws.append("shortcuts", {
        "type": "Page",
        "link_to": PAGE_NAME,
        "label": "Ops Assistant",
        "color": "Blue",
    })
    content = json.loads(ws.content)
    content.append({
        "id": frappe.generate_hash(length=10),
        "type": "shortcut",
        "data": {"shortcut_name": "Ops Assistant", "col": 4},
    })
    ws.content = json.dumps(content)
    ws.save(ignore_permissions=True)
    frappe.db.commit()
    print("Added shortcut to Fleet & HR workspace")


def execute():
    _create_page()
    _add_workspace_shortcut()
