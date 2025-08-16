import requests
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

BASE_URL = "http://localhost:8100/api"
DAYS_AHEAD = 7
# Example employee data
# All employees have the same password "dp"
EMPLOYEES = [
    {"username": "alice.johnson@example.com", "password": "dp"},
    {"username": "bob.smith@example.com", "password": "dp"},
    {"username": "charlie.medson@example.com", "password": "dp"},
    {"username": "jake.fox@example.com", "password": "dp"},
    {"username": "ben.cole@example.com", "password": "dp"},
    {"username": "max.ray@example.com", "password": "dp"},
    {"username": "leo.kent@example.com", "password": "dp"},
    {"username": "sam.tate@example.com", "password": "dp"},
    {"username": "zoe.lane@example.com", "password": "dp"},
    {"username": "eva.moss@example.com", "password": "dp"},
    {"username": "lian.hale@example.com", "password": "dp"},
    {"username": "noah.ried@example.com", "password": "dp"},
    {"username": "mia.wynn@example.com", "password": "dp"},
    {"username": "luke.cian@example.com", "password": "dp"},
    {"username": "amy.shaw@example.com", "password": "dp"},
]

DEVICE_INFO = {
    "device_uuid": "test-device-uuid-1231aqs",
    "device_name": "Samsung A501",
    "fcm_token": "test-fcm-token-123",
    "grant_type": "password",
    "client_id": "dummy-client-id",
    "client_secret": "dummy-client-secret",
    "force_logout": True
}

def dynamic_dates(days_ahead):
    return [(datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days_ahead)]

def login_employee(emp):
    payload = {**emp, **DEVICE_INFO}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post(
        f"{BASE_URL}/employees/auth/employee/login",
        data=payload,   # send as form data, not JSON
        headers=headers
    )
    if res.status_code != 200:
        print(f"Login failed for {emp['username']}: {res.status_code} | {res.text}")
        return None
    return res.json()

def fetch_common_shifts(token, dates, log_type="out"):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"dates": dates, "log_type": log_type}
    res = requests.post(f"{BASE_URL}/employee/common-shifts/", headers=headers, json=payload)
    return res.json() if res.status_code == 200 else None
def fetch_common_shifts(token, dates, log_type="in"):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"dates": dates, "log_type": log_type}
    res = requests.post(f"{BASE_URL}/employee/common-shifts/", headers=headers, json=payload)
    return res.json() if res.status_code == 200 else None

def book_shift(token, shift_id, date):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"shift_id": shift_id, "dates": date}
    res = requests.post(f"{BASE_URL}/employee/create_booking/", headers=headers, json=payload)
    return res.status_code, res.json()

def cancel_shift(token, shift_id, date):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"shift_id": shift_id, "dates": date}
    res = requests.post(f"{BASE_URL}/employee/cancel_booking/", headers=headers, json=payload)
    return res.status_code, res.json()

def main():
    report = []

    dates_to_try = dynamic_dates(DAYS_AHEAD)
    for emp in EMPLOYEES:
        print(f"\nProcessing {emp['username']}")
        login_res = login_employee(emp)
        if not login_res:
            print("Login failed")
            continue

        token = login_res["access_token"]

        for date in dates_to_try:
            shift_res = fetch_common_shifts(token, [date])
            if not shift_res or not shift_res.get("shifts"):
                print(f"No shifts for {date}")
                continue

            booked = False
            for shift in shift_res["shifts"]:
                shift_days = shift["day"].replace("{","").replace("}","").split(",")
                day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%A").lower()
                if day_name in shift_days:
                    status, res = book_shift(token, shift["shift_id"], date)
                    print(f"Booking {emp['username']} on {date}: {status} | {res}")
                    report.append({
                        "employee": emp['username'],
                        "date": date,
                        "shift_id": shift["shift_id"],
                        "status": status,
                        "response": res
                    })
                    booked = True
                    break
            if not booked:
                print(f"Date {date} does not match any shift days for {emp['username']}")

    # Save report
    with open("booking_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\nBooking report saved to booking_report.json")

if __name__ == "__main__":
    main()
