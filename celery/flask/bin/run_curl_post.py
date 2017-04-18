#!/usr/bin/env python

import requests
import json
import sys

case_id  = sys.argv[1]
zip_file = sys.argv[2]
post_url = "http://quip-loader:3001/submitZipOrder"

files   = { 'zip' : open(zip_file,'rb') }
payload = { 'case_id' : case_id }

r = requests.post(post_url,files=files,data=payload)

f = open('output.log','w')
f.write(json.dumps(r))
f.close()

