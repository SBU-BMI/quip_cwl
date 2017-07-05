#!/bin/sh
unzip $1
cp /home/region-templates/build/regiontemplates/examples/Tuning-Yi/rtconf.xml .
/home/region-templates/build/regiontemplates/examples/Tuning-Yi/sh run.sh -i ./data -f nm -d 2 -m 1 -t 0 -r 20 -x dice -u $2

