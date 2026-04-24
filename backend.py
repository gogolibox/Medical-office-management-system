import sqlite3
from prettytable import PrettyTable # type: ignore
from datetime import datetime, timedelta


def get_conn():
    return sqlite3.connect("clinic.db")


def doctor_signUP(doctor_id, doctor_name, expertise, day_of_week, start_t, end_t, slut_period):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # insert name and expertise of new doctor in doctor_info TABLE
        cur.execute("""
            INSERT INTO doctor_info(doctor_id, doctor_name, expertise)
            VALUES (?,?,?)"""
            , (doctor_id, doctor_name, expertise))
        conn.commit()

        # insert working hours in week days of the new doctor in doctor_schedule TABLE
        slut_end = start_t
        while True:
            slut_start = slut_end
            slut_end += timedelta(minutes=slut_period)
            if slut_end >= end_t:
                slut_end = end_t
                # inserting the incompelet last slut(maybe less that specified slut period)
                string_Stime = slut_start.strftime ("%H:%M")                            #string from time
                string_Etime = slut_end.strftime ("%H:%M")                              #string from time
                cur.execute("""
                    INSERT INTO 
                            doctor_schedule(doctor_id, day_of_week, start_time, end_time)
                    VALUES 
                            (?,?,?,?)"""
                    ,(doctor_id, day_of_week, string_Stime, string_Etime))
                # conn.commit()
                break
            
            string_Stime = slut_start.strftime ("%H:%M")        #string from time
            string_Etime = slut_end.strftime   ("%H:%M")        #string from time
        
            cur.execute("""
                INSERT INTO 
                        doctor_schedule(doctor_id, day_of_week, start_time, end_time)
                VALUES 
                        (?,?,?,?)"""
                ,(doctor_id, day_of_week, string_Stime, string_Etime))
            # conn.commit()

        conn.commit()

        #FOR UI
        return (True, "Doctor signed up successfully.")

    except sqlite3.Error as e:
        conn.rollback()
        # print("DB Error:", e)
        return (False, f"DB Error: {e}")
    finally:
        conn.close()

