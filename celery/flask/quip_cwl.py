import json
import yaml
import os
import sys
import subprocess  
import shutil
from uuid   import uuid4
from gevent import monkey; monkey.patch_all()
from gevent import wsgi
from flask  import Flask, request, jsonify, send_file
from celery import Celery

# read in the configuration file 
config_file = file("./config/config.json","r")
config_data = json.load(config_file)

if os.environ.get("CWL_BROKER_URL"):
   config_data["broker"] = os.environ.get("CWL_BROKER_URL")
if os.environ.get("CWL_BACKEND_URL"):
   config_data["backend"] = os.environ.get("CWL_BACKEND_URL")
if os.environ.get("MASTER_PORT"):
   config_data["server_port"] = int(os.environ.get("MASTER_PORT"))

# workflow data
cwl_file   = file("./config/cwl_workflows.json","r")
cwl_config = json.load(cwl_file)

# set up the application
app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = config_data["broker"]
app.config['CELERY_RESULT_BACKEND'] = config_data["backend"]
app.config['CELERY_TRACK_STARTED'] = True
# app.config['CELERY_ACKS_LATE'] = True
# app.config['BROKER_HEARTBEAT'] = 20.0
# app.config['CELERY_IGNORE_RESULT'] = True

cwl_worker = Celery(app.name, backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'])
cwl_worker.conf.update(app.config)

@cwl_worker.task (bind=True)
def cwl_task(self,workflow,work_dir,remove_tmp):
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

    # check if local dir was set
    outdir  = ""
    jobfile = "" 
    tmpdir  = ""
    if work_dir != "":
       if (not os.path.isdir(work_dir)):
          raise KeyError("Local dir does not exist on this machine.")
          return "Error"
    else:
       work_dir  = "tmp_"+str(uuid4())
       os.mkdir(work_dir)

    # create output folder in work_dir
    randval = uuid4() 
    outdir  = work_dir+"/out_"+str(randval)
    os.mkdir(outdir)

    # create temp folder for cwltool
    randval = uuid4() 
    tmpdir  = work_dir+"/tmp_"+str(randval)
    os.mkdir(tmpdir)

    # write the workflow job in work_dir
    jobfile = work_dir + '/workflow-job.json'
    f = open(jobfile,"w")
    f.write(json.dumps(w["workflow"]))
    f.close()
 
    cmd = []
    cmd.append("cwltool")
    cmd.append("--basedir")
    cmd.append(wkf_info["path"])
    cmd.append("--tmpdir-prefix")
    cmd.append(tmpdir)
    cmd.append("--outdir")
    cmd.append(outdir)
    cmd.append(wkf_info["path"] + "/" + wkf_info["file"]);
    cmd.append(jobfile);

    print cmd
    cwl_output = ""
    try:
       cwl_output = subprocess.check_output(cmd)
    except Exception:
       raise Exception("Command failed")
       return "Error"
    jout = json.loads(cwl_output)

    if remove_tmp == True:
       shutil.rmtree(work_dir)

    return jout 

@cwl_worker.task 
def cwl_list():
    return cwl_config

@cwl_worker.task
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

def cwl_check_request(request):
    assert request.method == 'POST'
    assert request.form['workflow']

def cwl_check_status(task):
    if task.state == "PENDING":
        response = {
            'state': task.state,
            'status': str(task.info)
        }
    elif task.state != "FAILURE":
        response = {
            'state': task.state,
            'status': task.info 
        }
    else:
        response = {
            'state': task.state,
            'error': str(task.info)  # this is the exception raised
        }
    return response 

def cwl_check_queue(queue_name):
    # There is an issue with control.inspect().active_queues()
    # it returns empty list or None if the system is busy with 
    # jobs. For now disable check_queue and return True
    return True   

    queue_list = cwl_worker.control.inspect().active_queues()
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
    if not cwl_check_queue(queue_name):
       result["status"]    = "error"
       result["queue"]     = str(queue_name)
       result["message"]   = "Queue does not exist"
       result["workflows"] = []
       return jsonify(result)
    task = cwl_list.apply_async((),queue=queue_name)
    task_result = "" 
    try:
       task_result = task.get()
       response = cwl_check_status(task)
       result["status"]    = "success"
       result["queue"]     = str(queue_name)
       result["message"]   = "Got results" 
       result["workflows"] = task_result 
    except Exception as ex:
       response = cwl_check_status(task)
       result["status"]    = "error"
       result["queue"]     = str(queue_name)
       result["message"]   = str(ex) 
       result["workflows"] = [] 

    return jsonify(result)

@app.route('/workflow/info/<queue_name>/<wkf_name>',methods=['GET'])
def get_info(queue_name,wkf_name):
    result = {}
    if not cwl_check_queue(queue_name):
       result["status"]    = "error"
       result["queue"]     = str(queue_name)
       result["message"]   = "Queue does not exist"
       result["workflows"] = []
       return jsonify(result)
    task = cwl_info.apply_async(([wkf_name]),queue=queue_name)
    task_result = "" 
    try:
       task_result = task.get()
       response = cwl_check_status(task)
       result["status"]    = "success"
       result["queue"]     = str(queue_name)
       result["message"]   = "Got results" 
       result["workflow"] = task_result 
    except Exception as ex:
       response = cwl_check_status(task)
       result["status"]    = "error"
       result["queue"]     = str(queue_name)
       result["message"]   = str(ex) 
       result["workflow"] = "" 

    return jsonify(result)

@app.route('/work/background/<queue_name>', methods=['POST'])
def async_cwl(queue_name):
    cwl_check_request(request)

    workflow = request.form['workflow']
    task = cwl_task.apply_async(([workflow,"",False]),queue=queue_name)

    return jsonify({'task_id' : task.id})

@app.route('/work/foreground/<queue_name>', methods=['POST'])
def exec_cwl(queue_name):
    if not cwl_check_queue(queue_name):
       return jsonify("Queue doesn't exist!")

    cwl_check_request(request)

    workflow = request.form['workflow']
    local_dir  = ""
    remove_tmp = True
    task = cwl_task.apply_async(([workflow,local_dir,False]),queue=queue_name)
    try:
       task.get()
       response = cwl_check_status(task)
    except Exception:
       response = cwl_check_status(task)

    return jsonify(response)

@app.route('/work/processfile/<queue_name>', methods=['POST'])
def upload_file(queue_name):
    cwl_check_request(request)

    if 'file' not in request.files:
       return jsonify({'error' : 'No file in the request.'}) 
    
    file = request.files['file']
    if file.filename == '':
       return jsonify({'error' : 'No file was selected.'}) 
    
    tmpdir = ""
    if file:
       filename = file.filename
       randval = uuid4() 
       tmpdir  = "./tmp_"+str(randval)
       os.mkdir(tmpdir)
       file.save(os.path.join(tmpdir, filename))
 
    workflow = request.form['workflow']
    task     = cwl_task.apply_async([workflow,tmpdir,False],queue=queue_name)

    return jsonify({'task_id' : task.id})

@app.route('/work/download/<task_id>', methods=['GET'])
def download_result(task_id):
    task     = cwl_task.AsyncResult(task_id)
    response = cwl_check_status(task)

    if response["state"] == "SUCCESS":
       return send_file(response["status"]["output_file"]["path"])
    else:
       return jsonify(response) 
    
@app.route('/work/status/<task_id>', methods=['GET'])
def taskstatus(task_id):
    task = cwl_task.AsyncResult(task_id)
    response = cwl_check_status(task)
    return jsonify(response)

@app.route('/job', methods=['POST'])
def async_order():
    job = request.get_json() 
    if job is None:
       raise ClientError("Content-type should be application/json", status_code=400)

    wkf_def = {}
    wkf_def["name"] = "segmentation"
    job_def = {} 
    job_def["image_wsi"] = job["data"]["order"]["image"]["case_id"]
    job_def["locx"] = int(job["data"]["order"]["roi"]["x"])
    job_def["locy"] = int(job["data"]["order"]["roi"]["y"])
    job_def["width"] = int(job["data"]["order"]["roi"]["w"])
    job_def["height"] = int(job["data"]["order"]["roi"]["h"])
    job_def["output_dir"] = "./"
    job_def["analysis_id"] = job["data"]["order"]["execution"]["execution_id"] 
    job_def["case_id"] = job["data"]["order"]["image"]["case_id"]
    job_def["subject_id"] = job["data"]["order"]["image"]["subject_id"]
    job_def["otsu_ratio"] = float(job["data"]["order"]["pr"]) 
    job_def["curv_weight"] = float(job["data"]["order"]["pw"])
    job_def["lower_size"] = float(job["data"]["order"]["pl"])
    job_def["upper_size"] = float(job["data"]["order"]["pu"])
    job_def["kernel_size"] = float(job["data"]["order"]["pk"])
    job_def["declump"] = job["data"]["order"]["pj"]
    job_def["mpp"] = float(0.25)
    job_def["upper_left_corner"] = job["data"]["order"]["roi"]["x"] + "," + job["data"]["order"]["roi"]["y"]
    job_def["tile_size"] = job["data"]["order"]["roi"]["w"] + "," + job["data"]["order"]["roi"]["h"]
    job_def["patch_size"] = job_def["tile_size"]
    job_def["zip_output"] = "output.zip"
    job_def["out_folder"] = "./temp"
    wkf_def["workflow"] = job_def
    queue_name = "cwlqueue"
    print wkf_def
    workflow = json.dumps(wkf_def)
    task = cwl_task.apply_async(([workflow,"",False]),queue=queue_name)
    return jsonify({'id' : task.id})

@app.route('/job/<task_id>', methods=['GET'])
def order_status(task_id):
    task     = cwl_task.AsyncResult(task_id)
    response = ""
    if task.state == "PENDING":
        response = {
            'state': 'pending',
            'status': str(task.info)
        }
    elif task.state == "STARTED":
        response = {
            'state': 'started',
            'status': task.info 
        }
    elif task.state == "SUCCESS":
        response = {
            'state': 'complete',
            'status': task.info 
        }
    else:
        response = {
            'state': 'failed',
            'error': str(task.info)  # this is the exception raised
        }

    return jsonify(response)

#
# return error, from flask documentation
#
class ClientError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(ClientError)
def handle_client_error(error):
    res = error.to_dict()
    res["state"] = "ERROR"
    response = jsonify(res)
    response.status_code = error.status_code
    return response

if __name__ == '__main__':
    server = wsgi.WSGIServer(('', config_data["server_port"]), app)
    server.serve_forever()

