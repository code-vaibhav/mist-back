import sqlite3

try:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    print("Connected to SQLite")

except sqlite3.Error as error:
    print('Error occurred - ', error)

jobs_table = """ CREATE TABLE jobs (
            uid VARCHAR(255) PRIMARY KEY,
            filename CHAR(50) NOT NULL,
            submitted_at INT NOT NULL,
            status CHAR(10) DEFAULT NULL,
            pid CHAR(15) DEFAULT NULL
            completed_at INT DEFAULT NULL
        ); """
process_table = """ CREATE TABLE processes (
            uid VARCHAR(255) NOT NULL,
            filename CHAR(50) NOT NULL,
            FOREIGN KEY (uid) REFERENCES jobs(uid)
        );"""
cursor.execute("DROP TABLE IF EXISTS jobs")
cursor.execute("DROP TABLE IF EXISTS processes")
cursor.execute(jobs_table)
cursor.execute(process_table)
