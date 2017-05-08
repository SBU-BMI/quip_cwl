#!/usr/bin/env python

import requests
import json
import sys

# command line parameters
img_id      = sys.argv[1]
exe_id      = sys.argv[2]
otsu_ratio  = sys.argv[3]
curv_weight = sys.argv[4]
lower_size  = sys.argv[5]
upper_size  = sys.argv[6]
kernel_size = sys.argv[7]
declump     = sys.argv[8]
tile_size   = int(sys.argv[9])

# get the image metadata
img_url = "http://quip-data:9099/services/Camicroscope_DataLoader/DataLoader/query/getMetaDataForCaseID"
payload = { "case_id" : img_id }
try:
    r = requests.get(img_url,params=payload)
except RequestException:
    sys.exit(1)    
img_meta = r.json()

img_mpp    = img_meta[0]["mpp-x"]
img_width  = img_meta[0]["width"]
img_height = img_meta[0]["height"]
sub_id     = img_meta[0]["subject_id"]

jobs_url="http://quip-jobs:3000/work/background/cwlqueue"
for i in range(0,img_width,tile_size):
    for j in range(0,img_height,tile_size):
        wkf_def = {}
        wkf_def["name"] = "segmentation"
        job_def = {} 
        job_def["image_wsi"] = img_id
        job_def["locx"] = int(i)
        job_def["locy"] = int(j)
        job_def["width"] = int(tile_size)
        if (i+tile_size>img_width):
            job_def["width"] = int(img_width-(i+1))
        job_def["height"] = int(tile_size)
        if (j+tile_size>img_height):
            job_def["height"] = int(img_height-(j+1))
        job_def["output_dir"] = "./"
        job_def["analysis_id"] = str(exe_id)  
        job_def["case_id"] = str(img_id) 
        job_def["subject_id"] = str(sub_id) 
        job_def["otsu_ratio"] = float(otsu_ratio) 
        job_def["curv_weight"] = float(curv_weight)
        job_def["lower_size"] = float(lower_size)
        job_def["upper_size"] = float(upper_size)
        job_def["kernel_size"] = float(kernel_size)
        job_def["declump"] = str(declump)
        job_def["mpp"] = float(img_mpp)
        job_def["upper_left_corner"] = str(i)+","+str(j)
        job_def["tile_size"]  = str(job_def["width"])+","+str(job_def["height"])
        job_def["patch_size"] = job_def["tile_size"]
        job_def["zip_output"] = "output.zip"
        job_def["out_folder"] = "./temp"
        wkf_def["workflow"] = job_def

        mydata = [ ('workflow', json.dumps(wkf_def)) ]
        try:
            res = requests.post(jobs_url,data=mydata)
        except RequestException:
            sys.exit(1)
        
        if res.status_code != requests.codes.ok:
            sys.exit(1)

sys.exit(0)


