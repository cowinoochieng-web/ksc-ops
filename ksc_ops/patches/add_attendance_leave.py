import frappe

DRIVER_DESIGNATION = "E-Trike Pilot"
SHIFT_NAME = "Field Collection Shift"
HOLIDAY_LIST_NAME = "Kenya Public Holidays 2026"

LEAVE_TYPES = (
	# (name, max_leaves_allowed, is_lwp)
	("Annual Leave", 21, 0),
	("Sick Leave", 14, 0),
	("Compassionate Leave", 5, 0),
)

KENYA_HOLIDAYS_2026 = (
	("2026-01-01", "New Year's Day"),
	("2026-05-01", "Labour Day"),
	("2026-06-01", "Madaraka Day"),
	("2026-10-20", "Mashujaa Day"),
	("2026-12-12", "Jamhuri Day"),
	("2026-12-25", "Christmas Day"),
)


def execute():
	create_leave_types()
	create_shift_type()
	create_holiday_list()
	assign_drivers()


def create_leave_types():
	for title, max_leaves, is_lwp in LEAVE_TYPES:
		if frappe.db.exists("Leave Type", title):
			continue
		frappe.get_doc(
			{
				"doctype": "Leave Type",
				"leave_type_name": title,
				"max_leaves_allowed": max_leaves,
				"is_lwp": is_lwp,
			}
		).insert(ignore_permissions=True)


def create_shift_type():
	if frappe.db.exists("Shift Type", SHIFT_NAME):
		return
	frappe.get_doc(
		{
			"doctype": "Shift Type",
			"name": SHIFT_NAME,
			"start_time": "05:00:00",
			"end_time": "13:00:00",
			"enable_auto_attendance": 1,
			"determine_check_in_and_check_out": "Strictly based on Log Type in Employee Checkin",
			"working_hours_calculation_based_on": "First Check-in and Last Check-out",
		}
	).insert(ignore_permissions=True)


def create_holiday_list():
	if frappe.db.exists("Holiday List", HOLIDAY_LIST_NAME):
		return
	frappe.get_doc(
		{
			"doctype": "Holiday List",
			"holiday_list_name": HOLIDAY_LIST_NAME,
			"from_date": "2026-01-01",
			"to_date": "2026-12-31",
			"holidays": [
				{"holiday_date": date, "description": desc} for date, desc in KENYA_HOLIDAYS_2026
			],
		}
	).insert(ignore_permissions=True)


def assign_drivers():
	drivers = frappe.get_all("Employee", filters={"designation": DRIVER_DESIGNATION}, pluck="name")
	for name in drivers:
		frappe.db.set_value(
			"Employee",
			name,
			{"default_shift": SHIFT_NAME, "holiday_list": HOLIDAY_LIST_NAME},
		)
		if not frappe.db.exists(
			"Holiday List Assignment", {"assigned_to": name, "holiday_list": HOLIDAY_LIST_NAME}
		):
			hla = frappe.get_doc(
				{
					"doctype": "Holiday List Assignment",
					"assigned_to": name,
					"holiday_list": HOLIDAY_LIST_NAME,
					"from_date": "2026-01-01",
				}
			)
			hla.insert(ignore_permissions=True)
			hla.submit()
