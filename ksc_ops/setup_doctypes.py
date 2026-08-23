"""
Scratch copy kept in the Flask repo for reference/history — the real
file that runs lives inside the Frappe app at
apps/ksc_ops/ksc_ops/setup_doctypes.py and is executed via:

    bench --site ksc.localhost execute ksc_ops.setup_doctypes.execute

Defines the five KSC Operations doctypes as real Frappe DocTypes
(Station, Farmer, Vehicle, Collection Item, Collection Run), mirroring
the SQLite schema in db.py from the Flask prototype.
"""

import frappe

MODULE = "KSC Operations"


def make_doctype(name, fields, autoname=None, istable=0, extra=None):
    if frappe.db.exists("DocType", name):
        print(f"DocType already exists: {name}")
        return
    doc = {
        "doctype": "DocType",
        "name": name,
        "module": MODULE,
        "custom": 0,
        "istable": istable,
        "fields": fields,
        "permissions": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}
        ],
    }
    if autoname:
        doc["autoname"] = autoname
    if extra:
        doc.update(extra)
    d = frappe.get_doc(doc)
    d.insert(ignore_permissions=True)
    print(f"Created DocType: {name}")


def execute():
    make_doctype(
        "Station",
        autoname="field:station_name",
        fields=[
            {"fieldname": "station_name", "label": "Station Name", "fieldtype": "Data", "reqd": 1, "unique": 1, "in_list_view": 1},
            {"fieldname": "county", "label": "County", "fieldtype": "Select",
             "options": "Kisii\nNyamira\nBomet\nNarok", "reqd": 1, "in_list_view": 1},
            {"fieldname": "column_break_coords", "fieldtype": "Column Break"},
            {"fieldname": "latitude", "label": "Latitude", "fieldtype": "Float"},
            {"fieldname": "longitude", "label": "Longitude", "fieldtype": "Float"},
        ],
    )

    make_doctype(
        "Farmer",
        autoname="naming_series:",
        fields=[
            {"fieldname": "naming_series", "label": "Series", "fieldtype": "Select", "options": "FARM-.#####", "reqd": 1},
            {"fieldname": "farmer_name", "label": "Farmer Name", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
            {"fieldname": "phone", "label": "Phone", "fieldtype": "Data"},
            {"fieldname": "column_break_farmer", "fieldtype": "Column Break"},
            {"fieldname": "station", "label": "Station", "fieldtype": "Link", "options": "Station", "reqd": 1, "in_list_view": 1},
            {"fieldname": "value_chain", "label": "Value Chain", "fieldtype": "Select",
             "options": "Dairy\nBanana\nVegetable", "reqd": 1, "in_list_view": 1},
        ],
    )

    # Named "KSC Vehicle" rather than "Vehicle" — ERPNext already ships a
    # standard "Vehicle" doctype (HR module, fleet/asset tracking with a
    # very different schema: license plate, make/model, insurance, fuel
    # type). Learned this the hard way: an earlier pass created a doctype
    # named "Vehicle" without checking, silently colliding with it.
    make_doctype(
        "KSC Vehicle",
        autoname="field:plate_or_tag",
        fields=[
            {"fieldname": "plate_or_tag", "label": "Plate / Tag", "fieldtype": "Data", "reqd": 1, "unique": 1, "in_list_view": 1},
            {"fieldname": "traccar_device_id", "label": "Traccar Device ID", "fieldtype": "Data", "reqd": 1},
            {"fieldname": "column_break_vehicle", "fieldtype": "Column Break"},
            {"fieldname": "home_station", "label": "Home Station", "fieldtype": "Link", "options": "Station", "reqd": 1, "in_list_view": 1},
        ],
    )

    make_doctype(
        "Collection Item",
        istable=1,
        fields=[
            {"fieldname": "farmer", "label": "Farmer", "fieldtype": "Link", "options": "Farmer", "reqd": 1, "in_list_view": 1},
            {"fieldname": "product", "label": "Product", "fieldtype": "Select",
             "options": "Dairy\nBanana\nVegetable", "reqd": 1, "in_list_view": 1},
            {"fieldname": "quantity", "label": "Quantity", "fieldtype": "Float", "reqd": 1, "in_list_view": 1},
            {"fieldname": "unit", "label": "Unit", "fieldtype": "Select", "options": "litres\nkg", "reqd": 1, "in_list_view": 1},
        ],
    )

    make_doctype(
        "Collection Run",
        autoname="naming_series:",
        fields=[
            {"fieldname": "naming_series", "label": "Series", "fieldtype": "Select", "options": "CR-.YYYY.-.#####", "reqd": 1},
            {"fieldname": "run_date", "label": "Run Date", "fieldtype": "Date", "default": "Today", "reqd": 1, "in_list_view": 1},
            {"fieldname": "status", "label": "Status", "fieldtype": "Select",
             "options": "In Progress\nDelivered\nSLA Breach", "default": "In Progress", "in_list_view": 1, "in_standard_filter": 1},
            {"fieldname": "column_break_run", "fieldtype": "Column Break"},
            {"fieldname": "vehicle", "label": "Vehicle", "fieldtype": "Link", "options": "KSC Vehicle", "reqd": 1, "in_list_view": 1},
            {"fieldname": "station", "label": "Station", "fieldtype": "Link", "options": "Station", "reqd": 1, "in_list_view": 1},
            {"fieldname": "section_break_times", "fieldtype": "Section Break", "label": "Timing"},
            {"fieldname": "start_time", "label": "Start Time", "fieldtype": "Datetime", "reqd": 1},
            {"fieldname": "column_break_times", "fieldtype": "Column Break"},
            {"fieldname": "delivery_time", "label": "Delivery Time", "fieldtype": "Datetime"},
            {"fieldname": "section_break_items", "fieldtype": "Section Break", "label": "Collected Items"},
            {"fieldname": "items", "label": "Items", "fieldtype": "Table", "options": "Collection Item"},
        ],
    )

    frappe.db.commit()
    print("All doctypes processed.")
