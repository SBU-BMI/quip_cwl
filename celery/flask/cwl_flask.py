import json
import yaml
import os
import sys
from uuid import uuid1, uuid4
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

    randval = uuid4() 
    tmpdir  = "./tmp"+str(randval)
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

@app.route('/workflow/list',methods=['GET'])
def get_list():
    return jsonify(cwl_config) 

@app.route('/workflow/info/<wkf_name>',methods=['GET'])
def get_info(wkf_name):
    for wkf in cwl_config:
      if wkf["name"] == wkf_name:
         wkf_info = wkf
    if wkf_info == "":
       raise KeyError("Name does not match")
       return "Error"
    
    f = file(wkf_info["path"] + "/" + wkf_info["file"],"r")
    w = yaml.load(f)
    return jsonify(w)

@app.route('/job/background/<queue_name>', methods=['POST'])
def async_cwl(queue_name):
    check_request(request)

    workflow = request.form['workflow']
    task = cwl_task.apply_async(([workflow]),queue=queue_name)

    return jsonify({'task_id' : task.id})

@app.route('/job/foreground/<queue_name>', methods=['POST'])
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

@app.route('/job/status/<task_id>', methods=['GET'])
def taskstatus(task_id):
    task = cwl_task.AsyncResult(task_id)
    response = check_status(task)
    return response

if __name__ == '__main__':
    server = wsgi.WSGIServer(('', 5000), app)
    server.serve_forever()

# if __name__ == '__main__':
#     app.run(debug=True)
