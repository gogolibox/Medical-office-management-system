# 1) Standard libraries
import sqlite3

# 2) Third-party libraries
import streamlit as st
import pandas as pd

# 3) Import your backend functions (from your code file)
#    IMPORTANT: rename your backend file to backend.py first.
from backend import (
    get_conn,
    doctor_signUP,
    book,
    list_appointment,
    list_doctor,
    check_id_exist,
    delete_doctor,
    authenticate_patient,
    cancel_appointment,
    get_appointment_by_id,
    register_patient,
    cancel_schedule_slot,
    admin_cancel_appointment_by_id,
    admin_list_all_appointments,
)

# ----------------------------
# Helper DB functions used only by the UI (admin actions / signup / listing all)
# ----------------------------

# def register_patient(nat_id: str, name: str, last_name: str, password: str):
#     """UI helper: register a new patient. Returns (ok, msg)."""
#     if not (nat_id and name and last_name and password):
#         return (False, "All fields are required.")

#     # check duplicate
#     if check_id_exist(nat_id, "national_id", "patients"):
#         return (False, "This National ID already exists. Please log in.")

#     conn = get_conn()
#     cur = conn.cursor()
#     try:
#         cur.execute("""
#             INSERT INTO patients(national_id, name, last_name, password)
#             VALUES (?,?,?,?)
#         """, (nat_id, name, last_name, password))
#         conn.commit()
#         return (True, "Signed up successfully. You can log in now.")
#     except sqlite3.Error as e:
#         conn.rollback()
#         return (False, f"DB Error: {e}")
#     finally:
#         conn.close()


# def admin_list_all_appointments(stat=None):
#     """UI helper: list all appointments for admin. Returns list[dict]."""
#     conn = get_conn()
#     cur = conn.cursor()
#     try:
#         cur.execute("""
#             SELECT
#                 a.id, a.doctor_id, a.patient_id, s.day_of_week, a.start_ts, a.end_ts, a.status
#             FROM appointments a
#             LEFT JOIN doctor_schedule s
#             ON s.doctor_id = a.doctor_id
#             AND s.start_time = a.start_ts
#             AND s.end_time   = a.end_ts
#             WHERE (? IS NULL OR status = ?)
#             ORDER BY start_ts
#         """, (stat, stat))
#         rows = cur.fetchall()
#         return [
#             {
#                 "id": r[0],
#                 "doctor_id": r[1],
#                 "patient_id": r[2],
#                 "day_of_week": r[3],
#                 "start_ts": r[4],
#                 "end_ts": r[5],
#                 "status": r[6],
#             }
#             for r in rows
#         ]
#     finally:
#         conn.close()


# def cancel_schedule_slot(schedule_id: int):
#     """
#     UI helper: cancel a slot in doctor_schedule and cancel matching appointments.
#     Returns (ok, msg).
#     """
#     conn = get_conn()
#     cur = conn.cursor()
#     try:
#         # Cancel the slot
#         cur.execute("""
#             UPDATE doctor_schedule
#             SET status = ?
#             WHERE id = ?
#         """, ("CANCELED", schedule_id))

#         # Cancel matching appointments (same doctor & times)
#         cur.execute("""
#             UPDATE appointments
#             SET status = ?
#             WHERE doctor_id = (
#                 SELECT doctor_id FROM doctor_schedule WHERE id = ?
#             )
#             AND start_ts = (
#                 SELECT start_time FROM doctor_schedule WHERE id = ?
#             )
#             AND end_ts = (
#                 SELECT end_time FROM doctor_schedule WHERE id = ?
#             )
#             AND status = 'CONFIRMED'
#         """, ("CANCELED", schedule_id, schedule_id, schedule_id))

#         conn.commit()

#         if cur.rowcount == 0:
#             # Note: rowcount here refers to the LAST UPDATE (appointments)
#             # The schedule update may still have worked. We keep message simple.
#             return (True, "Slot canceled. (No CONFIRMED matching appointments found.)")

#         return (True, "Slot canceled and matching appointments canceled.")
#     except sqlite3.Error as e:
#         conn.rollback()
#         return (False, f"DB Error: {e}")
#     finally:
#         conn.close()


# def admin_cancel_appointment_by_id(app_id: int):
#     """
#     Admin cancels any appointment by appointment id only.
#     Returns (ok, msg).
#     """
#     conn = get_conn()
#     cur = conn.cursor()
#     try:
#         cur.execute("SELECT status FROM appointments WHERE id = ?", (app_id,))
#         r = cur.fetchone()
#         if not r:
#             return (False, "Appointment not found.")

#         status = r[0]
#         if status == "CANCELED":
#             return (False, "This appointment is already canceled.")
#         if status != "CONFIRMED":
#             return (False, f"Only CONFIRMED can be canceled (current: {status}).")

