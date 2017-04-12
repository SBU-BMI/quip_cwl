#!/bin/bash

mongo < segment_curation.sh $@ > output.log

# echo "mongo < segment_curation.sh $@"

# echo "HELLO" $PWD $@ 
