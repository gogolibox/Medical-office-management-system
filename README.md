# Clinic Appointment System

## Overview

This project is a clinic appointment management system developed in Python. It supports both a web-based interface using Streamlit and a command-line interface (CLI).

The system allows patients to register, log in, view schedules, book appointments, and cancel them. Administrators can manage doctors, schedules, and appointments.

The design separates backend logic from the user interface, allowing multiple interfaces to use the same core functionality.

---

## Features

### Patient

* Sign up and login
* View doctor schedules
* Book appointments
* View personal appointments
* Cancel appointments

### Admin

* Login (admin password required)
* Add doctors and generate schedules
* View all appointments
* Cancel any appointment
* Cancel schedule slots
* Delete doctors

---

## Project Structure

```
clinic-appointment-system/
│
├── app_streamlit.py     # Streamlit web interface
├── app_cli.py           # Command-line interface
├── backend.py           # Core logic and database operations
├── init_db.py           # Database initialization (tables and triggers)
├── clinic.db            # SQLite database (created after initialization)
│
└── README.md
```

---

## Technologies Used

* Python
* SQLite
* Streamlit
* Pandas

---

## Getting Started

### 1. Install dependencies

```
pip install streamlit pandas
```

### 2. Initialize the database

```
python3 init_db.py
```

### 3. Run the application

Web interface:

```
streamlit run app_streamlit.py
```

Command-line interface:

```
python3 app_cli.py
```

---

## Database Design

### Tables

patients

* patient_id (Primary Key)
* national_id
* name
* last_name
* password

doctor_info

* doctor_id (Primary Key)
* doctor_name
* expertise

doctor_schedule

* id (Primary Key)
* doctor_id (Foreign Key)
* day_of_week
* start_time
* end_time
* status (AVAILABLE, BOOKED, CANCELED)

appointments

* id (Primary Key)
* doctor_id (Foreign Key)
* patient_id (Foreign Key)
* start_ts
* end_ts
* status (CONFIRMED, CANCELED)

---

## Database Logic (Triggers)

The system uses SQLite triggers to enforce consistency:

* Prevent overlapping appointments for the same doctor
* Prevent overlapping appointments for the same patient
* Automatically mark a schedule slot as BOOKED after reservation
* Automatically free a slot when an appointment is canceled

---

## Important Notes

* Admin password is hardcoded as: 1234
* Time format must be HH:MM
* Schedule slots are generated automatically when adding a doctor
* Canceling a time slot also cancels related appointments
* Conflict handling is enforced at the database level

---

## Future Improvements

* Secure password storage (hashing)
* Improved authentication system
* Enhanced user interface
* Deployment to a web server
* Notification system (email or SMS)

---

## Author

Alireza Ranjbar  
email: alireza.ranjbar1384@gmail.com
