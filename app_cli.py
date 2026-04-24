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
        print("doctor signed up SUCCESSFULLY!")

        list_doctor(None)

    except sqlite3.Error as e:
        print("DB Error:", e)
        conn.rollback()
    finally:
        conn.close()

def book(app_id, patient_id):
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
            , (app_id, ))
        
        row = cur.fetchone()

        if row[6] == "CANCELED":
            print("this time is canceled! Try Again.")
            return
        
        # elif row[6] == "BOOKED":
        #     print("this time is BOOKED! Try Again.")
        #     return
        
        start_ts = row[4]
        end_ts   = row[5]
        
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
        # print("test: DELETED")

        # insert reservation
        cur.execute("""
            INSERT INTO 
                    appointments(doctor_id, patient_id, start_ts, end_ts)
            VALUES 
                    (?,?,?,?)"""
            , (row[0], patient_id, start_ts, end_ts))
        conn.commit()
        apId = cur.lastrowid

        #change the status in doctor schedule to BOOKED            # REPLACED with trigger
        # query = f"""
        #     UPDATE doctor_schedule
        #     SET status = ?
        #     WHERE id = ?
        #     """
        # cur.execute(query, ("BOOKED", app_id))
        # conn.commit()
        print("appointment booked SUCCESSFULLY!")
        
        #Printing receipt
        query = f"""SELECT 
                        id,
                        doctor_id,
                        start_ts,
                        end_ts
                    FROM
                        appointments
                    WHERE
                        id = ?
                    """
        cur.execute(query, (apId,))
            
        app_rows = cur.fetchone()
  
        print("\nRECEIPT: Appointment ID:", app_rows[0])
        print("           Doctor ID:"     , app_rows[1])
        print("           Doctor name:"   , row[1])
        print("           expertise:"     , row[2])
        print("           day:"           , row[3])
        print("           Start time:"    , app_rows[2])
        print("           End time:"      , app_rows[3])
        print("REMEBER YOUR Appointment ID in case of need to change your appointment!!")

    except sqlite3.Error as e:
        print("DB Error:", e)
        conn.rollback()
    finally:
        conn.close()

def list_appointment(patient_id, appointment_id, stat):
    conn = get_conn()
    cur = conn.cursor()
    if appointment_id is None:    
        cur.execute("""
            SELECT doctor_id, patient_id, start_ts, end_ts, status
            FROM appointments
            WHERE patient_id = ? AND (? IS NULL OR status = ? )
            ORDER BY start_ts
            """, (patient_id, stat, stat))
        
    elif patient_id is None:    
        cur.execute("""
            SELECT doctor_id, patient_id, start_ts, end_ts, status
            FROM appointments
            WHERE id = ? AND (? IS NULL OR status = ? )
            ORDER BY start_ts
            """, (appointment_id, stat, stat))
        
    rows = cur.fetchall()

    myTable = PrettyTable(["doctor_id", "patient_id", "start_ts", "end_ts", "status"])

    for r in rows:
        myTable.add_row([r[0], r[1], r[2], r[3], r[4]])

    print (myTable)

    conn.close()

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

    myTable = PrettyTable(["id", "doctor_id", "doctor_name", "expertise", "week day", "start time", "end time", "statuse"])

    for r in rows:
        myTable.add_row([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]])

    print (myTable)

    conn.close()


