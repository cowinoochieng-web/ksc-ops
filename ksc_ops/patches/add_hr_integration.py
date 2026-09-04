import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

KSC_DESIGNATIONS = (
	"E-Trike Pilot",
	"Station Attendant",
	"Vehicle Technician",
	"Dispatch Supervisor",
)


def execute():
	create_custom_fields(
		{
			"Employee": [
				{
					"fieldname": "custom_home_station",
					"label": "Home Station",
					"fieldtype": "Link",
					"options": "Station",
					"insert_after": "branch",
				}
			]
		}
	)

	for title in KSC_DESIGNATIONS:
		if not frappe.db.exists("Designation", title):
			frappe.get_doc({"doctype": "Designation", "designation_name": title}).insert(
				ignore_permissions=True
			)
