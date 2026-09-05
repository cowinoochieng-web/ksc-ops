"""
api.py

Whitelisted, read-only REST endpoints exposed to the Flask
(ksc_collection_tracker) dashboard so it can pull live data from this
ERPNext instance -- the "systems integration" bridge between the two
portfolio pieces.

All three methods are plain frappe.get_list()/get_value() calls with no
ignore_permissions=True, so they are enforced by each caller's own
role/doctype permissions (see the "KSC API Reader" role, granted read-only
access to Station / Farmer / KSC Vehicle / Collection Run). A caller
without that role gets a frappe.PermissionError, not silently-filtered
data -- same "real enforcement" shape as ksc_collection_tracker's
require_menu() decorator.

Note: unlike the Flask side's Traccar integration, there is no live GPS
here -- KSC Vehicle has no position feed in ERPNext. get_fleet_status()
reports each vehicle's *dispatch* status (latest Collection Run) plus its
home Station's fixed coordinates, not a live device fix. Don't conflate
the two response shapes as both being "live GPS".
"""

from __future__ import annotations

import frappe
from frappe.utils import today


@frappe.whitelist(methods=["GET"])
def ping():
    """Cheap reachability/auth check -- used by Flask's erpnext_client.py
    to decide whether to use the real client or fall back to the mock,
    without doing a full data pull just to test connectivity."""
    return {
        "ok": True,
        "site": frappe.local.site,
        "user": frappe.session.user,
    }


@frappe.whitelist(methods=["GET"])
def get_summary(date_from: str | None = None, date_to: str | None = None) -> dict:
    """Mirrors the shape of ksc_collection_tracker's dashboard_data.get_summary():
    a date-scoped run-status breakdown plus roster counts."""
    date_from = date_from or today()
    date_to = date_to or today()

    runs = frappe.get_list(
        "Collection Run",
        filters={"run_date": ["between", [date_from, date_to]]},
        fields=["status"],
    )
    total_runs = len(runs)
    delivered = sum(1 for r in runs if r.status == "Delivered")
    sla_breaches = sum(1 for r in runs if r.status == "SLA Breach")
    in_progress = sum(1 for r in runs if r.status == "In Progress")

    return {
        "date_from": date_from,
        "date_to": date_to,
        "total_runs": total_runs,
        "delivered": delivered,
        "sla_breaches": sla_breaches,
        "in_progress": in_progress,
        "vehicle_count": frappe.db.count("KSC Vehicle"),
        "station_count": frappe.db.count("Station"),
        "farmer_count": frappe.db.count("Farmer"),
    }


@frappe.whitelist(methods=["GET"])
def get_fleet_status() -> list[dict]:
    """Mirrors the shape of dashboard_data.get_fleet_status(): one row per
    vehicle with its home location and current dispatch status. Latitude/
    longitude here are the home Station's fixed coordinates (Station has
    lat/lon fields), NOT a live vehicle position -- ERPNext has no GPS feed
    for KSC Vehicle."""
    vehicles = frappe.get_list(
        "KSC Vehicle",
        fields=["name", "plate_or_tag", "home_station", "default_driver"],
        order_by="plate_or_tag",
    )

    fleet = []
    for v in vehicles:
        station = None
        if v.home_station:
            station = frappe.db.get_value(
                "Station", v.home_station,
                ["station_name", "latitude", "longitude"], as_dict=True,
            )
        latest = frappe.get_list(
            "Collection Run",
            filters={"vehicle": v.name},
            fields=["status", "run_date", "start_time", "delivery_time"],
            order_by="creation desc",
            limit_page_length=1,
        )
        latest_run = latest[0] if latest else None

        fleet.append({
            "plate": v.plate_or_tag,
            "home_station": station.station_name if station else None,
            "driver": v.default_driver,
            "run_status": latest_run.status if latest_run else "no runs today",
            "run_date": latest_run.run_date if latest_run else None,
            "latitude": station.latitude if station else None,
            "longitude": station.longitude if station else None,
        })
    return fleet
