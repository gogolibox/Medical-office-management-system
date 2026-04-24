import sqlite3

# connecting to/creating(if does not exit) the database file
conn = sqlite3.connect("clinic.db")
cur = conn.cursor()

# creating the table
cur.execute("""
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    start_ts VARCHAR(255) NOT NULL,
    end_ts VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL DEFAULT 'CONFIRMED',
    FOREIGN KEY (doctor_id) REFERENCES doctor_info(doctor_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
            
    --UNIQUE(doctor_id, start_ts)
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS doctor_info (
    doctor_id INTEGER PRIMARY KEY,
    doctor_name VARCHAR(255) NOT NULL,
    expertise VARCHAR(255) NOT NULL   
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS doctor_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    day_of_week VARCHAR(255) NOT NULL,                 
    start_time VARCHAR(255) NOT NULL,                     -- '08:00'
    end_time   VARCHAR(255) NOT NULL,                     -- '08:30'
    status     VARCHAR(255) NOT NULL DEFAULT 'AVAILABLE',
    FOREIGN KEY (doctor_id) REFERENCES doctor_info(doctor_id) ON DELETE CASCADE,
    UNIQUE (doctor_id, day_of_week, start_time)   -- prevent duplicates
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    national_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL
);
""")

cur.executescript("""
    -- TRIGGER: prevent overlapping confirmed appointments for the SAME DOCTOR
    CREATE TRIGGER IF NOT EXISTS prevent_overlap
    BEFORE INSERT ON appointments
    BEGIN
        SELECT
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM appointments
                    WHERE doctor_id = NEW.doctor_id
                      AND status = 'CONFIRMED'
                      AND NEW.start_ts < end_ts
                      AND NEW.end_ts   > start_ts
                )
                THEN RAISE(ABORT, 'Slot already booked for this doctor')
            END;
    END;
                  
    -- TRIGGER: prevent overlapping confirmed appointments for the SAME PATIENT
    CREATE TRIGGER IF NOT EXISTS prevent_patient_overlap
    BEFORE INSERT ON appointments
    BEGIN
        SELECT
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM appointments
                    JOIN doctor_schedule ON appointments.doctor_id = doctor_schedule.doctor_id
                    WHERE patient_id = NEW.patient_id
                    AND doctor_schedule.day_of_week = (SELECT day_of_week FROM doctor_schedule WHERE doctor_id = NEW.doctor_id)
                    AND status = 'CONFIRMED'
                    AND NEW.start_ts < end_ts
                    AND NEW.end_ts   > start_ts
                )
                THEN RAISE(ABORT, 'Patient already has an overlapping appointment')
            END;
    END;

    -- TRIGGER: mark slot as BOOKED when an appointment is created
    CREATE TRIGGER IF NOT EXISTS reserve_slot
    AFTER INSERT ON appointments
    BEGIN
        UPDATE doctor_schedule
        SET status = 'BOOKED'
        WHERE doctor_id = NEW.doctor_id
          AND start_time = NEW.start_ts
          AND end_time   = NEW.end_ts;
    END;

    -- TRIGGER: free slot when appointment is canceled
    CREATE TRIGGER IF NOT EXISTS free_slot_on_cancel
    AFTER UPDATE OF status ON appointments
    WHEN NEW.status = 'CANCELED'
    BEGIN
        UPDATE doctor_schedule
        SET status = 'AVAILABLE'
        WHERE doctor_id = NEW.doctor_id
          AND start_time = NEW.start_ts
          AND end_time   = NEW.end_ts;
    END;
""")
conn.commit()
conn.commit()
conn.close()
