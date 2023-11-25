from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
import os
from zipfile import ZipFile
import subprocess
import uuid
import sqlite3
import multiprocessing
import time
import matplotlib.pyplot as plt
import numpy as np
import shutil
from pymongo import MongoClient

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', "https://mist-front-one.vercel.app"], supports_credentials=True)
client = MongoClient('mongodb+srv://vaibhavgoyal2506:OWBDv57eHgP1hybg@cluster0.oupzcx4.mongodb.net/?retryWrites=true&w=majority')
db = client['projects']  # Replace 'your_database' with your database name
jobs = db['jobs']  # Replace 'your_collection' with your collection name

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'simulation')

def worker(uid):
    process = subprocess.Popen(['qsub', os.path.join(app.config['UPLOAD_FOLDER'], uid, 'hpcrunme')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if stderr:
        print(f"Error: {stderr.decode('utf-8')}")
        with sqlite3.connect('database.db') as con:
            cursor = con.cursor()
            cursor.execute(
                "UPDATE jobs SET status='Error', completed_at=datetime('now', 'localtime') WHERE uid = ?", (uid))
    else:
        job_id = stdout.decode('utf-8').strip()
        
        result = subprocess.run(['qstat', job_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode('utf-8')
        stderr = result.stderr.decode('utf-8')
        
        if(result.returncode != 0):
            print(stderr)
        
        with sqlite3.connect('database.db') as con:
            cursor = con.cursor()
            cursor.execute(
                "UPDATE jobs SET pid=?, status=? WHERE uid = ?", (job_id, 'Running' if ' R ' in stdout else 'Queued', uid))
        
        flag = 0
        while True:
            # Run the qstat command to check the job status
            result = subprocess.run(['qstat', job_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout = result.stdout.decode('utf-8')
            stderr = result.stderr.decode('utf-8')
            
            if(result.returncode != 0):
                print(stderr)

            if not flag and ' R ' in stdout:
                with sqlite3.connect('database.db') as con:
                    cursor = con.cursor()
                    cursor.execute(
                        "UPDATE jobs SET status=? WHERE uid = ?", ('Running', uid))
                flag = 1
                
                
            if ' R ' not in stdout and ' Q ' not in stdout:
                all = True
                for _, subdirs, _ in os.walk(os.path.join(app.config['UPLOAD_FOLDER'], uid)):
                    for subdir in subdirs:
                        curr = False
                        for file in os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], uid, subdir)):
                            if "result" in file:
                                curr = True
                                break
                        all = (all and curr)
                    
                with sqlite3.connect('database.db') as con:
                    cursor = con.cursor()
                    cursor.execute(
                        "UPDATE jobs SET status=?, completed_at=datetime('now', 'localtime') WHERE uid = ?", ('Completed' if all else 'Error',uid))
                
                break

            # Sleep for a while before checking the status again
            time.sleep(120)


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

    with ZipFile(os.path.join(app.config['UPLOAD_FOLDER'], file.filename), 'r') as zip_ref:
        zip_ref.extractall(os.path.join(
            app.config['UPLOAD_FOLDER'], uid))

    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        for path in os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], uid)):
            cursor.execute(
                "INSERT INTO processes (uid, filename) VALUES (?, ?)", (uid, path))

    paths = os.listdir(os.path.join(
        app.config['UPLOAD_FOLDER'], uid))

    linux_run = os.path.join(
        app.config['UPLOAD_FOLDER'], uid, 'linux_run.sh')
    hpcrunme = os.path.join(app.config['UPLOAD_FOLDER'], uid, 'hpcrunme')

    with open(linux_run, mode="w") as f:
        f.write(
            f"""#!/bin/sh
            export LD_LIBRARY_PATH=/apps/libs/fftw/3.3.10/lib 
            /home/subham/varad/software/MIST/Default/mist -f {"".join([os.path.join('simulation', uid, path) for path in paths])}""")
    
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
        target=worker, args=(uid,))
    worker_process.start()

    return jsonify("Job Submitted Successfully"), 200


