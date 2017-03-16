#!/bin/bash

curl -X POST -F case_id=$1 -F zip=@$2 quip-loader:3001/submitZipOrder

# echo "CURL" $PWD $@ 
# echo "CURL" $PWD $@ > output.log