def book(schedule_id, patient_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # start time & end time from doctor_schedule TABLE
        cur.execute("""
            SELECT 
                    doctor_info.doctor_id,          --0
                    doctor_info.doctor_name,        --1
                    doctor_info.expertise,          --2
                    doctor_schedule.day_of_week,    --3
                    doctor_schedule.start_time,     --4
                    doctor_schedule.end_time,       --5
                    doctor_schedule.status          --6
            FROM 
                    doctor_schedule
            JOIN
                    doctor_info
            ON
                    doctor_info.doctor_id == doctor_schedule.doctor_id
            WHERE
                    doctor_schedule.id = ?
                    """
            , (schedule_id, ))
        
        row = cur.fetchone()


        #FOR UI
        if not row:
            return (False, "Schedule not found.", None)
        if row[6] == "CANCELED":
            return (False, "This time is canceled.", None)
        elif row[6] == "BOOKED":
            return (False, "This time is already booked.", None)
        

        # Interference check                                    # REPLACED with trigger
        # cur.execute("""
        #     SELECT 1 FROM appointments
        #     WHERE id = ? AND status='CONFIRMED'
        #     AND NOT (end_ts <= ? OR start_ts >= ?)
        #     LIMIT 1;
        # """, (patient_id,start_ts, end_ts))
        # if cur.fetchone():
        #     print(" time Interference: this time has been booked!")
        #     return
        

        start_ts = row[4]
        end_ts   = row[5]
        
        #delete the same record(booking now) in appointments that is canceled
        cur.execute("""
        DELETE FROM appointments
        WHERE status = "CANCELED"
          AND doctor_id = ?
          AND patient_id = ?
          AND start_ts = ?
          AND end_ts = ?
        """, (row[0], patient_id, start_ts, end_ts))
        conn.commit()
        

        # insert reservation
        cur.execute("""
            INSERT INTO 
                    appointments(doctor_id, patient_id, start_ts, end_ts)
            VALUES 
                    (?,?,?,?)"""
            , (row[0], patient_id, start_ts, end_ts))
        conn.commit()
        apId = cur.lastrowid

        #FOR UI
        receipt = {
            "appointment_id": apId,
            "doctor_id": row[0],
            "doctor_name": row[1],
            "expertise": row[2],
            "day": row[3],
            "start_time": row[4],
            "end_time": row[5],
        }
        return (True, "Appointment booked successfully.", receipt)

    except sqlite3.Error as e:
        conn.rollback()
        return (False, f"DB Error: {e}", None)
    finally:
        conn.close()

def list_appointment(patient_id, appointment_id, stat):
    conn = get_conn()
    cur = conn.cursor()

    if appointment_id is None:
        cur.execute("""
            SELECT
                a.id, a.doctor_id, a.patient_id, a.start_ts, a.end_ts, a.status, s.day_of_week
            FROM appointments a
            LEFT JOIN doctor_schedule s
            ON s.doctor_id = a.doctor_id
            AND s.start_time = a.start_ts
            AND s.end_time   = a.end_ts
            WHERE a.patient_id = ? AND (? IS NULL OR a.status = ? )
            ORDER BY a.start_ts
            """, (patient_id, stat, stat))
        
    elif patient_id is None:
        cur.execute("""
            SELECT
                a.id, a.doctor_id, a.patient_id, a.start_ts, a.end_ts, a.status, s.day_of_week
            FROM appointments a
            LEFT JOIN doctor_schedule s
            ON s.doctor_id = a.doctor_id
            AND s.start_time = a.start_ts
            AND s.end_time   = a.end_ts
            WHERE a.id = ? AND (? IS NULL OR a.status = ? )
            ORDER BY a.start_ts
            """, (appointment_id, stat, stat))
        
    rows = cur.fetchall()
    conn.close()

    #FOR UI
    return [
        {
            "id": r[0],
            "doctor_id": r[1],
            "patient_id": r[2],
            "start_ts": r[3],
            "end_ts": r[4],
            "status": r[5],
        }
        for r in rows
    ]


def list_doctor(doctor_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            doctor_schedule.id,             --0
            doctor_info.doctor_id,          --1
            doctor_info.doctor_name,        --2
            doctor_info.expertise,          --3
            doctor_schedule.day_of_week,    --4
            doctor_schedule.start_time,     --5
            doctor_schedule.end_time,       --6
            doctor_schedule.status          --7
        FROM
            doctor_info
        JOIN
            doctor_schedule
        ON
            doctor_info.doctor_id == doctor_schedule.doctor_id
        WHERE
            (? IS NULL OR doctor_info.doctor_id = ? )
        ORDER BY
            doctor_schedule.id
        """,(doctor_id, doctor_id)
    )
    
    rows = cur.fetchall()

    conn.close()
    
    return [
            {
                "id": r[0],
                "doctor_id": r[1],
                "doctor_name": r[2],
                "expertise": r[3],
                "day_of_week": r[4],
                "start_time": r[5],
                "end_time": r[6],
                "status": r[7],
            }
            for r in rows

            ]

def check_id_exist (id, column_name, table_name):
    conn = get_conn()
    cur = conn.cursor()
    try:
        query = f" SELECT {column_name} FROM {table_name} ORDER BY {column_name} "
        cur.execute(query)

        rows = cur.fetchall()

        #FOR UI
        return any(int(r[0]) == int(id) for r in rows)
        
    except sqlite3.Error as e:
        return False
    finally:
        conn.close()

def delete_doctor(doc_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM doctor_info WHERE doctor_id = ?", (doc_id,))
        cur.execute("DELETE FROM doctor_schedule WHERE doctor_id = ?", (doc_id,))
        conn.commit()
        return (True, "Doctor deleted successfully.")
    except sqlite3.Error as e:
        conn.rollback()
        return (False, f"DB Error: {e}")
    finally:
        conn.close()

def authenticate_patient(national_id: str, password: str):
    """
    Returns: (ok: bool, msg: str, patient: dict|None)
    patient dict: {"patient_id": ..., "name": ..., "last_name": ...}
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT patient_id, name, last_name
            FROM patients
            WHERE national_id = ? AND password = ?
        """, (national_id, password))
        r = cur.fetchone()
        if not r:
            return (False, "Invalid national ID or password.", None)

        patient = {"patient_id": r[0], "name": r[1], "last_name": r[2]}
        return (True, "Login successful.", patient)

    except sqlite3.Error as e:
        return (False, f"DB Error: {e}", None)

    finally:
        conn.close()



def cancel_appointment(app_id: int, patient_id: str):
    """
    Cancel an appointment belonging to the given patient.

    Returns:
        (ok: bool, msg: str)
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 1) Ensure the appointment exists and belongs to this patient
        cur.execute("""
                SELECT id, status 
                FROM appointments 
                WHERE 
                    id = ? AND patient_id = ?
                """,(app_id, patient_id),
        )
        row = cur.fetchone()
        if not row:
            return (False, "Appointment not found for this patient.")

        status = row[1]
        if status == "CANCELED":
            return (False, "This appointment is already canceled.")

        # enforce only CONFIRMED can be canceled
        # If you want to allow other statuses, remove this check.
        if status != "CONFIRMED":
            return (False, f"Only CONFIRMED appointments can be canceled (current: {status}).")

        # 2) Cancel it
        cur.execute("""
                    UPDATE appointments 
                    SET status = ? WHERE id = ? AND patient_id = ?""",
                ("CANCELED", app_id, patient_id),
        )
        conn.commit()

        #did the UPDATE actually change any row?
        if cur.rowcount == 0:
            return (False, "Cancel failed (appointment may have changed).")

        # Your trigger should free the schedule when appointment becomes CANCELED.
        return (True, "Appointment canceled successfully.")

    except sqlite3.Error as e:
        conn.rollback()
        return (False, f"DB Error: {e}")

    finally:
        conn.close()


def get_appointment_by_id(app_id: int, patient_id: str):
    """
    Returns (ok, msg, appointment_dict_or_none)
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, doctor_id, patient_id, start_ts, end_ts, status
            FROM appointments
            WHERE id = ? AND patient_id = ?
        """, (app_id, patient_id))
        r = cur.fetchone()
        if not r:
            return (False, "Appointment not found for this patient.", None)

        ap = {
            "id": r[0],
            "doctor_id": r[1],
            "patient_id": r[2],
            "start_ts": r[3],
            "end_ts": r[4],
            "status": r[5],
        }
        return (True, "OK", ap)

    except sqlite3.Error as e:
        return (False, f"DB Error: {e}", None)
    finally:
        conn.close()

