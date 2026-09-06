"""
assistant_api.py

Whitelisted, read-only Q&A endpoint for the "Ops Assistant" desk Page.
Deliberately separate from api.py: that module is scoped to the
Flask-bridge's KSC API Reader role (Station/Farmer/KSC Vehicle/
Collection Run only) and its GET-only REST shape; this endpoint is
called by an already-authenticated desk user and needs Leave
Application/Employee too, so it's a different permission surface.

All context queries use frappe.get_list(), never frappe.get_all(),
so the calling desk user's own doctype permissions are enforced --
same rule established in api.py.
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, today

from ksc_ops.llm_client import MockLLMClient, build_client

CONTEXT_WINDOW_DAYS = 7


def get_context() -> dict:
    """Compact snapshot of current ops + HR state, bounded to the last
    7 days of runs and today's leave, to keep the eventual real-LLM
    prompt small (roughly a few KB of JSON / low thousands of tokens
    worst case, not the whole database)."""
    today_, week_ago = today(), add_days(today(), -CONTEXT_WINDOW_DAYS)

    runs = frappe.get_list(
        "Collection Run",
        filters={"run_date": ["between", [week_ago, today_]]},
        fields=["name", "run_date", "status", "vehicle", "station", "driver", "start_time", "delivery_time"],
        order_by="run_date desc",
        limit_page_length=100,
    )
    fleet = frappe.get_list(
        "KSC Vehicle",
        fields=["name", "plate_or_tag", "home_station", "default_driver"],
        order_by="plate_or_tag",
        limit_page_length=50,
    )
    stations = frappe.get_list(
        "Station", fields=["name", "station_name", "county"], limit_page_length=50
    )
    leave_today = frappe.get_list(
        "Leave Application",
        filters={"status": "Approved", "from_date": ["<=", today_], "to_date": [">=", today_]},
        fields=["employee", "employee_name", "leave_type", "from_date", "to_date"],
        limit_page_length=50,
    )

    return {
        "today": today_,
        "window": {"from": week_ago, "to": today_},
        "runs": runs,
        "sla_breaches": [r for r in runs if r.status == "SLA Breach"],
        "fleet": fleet,
        "stations": stations,
        "leave_today": leave_today,
        "counts": {
            "total_runs": len(runs),
            "sla_breaches": sum(1 for r in runs if r.status == "SLA Breach"),
            "in_progress": sum(1 for r in runs if r.status == "In Progress"),
            "delivered": sum(1 for r in runs if r.status == "Delivered"),
            "vehicles": len(fleet),
            "stations": len(stations),
            "on_leave_today": len(leave_today),
        },
    }


@frappe.whitelist()
def ask(question: str) -> dict:
    """Called via frappe.call() from ops_assistant.js."""
    if not question or not question.strip():
        frappe.throw("Please enter a question.")

    context = get_context()
    client, is_live = build_client()
    provider = client.__class__.__name__

    try:
        answer = client.ask(question.strip(), context)
    except Exception:
        frappe.log_error(title="KSC Ops Assistant: live LLM call failed")
        if not is_live:
            raise
        client, is_live, provider = MockLLMClient(), False, "MockLLMClient"
        answer = client.ask(question.strip(), context) + (
            "\n\n_(Note: the live LLM call failed; fell back to offline mode for this answer.)_"
        )

    return {"answer": answer, "is_live": is_live, "provider": provider}
