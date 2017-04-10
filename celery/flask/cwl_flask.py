import json
import yaml
import os
import sys
from random import randint
from gevent import monkey; monkey.patch_all()
from gevent import wsgi
from flask  import Flask, request, jsonify
from celery import Celery
from subprocess import call, check_call 

# read in the configuration file 
config_file = file("./config/config.json","r")
config_data = json.load(config_file)

# workflow data
cwl_file   = file("./config/cwl_workflows.json","r")
cwl_config = json.load(cwl_file)

# set up the application
app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = config_data["broker"]
app.config['CELERY_RESULT_BACKEND'] = config_data["backend"]

celery = Celery(app.name, backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task (bind=True)
def cwl_task(self,workflow):
    w = json.loads(workflow)
    if "name" not in w:
       raise KeyError('Name is not in the list')
       return "Error"
   
    wkf_info = ""; 
    for wkf in cwl_config:
       if wkf["name"] == w["name"]:
          wkf_info = wkf
    if wkf_info == "":
       raise KeyError("Name does not match")
       return "Error"

    randval = randint(1,100000)
    tmpdir  = "./tmpdir"+str(randval)
    os.mkdir(tmpdir)
    jobfile = tmpdir + '/workflow-job.json'
    f = open(jobfile,"w")
    f.write(json.dumps(w["workflow"]))
    f.close()
 
    cmd = []
    cmd.append("cwltool")
    cmd.append("--basedir")
    cmd.append(wkf_info["path"])
    cmd.append("--outdir")
    cmd.append(tmpdir)
    cmd.append(wkf_info["path"] + "/" + wkf_info["file"]);
    cmd.append(jobfile);

    print cmd
    try:
       check_call(cmd)
    except Exception:
       raise Exception("Command failed")
       return "Error"

    return w["name"] 

def check_request(request):
    assert request.method == 'POST'
    assert request.form['workflow']

def check_status(task):
    if task.state == "PENDING":
        response = {
            'state': task.state,
            'status': str(task.info)
        }
    elif task.state != "FAILURE":
        response = {
            'state': task.state,
            'status': str(task.info), 
        }
    else:
        response = {
            'state': task.state,
            'error': str(task.info)  # this is the exception raised
        }
    return jsonify(response)

@app.route('/info',methods=['GET'])
def get_info():
    return jsonify(cwl_config) 

@app.route('/background/<queue_name>', methods=['POST'])
def async_cwl(queue_name):
    check_request(request)

    workflow = request.form['workflow']
    task = cwl_task.apply_async(([workflow]),queue=queue_name)

    return jsonify({'task_id' : task.id})

@app.route('/exec/<queue_name>', methods=['POST'])
def exec_cwl(queue_name):
    check_request(request)

    workflow = request.form['workflow']
    task = cwl_task.apply_async(([workflow]),queue=queue_name)
    try:
       task.get()
       response = check_status(task)
    except Exception:
       response = check_status(task)

    return response

@app.route('/status/<task_id>', methods=['GET'])
def taskstatus(task_id):
    task = cwl_task.AsyncResult(task_id)
    response = check_status(task)
    return response

if __name__ == '__main__':
    server = wsgi.WSGIServer(('0.0.0.0', 5000), app)
    server.serve_forever()

# if __name__ == '__main__':
#     app.run(debug=True)