#         cur.execute("UPDATE appointments SET status = ? WHERE id = ?", ("CANCELED", app_id))
#         conn.commit()

#         if cur.rowcount == 0:
#             return (False, "Cancel failed (appointment may have changed).")

#         return (True, "Appointment canceled successfully.")
#     except sqlite3.Error as e:
#         conn.rollback()
#         return (False, f"DB Error: {e}")
#     finally:
#         conn.close()


# ----------------------------
# Streamlit App Setup
# ----------------------------

st.set_page_config(page_title="Clinic App", layout="wide")

# Session state initialization
if "auth" not in st.session_state:
    st.session_state.auth = {
        "logged_in": False,
        "role": None,          # "patient" or "admin"
        "patient": None,       # dict with patient data
    }

# Header
st.title("Clinic Appointment System")

# ----------------------------
# Sidebar Navigation
# ----------------------------

with st.sidebar:
    st.header("Navigation")

    if not st.session_state.auth["logged_in"]:
        page = st.radio("Go to", ["Login / Signup"])
    else:
        role = st.session_state.auth["role"]
        st.caption(f"Logged in as: {role}")

        if role == "patient":
            page = st.radio("Go to", [
                "Patient Dashboard",
                "View Schedules",
                "Book Appointment",
                "My Appointments",
                "Cancel Appointment",
                "Logout"
            ])
        else:
            page = st.radio("Go to", [
                "Admin Dashboard",
                "View Schedules",
                "View All Appointments",
                "Cancel Appointment (Admin)",
                "Cancel Time Slot",
                "Sign Up Doctor",
                "Delete Doctor",
                "Logout"
            ])

# ----------------------------
# Pages (UI)
# ----------------------------

if page == "Login / Signup":
    st.subheader("Login / Signup")

    tab_login, tab_signup = st.tabs(["Login", "Signup (Patient only)"])

    with tab_login:
        role = st.selectbox("Role", ["patient", "admin"])

        if role == "admin":
            admin_pass = st.text_input("Admin Secret", type="password", key="admin_secret")

        elif role == "patient":
            username = st.text_input("National ID", key="login_nat")
            password = st.text_input("Password", type="password", key="login_pw")

        if st.button("Login"):
            if role == "patient":
                ok, msg, patient = authenticate_patient(username, password)
                if ok:
                    st.session_state.auth["logged_in"] = True
                    st.session_state.auth["role"] = "patient"
                    st.session_state.auth["patient"] = patient
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                # Admin auth
                if admin_pass == "1234":
                    st.session_state.auth["logged_in"] = True
                    st.session_state.auth["role"] = "admin"
                    st.session_state.auth["patient"] = None
                    st.success("Admin login successful.")
                    st.rerun()
                else:
                    st.error("Wrong admin password.")

    with tab_signup:
        nat_id = st.text_input("National ID", key="su_nat")
        name = st.text_input("First Name", key="su_name")
        last_name = st.text_input("Last Name", key="su_last")
        pw1 = st.text_input("Password", type="password", key="su_pw1")
        pw2 = st.text_input("Password Again", type="password", key="su_pw2")

        if st.button("Create Account"):
            if pw1 != pw2:
                st.error("Passwords do not match.")
            else:
                ok, msg = register_patient(nat_id, name, last_name, pw1)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


elif page == "Patient Dashboard":
    st.subheader("Patient Dashboard")
    patient = st.session_state.auth["patient"]
    st.write(f"Welcome **{patient['name']} {patient['last_name']}** (ID: {patient['patient_id']})")

    st.info("Use the sidebar to view schedules, book, or cancel appointments.")


elif page == "Admin Dashboard":
    st.subheader("Admin Dashboard")
    st.info("Use the sidebar to manage schedules and appointments.")


elif page == "View Schedules":
    st.subheader("Doctor Schedules")

    doc_filter = st.text_input("Filter by doctor_id (leave empty for all)")
    doctor_id = None if doc_filter.strip() == "" else doc_filter.strip()

    rows = list_doctor(doctor_id)
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    st.caption("Column id is the schedule slot id. Use it for booking/canceling slots.")


elif page == "Book Appointment":
    st.subheader("Book Appointment")

    patient = st.session_state.auth["patient"]
    patient_id = patient["patient_id"]

    # Show schedules first
    rows = list_doctor(None)
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    schedule_id = st.number_input("Enter schedule slot id to book", min_value=1, step=1)

    if st.button("Book"):
        ok, msg, receipt = book(int(schedule_id), patient_id)
        if ok:
            st.success(msg)
            st.json(receipt)
        else:
            st.error(msg)


elif page == "My Appointments":
    st.subheader("My Appointments")

    patient = st.session_state.auth["patient"]
    patient_id = patient["patient_id"]

    status_filter = st.selectbox("Status filter", ["CONFIRMED", "CANCELED", "ALL"])
    stat = None if status_filter == "ALL" else status_filter

    rows = list_appointment(patient_id, None, stat)
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)


