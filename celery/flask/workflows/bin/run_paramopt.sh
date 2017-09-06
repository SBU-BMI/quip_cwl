#!/bin/sh
export HARMONY_HOME=/home/activeharmony-4.6.0/
unzip $1
cp /home/region-templates/build/regiontemplates/examples/Tuning-Yi/rtconf.xml .
/home/region-templates/build/regiontemplates/examples/Tuning-Yi/run.sh -i ./data -f nm -d 2 -m 1 -t 0 -r 20 -x dice -u $2

