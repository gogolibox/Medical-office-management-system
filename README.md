# Clinic Appointment System

## Description

This project is a Clinic Appointment Management System developed in Python.
It provides a web-based interface using Streamlit and uses SQLite as the database.

The system supports two roles:

* Patients: can register, log in, book, view, and cancel appointments
* Admin: can manage doctors, schedules, and all appointments

The system ensures data consistency using database triggers for conflict prevention and automatic updates.

---

## Technologies Used

* Python
* SQLite
* Streamlit
* Pandas

---

## Project Structure

* `app.py` → Streamlit frontend (UI and navigation)
* `backend.py` → Business logic and database operations
* `init_db.py` → Database creation (tables + triggers)
* `clinic.db` → SQLite database (generated after running init_db.py)

---

## How to Run

1. Install required packages:
   pip install streamlit pandas

2. Initialize the database:
   python3 init_db.py

3.1. Run CLI version:  
     python3 cli_app.py

3.2. Run Web version:  
      streamlit run app_streamlit.py  
      Open in browser:  
      http://localhost:8501  

---

## System Features

Patient Features:

* Sign up with national ID
* Login securely
* View doctor schedules
* Book appointments
* View personal appointments
* Cancel appointments

Admin Features:

* Login (password: 1234)
* Add doctors and generate weekly schedules
* View all appointments
* Cancel any appointment
* Cancel schedule slots (with cascading effect)
* Delete doctors

---

## Database Design

Tables:

1. patients

   * patient_id (PK)
   * national_id
   * name
   * last_name
   * password

2. doctor_info

   * doctor_id (PK)
   * doctor_name
   * expertise

3. doctor_schedule

   * id (PK)
   * doctor_id (FK)
   * day_of_week
   * start_time
   * end_time
   * status (AVAILABLE / BOOKED / CANCELED)

4. appointments

   * id (PK)
   * doctor_id (FK)
   * patient_id (FK)
   * start_ts
   * end_ts
   * status (CONFIRMED / CANCELED)

---

## Database Triggers (Important Logic)

* Prevent doctor double-booking
  → A doctor cannot have overlapping confirmed appointments

* Prevent patient schedule conflicts
  → A patient cannot book overlapping appointments

* Auto-reserve slot
  → When an appointment is created, the schedule slot becomes BOOKED

* Auto-free slot
  → When an appointment is canceled, the slot becomes AVAILABLE

---

## Important Notes

* Admin password is hardcoded: 1234
* Time format must be HH:MM
* Schedule slots are generated automatically when adding a doctor
* Canceling a schedule slot by admin also cancels related appointments
* Conflict handling is enforced at the database level (via triggers)

---

## Future Improvements

* Secure password hashing
* Role-based authentication system
* Improved UI/UX
* Deployment (web hosting)
* Notification system (email/SMS)

---

## Author

Alireza Ranjbar
email: alireza.ranjbar1384@gmail.com
