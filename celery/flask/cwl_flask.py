import json
import yaml
import os
import sys
from uuid   import uuid1, uuid4
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
app.config['CELERY_TRACK_STARTED'] = True

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

@celery.task 
def cwl_list():
    return cwl_config

@celery.task
def cwl_info(wkf_name):
    wkf_info = ""
    for wkf in cwl_config:
      if wkf["name"] == wkf_name:
         wkf_info = wkf
    if wkf_info == "":
       raise KeyError("Name does not match")
       return "Error"
    
    f = file(wkf_info["path"] + "/" + wkf_info["file"],"r")
    w = yaml.load(f)
    return w

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

def check_queue(queue_name):
    queue_list = celery.control.inspect().active_queues()
    if not queue_list:
       return False;
    for worker in queue_list:
        for que in queue_list[worker]:
            if que["name"] == str(queue_name):
               return True
    return False

@app.route('/workflow/list/<queue_name>',methods=['GET'])
def get_list(queue_name):
    result = {}
    if not check_queue(queue_name):
       result["status"]    = "error"
       result["queue"]     = str(queue_name)
       result["message"]   = "Queue does not exist"
       result["workflows"] = []
       return jsonify(result)
    task = cwl_list.apply_async((),queue=queue_name)
    task_result = "" 
    try:
       task_result = task.get(timeout=10)
       response = check_status(task)
       result["status"]    = "success"
       result["queue"]     = str(queue_name)
       result["message"]   = "Got results" 
       result["workflows"] = task_result 
    except Exception as ex:
       response = check_status(task)
       result["status"]    = "error"
       result["queue"]     = str(queue_name)
       result["message"]   = str(ex) 
       result["workflows"] = [] 

    return jsonify(result)

@app.route('/workflow/info/<queue_name>/<wkf_name>',methods=['GET'])
def get_info(queue_name,wkf_name):
    result = {}
    if not check_queue(queue_name):
       result["status"]    = "error"
       result["queue"]     = str(queue_name)
       result["message"]   = "Queue does not exist"
       result["workflows"] = []
       return jsonify(result)
    task = cwl_info.apply_async(([wkf_name]),queue=queue_name)
    task_result = "" 
    try:
       task_result = task.get(timeout=10)
       response = check_status(task)
       result["status"]    = "success"
       result["queue"]     = str(queue_name)
       result["message"]   = "Got results" 
       result["workflow"] = task_result 
    except Exception as ex:
       response = check_status(task)
       result["status"]    = "error"
       result["queue"]     = str(queue_name)
       result["message"]   = str(ex) 
       result["workflow"] = "" 

    return jsonify(result)

@app.route('/job/background/<queue_name>', methods=['POST'])
def async_cwl(queue_name):
    check_request(request)

    workflow = request.form['workflow']
    task = cwl_task.apply_async(([workflow]),queue=queue_name)

    return jsonify({'task_id' : task.id})

@app.route('/job/foreground/<queue_name>', methods=['POST'])
def exec_cwl(queue_name):
    if not check_queue(queue_name):
       return jsonify("Queue doesn't exist!")

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
