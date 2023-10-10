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

    process = subprocess.Popen(['qsub', os.path.join(app.config['UPLOAD_FOLDER'], filename, 'hpcrunme')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
    hpcrunme = os.path.join(app.config['UPLOAD_FOLDER'], file.filename.split('.')[0], 'hpcrunme')

    with open(linux_run, mode="w") as f:
        f.write(
            f"""#!/bin/sh
            export LD_LIBRARY_PATH=/apps/libs/fftw/3.3.10/lib 
            /home/subham/varad/software/MIST/Default/mist -f {"".join([os.path.join('simulation', file.filename.split('.')[0], path) for path in paths])}""")
    
    with open(hpcrunme, mode="w") as f:
        f.write(
            f"""#!/bin/bash
                #PBS -N mini-1
                #PBS -l nodes=1:ppn=1,walltime=20:00:00
                #PBS -j oe
                cd $PBS_O_WORKDIR
                export I_MPI_FABRICS=shm:dapl
                #export I_MPI_MPD_TMPDIR=/scratch/varaddaoo20


                module load compiler/openmpi-4.1.4
                module load fftw-3.3.10
                mpirun -machinefile $PBS_NODEFILE -np 1 {os.path.join(app.config["UPLOAD_FOLDER"], file.filename.split(".")[0], 'linux_run.sh')} > {os.path.join(app.config["UPLOAD_FOLDER"], file.filename.split(".")[0], 'out')} """
        )
        
    os.chmod(linux_run, os.stat(linux_run).st_mode | 0o0111)
    os.chmod(hpcrunme, os.stat(hpcrunme).st_mode | 0o0111)

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

    return jsonify(list(stats.values())), 200


@app.route('/getresult/<uid>', methods=['GET'])
def get_result(uid):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], uid)
    result_zip = os.path.join(folder, 'results.zip')

    if not os.path.exists(result_zip):
        with zipfile.ZipFile(result_zip, 'w') as zip_ref:
            for _, subdirs, _ in os.walk(folder):
                for subdir in subdirs:
                    for file in os.listdir(os.path.join(folder, subdir)):
                        if "result" in file or "dump" in file: 
                            file_path = os.path.join(folder, subdir, file)
                            arcname = os.path.relpath(file_path, folder)
                            zip_ref.write(file_path, arcname)

    try:
        return send_file(result_zip, as_attachment=True), 200
    except Exception as e:
        return str(e), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
