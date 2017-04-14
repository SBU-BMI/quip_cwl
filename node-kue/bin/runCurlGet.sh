#!/bin/bash

img_loc=`curl -X GET "http://quip-data:9099/services/Camicroscope_DataLoader/DataLoader/query/getFileLocationByIID/?TCGAId=$1" | jq-linux64 -r '.[0]["file-location"]'`;

echo "IMG LOCATION: " $img_loc

curl -o image.tif -X GET "http://quip-oss:5000/$img_loc/$2,$3,$4,$5/full/0/default.tif"

# /data/images/TCGA-06-0148-01Z-00-DX1.3b19c82d-c52d-4514-8bf6-5b0f629c18de.svs/11287,13719,199,192/full/0/default.jpg
# echo "CURL" $PWD $@ 
# echo "CURL" $PWD $@ > image.jpg
