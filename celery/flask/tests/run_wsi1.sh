curl -X POST -d 'workflow={"name" : "segment_wsi", "workflow" : {"tile_size" : 2048, "case_id" : "image3", "analysis_id" : "seg:wsi_test3", "otsu_ratio" : 1.1, "curv_weight": 0.8, "lower_size": 3, "upper_size": 100, "kernel_size": 20, "declump": "N"}}' http://localhost:5000/work/background/cwlqueue
curl -X POST -d 'workflow={"name" : "segment_wsi", "workflow" : {"tile_size" : 2048, "case_id" : "image3", "analysis_id" : "seg:wsi_test2", "otsu_ratio" : 1.1, "curv_weight": 0.8, "lower_size": 3, "upper_size": 100, "kernel_size": 20, "declump": "N"}}' http://localhost:5000/work/background/cwlqueue