elif page == "Cancel Appointment":
    st.subheader("Cancel Appointment (Patient)")

    patient = st.session_state.auth["patient"]
    patient_id = patient["patient_id"]

    # show current confirmed appointments
    rows = list_appointment(patient_id, None, "CONFIRMED")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    app_id = st.number_input("Enter appointment id to cancel", min_value=1, step=1)
    show = st.button("Show Appointment")

    if show:
        ok, msg, ap = get_appointment_by_id(int(app_id), patient_id)
        if ok:
            st.json(ap)
        else:
            st.error(msg)

    confirm = st.checkbox("I confirm I want to cancel this appointment")

    if st.button("Cancel Now"):
        if not confirm:
            st.warning("Please confirm first.")
        else:
            ok, msg = cancel_appointment(int(app_id), patient_id)
            if ok:
                st.success(msg)
            else:
                st.error(msg)


elif page == "View All Appointments":
    st.subheader("All Appointments (Admin)")

    status_filter = st.selectbox("Status filter", ["CONFIRMED", "CANCELED", "ALL"], key="admin_app_filter")
    stat = None if status_filter == "ALL" else status_filter

    rows = admin_list_all_appointments(stat)
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.caption("To cancel one, go to 'Cancel Appointment (Admin)' and use the appointment id.")


elif page == "Cancel Appointment (Admin)":
    st.subheader("Cancel Appointment (Admin)")

    # show all confirmed for convenience
    rows = admin_list_all_appointments("CONFIRMED")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    app_id = st.number_input("Enter appointment id to cancel", min_value=1, step=1, key="admin_cancel_id")
    confirm = st.checkbox("I confirm I want to cancel this appointment", key="admin_cancel_confirm")

    if st.button("Cancel Appointment", key="admin_cancel_btn"):
        if not confirm:
            st.warning("Please confirm first.")
        else:
            ok, msg = admin_cancel_appointment_by_id(int(app_id))
            if ok:
                st.success(msg)
            else:
                st.error(msg)


elif page == "Cancel Time Slot":
    st.subheader("Cancel Time Slot (Admin)")

    rows = list_doctor(None)
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    schedule_id = st.number_input("Enter schedule slot id to cancel", min_value=1, step=1, key="slot_cancel_id")
    confirm = st.checkbox("I confirm I want to cancel this slot", key="slot_cancel_confirm")

    if st.button("Cancel Slot", key="slot_cancel_btn"):
        if not confirm:
            st.warning("Please confirm first.")
        else:
            # Validate existence
            if not check_id_exist(schedule_id, "id", "doctor_schedule"):
                st.error("Invalid schedule id.")
            else:
                ok, msg = cancel_schedule_slot(int(schedule_id))
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


elif page == "Sign Up Doctor":
    st.subheader("Sign Up Doctor (Admin)")

    doc_id = st.number_input("Doctor ID", min_value=1, step=1)
    doc_name = st.text_input("Doctor Name")
    expertise = st.text_input("Expertise")

    week_days = ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday"]
    day_of_week = st.selectbox("Day of week", week_days)

    start_time = st.text_input("Start time (HH:MM) e.g. 09:00")
    end_time = st.text_input("End time (HH:MM) e.g. 17:00")
    slot_minutes = st.number_input("Slot length (minutes)", min_value=10, max_value=60, step=5)

    if st.button("Create Doctor Schedule"):
        # Validate doctor id uniqueness (simple)
        if check_id_exist(doc_id, "doctor_id", "doctor_info"):
            st.error("Doctor ID already exists.")
        else:
            # Parse times
            try:
                from datetime import datetime
                start_dt = datetime.strptime(start_time, "%H:%M")
                end_dt = datetime.strptime(end_time, "%H:%M")
                if start_dt >= end_dt:
                    st.error("End time must be after start time.")
                else:
                    ok, msg = doctor_signUP(int(doc_id), doc_name, expertise, day_of_week, start_dt, end_dt, int(slot_minutes))
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            except ValueError:
                st.error("Invalid time format. Use HH:MM.")


elif page == "Delete Doctor":
    st.subheader("Delete Doctor (Admin)")

    rows = list_doctor(None)
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    doc_id = st.number_input("Doctor ID to delete", min_value=1, step=1)
    confirm = st.checkbox("I confirm I want to delete this doctor")

    if st.button("Delete Doctor"):
        if not confirm:
            st.warning("Please confirm first.")
        else:
            ok, msg = delete_doctor(int(doc_id))
            if ok:
                st.success(msg)
            else:
                st.error(msg)


elif page == "Logout":
    st.session_state.auth = {"logged_in": False, "role": None, "patient": None}
    st.success("Logged out.")
    st.rerun()
