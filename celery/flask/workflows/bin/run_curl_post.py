#!/usr/bin/env python

import requests
import json
import sys
import time

case_id  = sys.argv[1]
zip_file = sys.argv[2]
post_url = "http://quip-loader:3001/submitZipOrder"
chck_url = "http://quip-loader:3000/job"

files   = { 'zip' : open(zip_file,'rb') }
payload = { 'case_id' : case_id }

try:
    r = requests.post(post_url,files=files,data=payload)
except RequestException:
    sys.exit(1)

f = open('output.log','w')
if r.status_code == requests.codes.ok:
   rv = r.json()
   task_id = rv["id"]
   chk_post = False
   chk_t = ""
   while not chk_post:
      chk_v = chck_url+"/"+str(task_id)
      chk_r = requests.get(chk_v)
      chk_t = chk_r.json()
      if "comp" in chk_t["state"]:
         chk_post = True;
      elif "fail" in chk_t["state"]:
         chk_post = True;
      else:
        time.sleep(1)
   f.write(json.dumps(chk_t))
   if "fail" in chk_t["state"]:
      sys.exit(1)
   else:
      sys.exit(0)
else:
   f.write("ERROR")
   rv = r.json()
   f.write(json.dumps(rv))
   sys.exit(1)
f.close()

sys.exit(0)