def cancel_schedule_slot(schedule_id: int):
    """
    UI helper: cancel a slot in doctor_schedule and cancel matching appointments.
    Returns (ok, msg).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Cancel the slot
        cur.execute("""
            UPDATE doctor_schedule
            SET status = ?
            WHERE id = ?
        """, ("CANCELED", schedule_id))

        # Cancel matching appointments (same doctor & times)
        cur.execute("""
            UPDATE appointments
            SET status = ?
            WHERE doctor_id = (
                SELECT doctor_id FROM doctor_schedule WHERE id = ?
            )
            AND start_ts = (
                SELECT start_time FROM doctor_schedule WHERE id = ?
            )
            AND end_ts = (
                SELECT end_time FROM doctor_schedule WHERE id = ?
            )
            AND status = 'CONFIRMED'
        """, ("CANCELED", schedule_id, schedule_id, schedule_id))

        conn.commit()

        if cur.rowcount == 0:
            # Note: rowcount here refers to the LAST UPDATE (appointments)
            # The schedule update may still have worked. We keep message simple.
            return (True, "Slot canceled. (No CONFIRMED matching appointments found.)")

        return (True, "Slot canceled and matching appointments canceled.")
    except sqlite3.Error as e:
        conn.rollback()
        return (False, f"DB Error: {e}")
    finally:
        conn.close()

def register_patient(nat_id: str, name: str, last_name: str, password: str):
    """UI helper: register a new patient. Returns (ok, msg)."""
    if not (nat_id and name and last_name and password):
        return (False, "All fields are required.")

    # check duplicate
    if check_id_exist(nat_id, "national_id", "patients"):
        return (False, "This National ID already exists. Please log in.")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO patients(national_id, name, last_name, password)
            VALUES (?,?,?,?)
        """, (nat_id, name, last_name, password))
        conn.commit()
        return (True, "Signed up successfully. You can log in now.")
    except sqlite3.Error as e:
        conn.rollback()
        return (False, f"DB Error: {e}")
    finally:
        conn.close()

