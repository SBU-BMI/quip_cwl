#!/bin/bash

echo  "user: " $1
echo "case_id: " $2

params="user='$1',case_id='$2'"

echo $params

mongo quip-data:27017/quip   --eval "user='$1',case_id='$2'" /root/quip_cwl/bin/segment_curation.js > output.log

