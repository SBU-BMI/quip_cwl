#!/bin/bash
curl -X POST -F "file=@data.zip" -F 'workflow={"name" : "paramopt", "workflow" : {"inpfile" : { "class": "File", "path": "data.zip"}, "outfile" : "blahboy"}}' http://localhost:5000/work/processfile/celery