def admin_cancel_appointment_by_id(app_id: int):
    """
    Admin cancels any appointment by appointment id only.
    Returns (ok, msg).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT status FROM appointments WHERE id = ?", (app_id,))
        r = cur.fetchone()
        if not r:
            return (False, "Appointment not found.")

        status = r[0]
        if status == "CANCELED":
            return (False, "This appointment is already canceled.")
        if status != "CONFIRMED":
            return (False, f"Only CONFIRMED can be canceled (current: {status}).")

        cur.execute("UPDATE appointments SET status = ? WHERE id = ?", ("CANCELED", app_id))
        conn.commit()

        if cur.rowcount == 0:
            return (False, "Cancel failed (appointment may have changed).")

        return (True, "Appointment canceled successfully.")
    except sqlite3.Error as e:
        conn.rollback()
        return (False, f"DB Error: {e}")
    finally:
        conn.close()

def admin_list_all_appointments(stat=None):
    """UI helper: list all appointments for admin. Returns list[dict]."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT
                a.id, a.doctor_id, a.patient_id, s.day_of_week, a.start_ts, a.end_ts, a.status
            FROM appointments a
            LEFT JOIN doctor_schedule s
            ON s.doctor_id = a.doctor_id
            AND s.start_time = a.start_ts
            AND s.end_time   = a.end_ts
            WHERE (? IS NULL OR a.status = ?)
            ORDER BY a.start_ts
        """, (stat, stat))
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "doctor_id": r[1],
                "patient_id": r[2],
                "day_of_week": r[3],
                "start_ts": r[4],
                "end_ts": r[5],
                "status": r[6],
            }
            for r in rows
        ]
    finally:
        conn.close()

def main():

    while True:
        print("\n1)Patient \n2)Admin \n3)EXIT")
        ch = input("select:  ").strip()

        if ch == "1":
            logged_in = False

            while True:
                opt = input("\n1)Sign Up \n2)Login \n3)Cancel reservation \nselect:")

                if opt == "1":      #Sign Up
                    try:
                        while True:                                 
                            name       = input("First Name:    ")
                            last_name  = input("Last Name:     ")
                            nat_id     = input("National ID:   ")
                            if not (name and last_name and nat_id):                                 #check empty input
                                print("First name, Last name of National ID can NOT be empty. Try Again!")
                            else:
                                break

                        while True:
                            passw           = input("PASSWORD:      ")
                            check_passw     = input("PASSWORD Again:")
                            if passw == check_passw:
                                break
                            else:
                                print("Wrong password identification! Try Again.")
                        
                        if check_id_exist (nat_id, "national_id", "patients"):
                            print("This National ID exists! Try to login.")
                        else:
                            register_patient (nat_id, name, last_name, passw)
                            print("Signed In Successfully.")
                            continue

                    except sqlite3.Error as e:
                        print("DB Error:", e)

                elif opt == "2":    #Login
                    
                    try:
                        ni  = input("National Id:")
                        pas = input("Password:   ")
                        
                        #FOR UI
                        ok, msg, patient = authenticate_patient(ni, pas)

                        if ok:
                            global user_id
                            #FOR UI
                            user_id = patient["patient_id"]
                            logged_in = True
                            print(msg)
                            print(f"Welcome {patient['name']} {patient['last_name']}")

                        else:
                            print(msg)
                            continue

                    except sqlite3.Error as e:
                        print("DB Error:", e)

                elif opt == "3":    #CANCEL
                    break

                else:
                    print("Invalid option! Try Again.")
        
            if not logged_in:
                continue

            while True:
                print ("\n**Patient**")
                print("1)BOOK \n2)My appointments \n3)Cancel appointment \n4)Back")
                ch = input("select:  ").strip()

                if ch == "1":

                    # display doctor's LIST
                    list_doctor(None)

                    # INPUT
                    res = False
                    while (res == False):
                        id = int(input("id: "))
                        res = check_id_exist (id, "id", "doctor_schedule")
                        if res == False:
                                print ("ID does NOT exist! Try Again.")

                    book(id, user_id)             

                elif ch == "2":
                    # d = input("patient_id: ")
                    list_appointment(user_id,None,"CONFIRMED")
                
                elif ch == "3":
                    
                    while True:
                        app_id = int(input("Enter appointment id to cancel (or 0 to go back): "))
                        if app_id == 0:
                            break

                        ok, msg, ap = get_appointment_by_id(app_id, user_id)
                        if not ok:
                            print(msg)
                            continue

                        # display the appointment
                        print(ap)

                        confirm = input("Cancel this appointment? (y/n): ").strip().lower()
                        if confirm != "y":
                            continue
                        else:
                            ok, msg = cancel_appointment(app_id, user_id)
                            print(msg)
                        if ok:
                            break

                elif ch == "4":
                    break

                else:
                    print("INVALID option!, try again.")

        elif ch == "2":

            #ADMIN password
            admin_pass = "1234"
            while True:
                sec_pass = input("Admin Password: ")
                if sec_pass == admin_pass:
                    print ("CORRECT!")
                    break
                else:
                    print("Wrong Password! Try Again.")
                
            while True:
                print ("\n**Admin**")
                print("1)Table of schedules \n2)SignUP doctor \n3)Cancel appointment(admin side) \n4)Cancel time slot \n5)Delete doctor \n6)Back")
                ch = input("select:  ").strip()
                
                if ch == "1":
                    list_doctor(None)
                
                elif ch == "2":
                    while True:
                        docId = int(input("doctor ID: "   ))
                        if (check_id_exist (docId, "doctor_id", "doctor_schedule")):
                            print("doctor id repeted! Try Again.")
                        else:
                            break

                    docName = input("doctor name: "      )
                    exper   = input("doctor expertise: " )

                    weekDays = ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday"]

                    status = "y"
                    while status == "y":
                        while True:
                            print(weekDays)
                            day_of_week = input("Enter the day of the week: " )
                            if day_of_week in weekDays:
                                break
                            else:
                                print ("Non valid entery!\nTry Again.")

                        while True:
                            while True:                                                     #catch Invalid input
                                St = input("Starting working hour: (HH:MM): " )
                                try:
                                    start_dt = datetime.strptime(St,"%H:%M"   )             #string parsed time
                                    break
                                except ValueError:
                                    print ("Invalid time format! Please use HH:MM")

                            while True:                                                     #catch Invalid input
                                Et = input("ending working hour:   (HH:MM): " )
                                try:
                                    end_dt = datetime.strptime(Et,"%H:%M"     )             #string parsed time
                                    break
                                except ValueError:
                                    print ("Invalid time format! Please use HH:MM")
                            if (St < Et):
                                break
                            else:
                                print("end time should be after start time! Try Again.")
                            
                        
                        while True:                                                         #catch Invalid input
                            slut_p = int(input("the length of each period you want: (Minutes 10-60): " ))
                            if slut_p > 60 or slut_p < 10:
                                print ("Invalid Number! Try Again")
                            else:
                                break
                        
                        doctor_signUP(docId, docName, exper, day_of_week, start_dt, end_dt, slut_p)

                        while True:
                            status = input("Continue? (y/n) ")
                            if (status == "n") or (status == "y"):
                                break
                            else:
                                print ("Invalid Option! Try Again")

                elif ch == "3":
                    rows = admin_list_all_appointments(None)
                    print(rows)  # CLI only (Streamlit will display a dataframe)

                    app_id = int(input("Enter appointment id to cancel (0 to go back): "))
                    if app_id != 0:
                        ok, msg = admin_cancel_appointment_by_id(app_id)
                        print(msg)

                elif ch == "4":
                    list_doctor(None)
                    while True:
                        schedule_id = input("Enter the appointment id: ")
                        if (check_id_exist (schedule_id,"id","doctor_schedule")):
                            ok, msg = cancel_schedule_slot(schedule_id)
                            print(msg)
                            break
                        else:
                            print("INVALID id! Try Again.")
                    
                elif ch == "5":
                    
                    list_doctor(None)
                    
                    doc_id = input ("Enter doctor id: ")
                    list_doctor(doc_id)
                    print ("Do you want to delete this doctor?")
                    
                    while True:
                        ans = input("y/n ")
                        if (ans == "n") or (ans == "y"):
                            break
                        else:
                            print ("Invalid Option! Try Again")

                    if ans == "y":
                        delete_doctor(doc_id)
                        list_doctor(None)


                elif ch == "6":
                    break
                
                else:
                    print("INVALID option!, try again.")

        elif ch == "3":
            break
            
        else:
            print("INVALID option!, try again.")

if __name__ == "__main__":
    main()