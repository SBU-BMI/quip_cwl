#!/bin/bash

curl -o image.jpg -X GET http://quip-oss:5000/data/images/$1/$2,$3,$4,$5/full/0/default.jpg 

# /data/images/TCGA-06-0148-01Z-00-DX1.3b19c82d-c52d-4514-8bf6-5b0f629c18de.svs/11287,13719,199,192/full/0/default.jpg
# echo "CURL" $PWD $@ 
# echo "CURL" $PWD $@ > image.jpg