def check_id_exist (id, column_name, table_name):
    conn = get_conn()
    cur = conn.cursor()
    try:
        query = f" SELECT {column_name} FROM {table_name} ORDER BY {column_name} "
        cur.execute(query)
            
        rows = cur.fetchall()

        for r in rows:
            if int(r[0]) == int(id):
                return True
        return False
        
    except sqlite3.Error as e:
        print("DB Error:", e)
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":

    while True:
        print("\n1)Patient \n2)Admin \n3)EXIT")
        ch = input("select:  ").strip()

        if ch == "1":
            logged_in = False

            while True:
                opt = input("\n1)Sign Up \n2)Login \n3)Cancel \nselect:")

                if opt == "1":      #Sign Up
                    conn = get_conn()
                    cur = conn.cursor()
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
                            cur.execute(""" INSERT INTO 
                                                    patients(national_id, name, last_name, password)
                                            VALUES
                                                    (?,?,?,?)"""
                                        , (nat_id, name, last_name, passw))
                            conn.commit()
                            print("Signed In Successfully.")
                            continue

                    except sqlite3.Error as e:
                        print("DB Error:", e)
                        conn.rollback()

                    finally:
                        conn.close()

                elif opt == "2":    #Login
                    conn = get_conn()
                    cur = conn.cursor()
                    try:
                        ni  = input("National Id:")
                        pas = input("Password:   ")
                        
                        #check if the inputs are already signed up
                        id_res   = check_id_exist(ni, "national_id", "patients")
                        pass_res = check_id_exist(pas, "password", "patients")

                        if id_res and pass_res:
                            cur.execute("""SELECT patient_id
                                            FROM patients
                                            WHERE national_id = ? AND password = ?"""
                                            , (ni, pas))
                            
                            global user_id
                            user_id = (cur.fetchone())[0]
                            logged_in = True
                            print ("Logged in successfuly")

                            #display user info
                            cur.execute(""" SELECT 
                                                patient_id, name, last_name
                                            FROM
                                                patients
                                            WHERE
                                                patient_id = ?
                                            """
                                            , (user_id,))
                            r = cur.fetchone()
                            
                            myTable = PrettyTable(["patient_id", "name", "last name"])
                            myTable.add_row([r[0], r[1], r[2]])
                            print (myTable)
                            
                            #END
                            break
                        else:
                            print("National id or password is wrong! Try Again")
                    
                    except sqlite3.Error as e:
                        print("DB Error:", e)
                        conn.rollback()

                    finally:
                        conn.close()

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

                    conn = get_conn()
                    cur = conn.cursor()

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
                
                    conn.close()

                elif ch == "2":
                    # d = input("patient_id: ")
                    list_appointment(user_id,None,"CONFIRMED")
                
                elif ch == "3":

                    conn = get_conn()
                    cur = conn.cursor()

                    ans = "n"
                    while ans == "n":    
                        print ("please enter the Appoitment ID provided in your receipt!")
                        
                        while True:
                            app_id = int(input ("Appointment ID: "))

                            #checking that the entered appointment id, belongs to the logged in user
                            cur.execute(""" SELECT 1 FROM appointments 
                                            WHERE id = ? AND patient_id = ?
                                            """, (app_id, user_id))
                            # res = check_id_exist (app_id, "id", "appointments") and if cur.fetchone()
                            if not cur.fetchone():
                                print ("Appointment id does NOT exist! Try Again.")
                            else:
                                break

                        #approve the appointment
                        print ("Is this the appointment you intended to cancel?")
                        
                        list_appointment(None, app_id, "CONFIRMED")
                        
                        while True:
                            ans = input ("y/n ")
                            if (ans == "y" or ans == "n"):
                                break
                            else:
                                print ("wrong option! y/n")
                    
                    #change status from "CONFIRMED" --> "CANCELED"
                    if ans == "y":
                        query = f"""
                            UPDATE appointments
                            SET status = ?
                            WHERE id = ? AND status = ?
                            """
                        cur.execute(query, ("CANCELED", app_id, "CONFIRMED"))
                        conn.commit()

                    
                    #change status from "BOOKED" --> "AVAILABLE"            # REPLACED with trigger
                        # cur.execute("""
                        #                 SELECT doctor_id, start_ts, end_ts
                        #                 FROM appointments
                        #                 WHERE id = ?
                        #             """, (app_id,))
                        # row = cur.fetchone()

                        # query = f"""
                        #     UPDATE doctor_schedule
                        #     SET status = ?
                        #     WHERE doctor_id = ? AND (start_time = ? AND end_time = ?)
                        #     """
                        # cur.execute(query, ("AVAILABLE", row[0], row[1], row[2]))
                        # conn.commit()
                        print ("**Appointment canceled SUCCESSFULLY**")

                    conn.close()

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
                print("1)Table of schedules \n2)SignUP doctor \n3)Update reservation \n4)Cancel time \n5)Delete doctor \n6)Back")
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

                    while True:
                        d = input("appointment id (from RECEIPT): ")
                        if (check_id_exist (d,"id","appointments")):
                            break
                        else:
                            print("INVALID id! Try Again.")
                            
                
                    list_appointment(None, d, None)

                    conn = get_conn()
                    cur = conn.cursor()
                    
                    docID = input ("doctor_id:  ")
                    # patID = input ("patient_id: ")
                    St    = input ("start_ts:   ")
                    En    = input ("end_ts:     ")

                    query = f"""
                        UPDATE appointments
                        SET docotor_id = ?, patient_id = ?, start_ts = ?, end_ts = ?
                        WHERE id = ? 
                        """
                    cur.execute(query, (docID, user_id, St, En, d))
                    conn.commit()

                    list_appointment(None, d, None)
                    conn.close()

                elif ch == "4":
                    conn = get_conn()
                    cur = conn.cursor()

                    list_doctor(None)
                    while True:
                        schedule_id = input("Enter the appointment id: ")
                        if (check_id_exist (schedule_id,"id","doctor_schedule")):
                            break
                        else:
                            print("INVALID id! Try Again.")
                            
                            
                    query = f"""
                        UPDATE doctor_schedule
                        SET status = ?
                        WHERE id = ?
                        """
                    cur.execute(query, ("CANCELED", schedule_id))

                    query = f"""
                        UPDATE appointments
                        SET status = ?
                        WHERE   doctor_id =  ( SELECT doctor_id
                                              FROM doctor_schedule
                                              WHERE id = ?)
                                AND
                                start_ts  = ( SELECT start_time
                                              FROM doctor_schedule
                                              WHERE id = ?)
                                AND
                                end_ts    = ( SELECT end_time
                                              FROM doctor_schedule
                                              WHERE id = ?)
                        """
                    cur.execute(query, ("CANCELED", schedule_id, schedule_id, schedule_id))
                    conn.commit()
                    print("Canceled successfully.")

                    conn.close()

                elif ch == "5":
                    conn = get_conn()
                    cur = conn.cursor()

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
                        query = "DELETE FROM doctor_info WHERE doctor_id = ?;"
                        cur.execute(query, (doc_id,))
                        query = "DELETE FROM doctor_schedule WHERE doctor_id = ?;"
                        cur.execute(query, (doc_id,))
                        conn.commit()
                        print("Deleted successfully.")
                        list_doctor(None)


                    conn.close()

                elif ch == "6":
                    break
                
                else:
                    print("INVALID option!, try again.")

        elif ch == "3":
            break
            
        else:
            print("INVALID option!, try again.")