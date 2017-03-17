#!/bin/bash

echo "mainSegmentFeatures -t img $@"
mainSegmentFeatures -t img $@ 

# mainSegmentFeatures -i images/1/1.JPEG -z images/1/output.zip -o images/1 -t img -c test1 -p test1 -a seg:r1:w0.8:l3:u10:k20:jN -s 11287,13719 -b 199,192 -d 199,192 -r 1 -w 0.8 -l 3 -u 10 -k 20 -m 0.25 -j N

# echo "HELLO" $PWD $@ 
# echo "HELLO" $PWD $@ > myout.txt
# zip my-output.zip myout.txt
