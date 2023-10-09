from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import zipfile
import subprocess
import uuid
import sqlite3
import multiprocessing

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'simulation')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def worker(filename, uid):
    print('start process')

    process = subprocess.Popen([os.path.join(app.config['UPLOAD_FOLDER'], 'hpcrunme'), os.path.join(
        app.config['UPLOAD_FOLDER'], filename, 'linux_run.sh')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        cursor.execute(
            "UPDATE jobs SET pid = ?, status='Running' WHERE uid = ?", (process.pid, uid))

    return_code = process.wait()
    print('completed')
    print(return_code)
    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        cursor.execute(
            "UPDATE jobs SET status = ? WHERE uid = ?", ('Completed' if return_code == 0 else 'Error', uid))


@app.route('/postjob', methods=['POST'])
def execute():
    if ('zipFile' not in request.files):
        return jsonify({'error': 'No file present'}), 400

    file = request.files['zipFile']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        uid = uuid.uuid4().hex
        cursor.execute(
            "INSERT INTO jobs (uid, filename, submitted_at) VALUES (?, ?, datetime('now', 'localtime'))", (uid, file.filename))

    file.filename = uid + '.zip'
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

    with zipfile.ZipFile(os.path.join(app.config['UPLOAD_FOLDER'], file.filename), 'r') as zip_ref:
        zip_ref.extractall(os.path.join(
            app.config['UPLOAD_FOLDER'], file.filename.split('.')[0]))

    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        for path in os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], file.filename.split('.')[0])):
            cursor.execute(
                "INSERT INTO processes (uid, filename) VALUES (?, ?)", (uid, path))

    paths = os.listdir(os.path.join(
        app.config['UPLOAD_FOLDER'], file.filename.split('.')[0]))

    linux_run = os.path.join(
        app.config['UPLOAD_FOLDER'], file.filename.split('.')[0], 'linux_run.sh')
    with open(linux_run, mode="w") as f:
        f.write(
            f"""#!/usr/bin/sh
            export LD_LIBRARY_PATH=/home/vaibhav/MIST/software/fftw/fftw3 
            /home/vaibhav/MIST/software/MIST/Default/mist -f {"".join([os.path.join('simulation', file.filename.split('.')[0], path) for path in paths])}""")

    st = os.stat(linux_run)
    os.chmod(linux_run, st.st_mode | 0o0111)

    worker_process = multiprocessing.Process(
        target=worker, args=(file.filename.split('.')[0], uid))
    worker_process.start()

    return jsonify("Job Submitted Successfully"), 200


@app.route('/getjobs', methods=['GET'])
def get_jobs():
    query = """ SELECT j.uid, j.filename, j.submitted_at, p.filename, j.pid, j.status
                FROM jobs as j
                LEFT JOIN processes as p
                ON j.uid = p.uid
                ORDER BY j.status
    """
    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        stats = {}
        for res in cursor.execute(query).fetchall():
            if res[0] in stats:
                stats[res[0]].processes.push(res[3])
            else:
                stats[res[0]] = ({'uid': res[0], 'filename': res[1], 'submitted_at': res[2],
                                 'pid': res[4], 'status': res[5], 'processes': [res[3]]})

    return list(stats.values()), 200


@app.route('/getresult/<uid>', methods=['GET'])
def get_result(uid):
    result_folder = os.path.join(app.config['UPLOAD_FOLDER'], uid)
    result_zip_file = os.path.join(result_folder, 'results.zip')

    if not os.path.exists(result_zip_file):
        with zipfile.ZipFile(result_zip_file, 'w') as zip_ref:
            for subdir, _, files in os.walk(result_folder):
                for file in files:
                    file_path = os.path.join(subdir, file)
                    arcname = os.path.relpath(file_path, result_folder)
                    zip_ref.write(file_path, arcname=arcname)

    try:
        return send_file(result_zip_file, as_attachment=True), 200
    except Exception as e:
        return str(e), 500


if __name__ == "__main__":
    app.run(debug=True, port=8080)
