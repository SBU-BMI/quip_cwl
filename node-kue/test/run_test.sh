#!/usr/bin/env bash
curl -H "Content-Type: application/json" -X POST -d '{"type" : "quip_composite_cwl", "data" : { "name" : "segment_curation", "workflow" : {"user" : "tigerfan7495", "case_id" : "Alpha123"}}}'  http://quip-jobs:3000/job