@app.route('/getjobs', methods=['GET'])
def get_jobs():
    query = """ SELECT j.uid, j.filename, j.submitted_at, p.filename, j.pid, j.status, j.completed_at
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
                stats[res[0]] = ({'uid': res[0], 'filename': res[1], 'submitted_at': res[2], 'completed_at': res[6],
                                 'pid': res[4], 'status': res[5], 'processes': [res[3]]})

    return jsonify(list(stats.values())), 200

def strip_val(n):
    return not not n.strip()

@app.route('/getresult/<uid>', methods=['GET'])
def get_result(uid):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], uid)
    result_zip = os.path.join(folder, 'results.zip')
    
    if os.path.exists(result_zip):
        os.remove(result_zip)
        
    with ZipFile(result_zip, 'w') as zip_ref:
        for _, subdirs, _ in os.walk(folder):
            for subdir in subdirs:
                # x, y, z = [], [], []
                # with open(os.path.join(app.config['UPLOAD_FOLDER'], uid, subdir, 'dump.xyz0')) as f:
                #     for line in f:
                #         vals = list(filter(strip_val, line.split(' ')))
                #         if(len(vals) == 4):
                #             x.append(vals[1])
                #             y.append(vals[2])
                #             z.append(vals[3])
                
                # x = np.array(x, dtype=np.float32)
                # y = np.array(y, dtype=np.float32)
                # z = np.array(z, dtype=np.float32)
                
                # fig = plt.figure()
                # ax = fig.add_subplot(111, projection='3d')
                # surf = ax.scatter(y, z, x, c='r', marker='o')
                # plt.savefig(os.path.join(folder, subdir, 'points.jpg'), format='jpg')     
                          
                x, y = [],[]
                with open(os.path.join(app.config['UPLOAD_FOLDER'], uid, subdir, 'result.prop.0')) as f:
                    first_line = f.readline()
                    arr=list(filter(lambda s: 'molecule' in s, first_line.split(' ')))
                    
                    for line in f:
                        vals = list(filter(strip_val, line.split(' ')))
                        x.append(vals[0])
                        y.append(vals[1:len(arr)+1])
                    
                    x = np.array(x, dtype=np.uint16)
                    y = np.array(y, dtype=np.float32)
                    for i in range(len(arr)):
                        fig, ax = plt.subplots()
                        ax.set_title(f'cycle vs {arr[i]}')
                        ax.set_xlabel('cycle')
                        ax.set_ylabel(f'{arr[i]}')
                        ax.scatter(x[1:], y[1:,i])
                        plt.savefig(os.path.join(folder, subdir, f'{arr[i]}.jpg'), format='jpg')
                        plt.close(fig)
                    
                    fig, ax = plt.subplots()
                    ax.set_title(f'cycle vs {arr[i]}')
                    ax.set_xlabel('cycle')
                    ax.set_ylabel(f'{arr[i]}')
                    for i in range(len(arr)):
                        ax.scatter(x[1:], y[1:, i], label=f'{arr[i]}')
                    
                    ax.legend(loc='upper right', shadow=True, fontsize='large')
                    plt.savefig(os.path.join(folder, subdir, 'combined.jpg'), format='jpg')  
                    plt.close(fig)     
                
                for file in os.listdir(os.path.join(folder, subdir)):
                    if "result" in file or "dump" in file or ".jpg" in file: 
                        file_path = os.path.join(folder, subdir, file)
                        arcname = os.path.relpath(file_path, folder)
                        zip_ref.write(file_path, arcname)

    try:
        return send_file(result_zip, as_attachment=True), 200
    except Exception as e:
        return str(e), 500

@app.route('/getjob/<uid>/', methods=['GET'])
def get_job(uid):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], f'{uid}.zip'), as_attachment=True), 200

@app.route('/deletejob/<uid>/', methods=['POST'])
def delete_job(uid):
    with sqlite3.connect('database.db') as con:
        cursor = con.cursor()
        res = cursor.execute("SELECT pid, status FROM jobs WHERE uid = ?", (uid,)).fetchone()
        result = subprocess.run(['qstat', res[0]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode('utf-8')
        stderr = result.stderr.decode('utf-8')
        
        if(result.returncode != 0):
            return stderr, 500
        
        if ' R ' in stdout or ' Q ' in stdout:
            result = subprocess.run(['qdel', res[0]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout = result.stdout.decode('utf-8')
            stderr = result.stderr.decode('utf-8')
            
            if(result.returncode != 0):
                return stderr, 500
                
        cursor.execute("DELETE FROM jobs WHERE uid = ?", (uid,))
        cursor.execute("DELETE FROM processes WHERE uid = ?", (uid,))
    
    shutil.rmtree(os.path.join(app.config['UPLOAD_FOLDER'], uid))
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f"{uid}.zip"))
                
    return get_jobs()


if __name__ == "__main__":
    app.run(ssl_context=('fullchain.pem', 'privkey.pem'), host='0.0.0.0', port=5001)

