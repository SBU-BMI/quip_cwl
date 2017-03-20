var kue     = require('kue');
var express = require('express');
var sleep   = require('sleep');
var fs      = require('fs');
var workflows = require('./config/cwl_workflows.json');
const exec    = require('child_process').exec; 

var jobs = kue.createQueue({
	prefix: 'q',
  	redis: {
    		port: 6379,
    		host: 'quip-jobs'
	}
});

jobs.process('quip_cwl', function(job,done) {
	console.log(job.data);
	var workflow = workflows.filter(function(el) {
                console.log(el);
		return el.name === job.data.name;
	});
        console.log(workflow);
	if (workflow.length==0) {
		done(new Error("Unrecognized workflow: " + job.data.name));
	} else {
		console.log(workflow);
		var randval = Math.floor(Math.random()*100000);
		var tmpdir  = './tmpdir'+randval;
	        fs.mkdirSync(tmpdir);
		var jobfile = tmpdir + '/workflow-job.json';
		fs.writeFile(jobfile,JSON.stringify(job.data.workflow), function(err) {
			if (err) {
				console.log(err);
				done(new Error("file error: " + err));
			}
		});
		var cmd = 'cwltool --basedir ' + workflow[0].path + ' --outdir ' + tmpdir;
		cmd = cmd + ' ' + workflow[0].path + '/' + workflow[0].file;
		cmd = cmd + ' ' + jobfile;
		console.log(cmd);

		exec(cmd, function(error,stdout,stderr) {
			if (error) {
				console.error(error);
				done(new Error("Execution error: " + error));
			}
			console.log(stdout);
		        done(null,stdout);
		});
	}
});

jobs.process('order', function(job,done) {
	console.log(job.data);
	var workflow = workflows.filter(function(el) {
                console.log(el);
		return el.name === "segmentation";
	});
        console.log(workflow);
	if (workflow.length==0) {
		done(new Error("Unrecognized workflow: " + job.data.name));
	} else {
                var job_def = {}; 

                job_def.image_wsi = job.data.order.image.case_id;
                job_def.locx = parseInt(job.data.order.roi.x);
                job_def.locy = parseInt(job.data.order.roi.y);
                job_def.width = parseInt(job.data.order.roi.w);
                job_def.height = parseInt(job.data.order.roi.h);
                job_def.output_dir = "./";
                job_def.analysis_id = job.data.order.execution.execution_id;
		job_def.case_id = job.data.order.image.case_id;
		job_def.subject_id = job.data.order.image.subject_id;
                console.log("OTSU " + job.data.order.pr);
                job_def.otsu_ratio = parseFloat(job.data.order.pr);
                console.log("CURV " + job.data.order.pw);
                job_def.curv_weight = parseFloat(job.data.order.pw);
                job_def.lower_size = parseFloat(job.data.order.pl);
                job_def.upper_size = parseFloat(job.data.order.pu);
                job_def.kernel_size = parseFloat(job.data.order.pk);
                job_def.declump = job.data.order.pj;
		job_def.mpp = 0.25;
                job_def.upper_left_corner = job.data.order.roi.x + "," + job.data.order.roi.y;
                job_def.tile_size = job.data.order.roi.w + "," + job.data.order.roi.h;
                job_def.patch_size = job_def.tile_size;
		job_def.zip_output = "output.zip";
                job_def.out_folder = "./temp";

		var randval = Math.floor(Math.random()*100000);
		var tmpdir  = './tmpdir'+randval;
	        fs.mkdirSync(tmpdir);
		var jobfile = tmpdir + '/workflow-job.json';
		fs.writeFile(jobfile,JSON.stringify(job_def), function(err) {
			if (err) {
				console.log(err);
				done(new Error("file error: " + err));
			}
		});
		var cmd = 'cwltool --basedir ' + workflow[0].path + ' --outdir ' + tmpdir;
		cmd = cmd + ' ' + workflow[0].path + '/' + workflow[0].file;
		cmd = cmd + ' ' + jobfile;
		console.log(cmd);

		exec(cmd, function(error,stdout,stderr) {
			if (error) {
				console.error(error);
				done(new Error("Execution error: " + error));
			}
			console.log(stdout);
		        done(null,stdout);
		});
	}
});

