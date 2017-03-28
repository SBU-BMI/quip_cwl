var kue       = require('kue');
var express   = require('express');
var sleep     = require('sleep');
var fs        = require('fs');
var cluster   = require('cluster');
const exec    = require('child_process').exec; 
var request   = require('superagent');
const redis   = require('redis');
var workflows = require('./config/cwl_workflows.json');
var config    = require('./config/config.json');

var redis_host = process.env.REDIS_HOST || config.redis.host;
var redis_port = process.env.REDIS_PORT || config.redis.port;
var numCores   = 8 || process.env.NUM_CORES || require('os').cpus().length;

kue.redis.createClient = function() {
    var client = redis.createClient(redis_port, redis_host);
    return client;
}
var jobs = kue.createQueue(); 

/* var jobs = kue.createQueue({
	prefix: 'q',
	redis: {
		port: redis_port,
		host: redis_host
	}
}); */

if (cluster.isMaster) {
	for (var i = 0; i < numCores; i++) 
		cluster.fork();
	cluster.on('exit', function(worker, code, signal) {
		console.log('worker ',worker.process.pid,' died');
	});
} else {
	console.log('Worker ',process.pid,' started');

	// service may lose connection to redis sub/pub in docker swarm
	// ping redis at intervals to keep connection open
	var redisURL   = "redis://"+redis_host+":"+redis_port;
	var redisCache = redis.createClient(redisURL);
	var timeDelay  = 10*1000;
	setInterval(function() {  
		console.log('Pinging Redis.');
		redisCache.set('ping', 'pong');
	}, timeDelay);

	jobs.on('error', function( err ) {
  		console.log( 'ERROR: ', err );
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

	jobs.process('wsi_segment', function(job,done) {
		console.log(job.data);
		var wsi = job.data.wsi;

		// get metadata about image
		request.get('http://quip-data:9099/services/Camicroscope_DataLoader/DataLoader/query/getMetaDataForCaseID')
		.query('case_id='+wsi.case_id)
		.end(function(err,res) {
			console.log('RESULT: ' + JSON.stringify(res));
			var wsi_info = JSON.parse(res.text)[0];
			console.log("Width: " + wsi_info.width);
			console.log("Height: " + wsi_info.height);
			console.log("MPP: " + wsi_info['mpp-x']);

			var tile_size = 4096;
			for (i=0;i<wsi_info.width;i+=tile_size) {
				for (j=0;j<wsi_info.height;j+=tile_size) {
					var seg_params = {};
					seg_params.locx = i;
					seg_params.locy = j;
					seg_params.width = tile_size; 
					if ((seg_params.locx+seg_params.width)>wsi_info.width) {
						seg_params.width = wsi_info.width-(seg_params.locx+1);
					}
					seg_params.height = tile_size;
					if ((seg_params.locy+seg_params.height)>wsi_info.height) {
						seg_params.height = wsi_info.height-(seg_params.locy+1);
					}
					seg_params.otsu_ratio = 1.0;
					seg_params.curv_weight = 0.8;
					seg_params.lower_size  = 3.0;
					seg_params.upper_size  = 200.0;
					seg_params.kernel_size = 10;
					seg_params.mpp = parseFloat(wsi_info['mpp-x']);
					seg_params.declump = 'N';
					seg_params.upper_left_corner = seg_params.locx + ',' + seg_params.locy;
					seg_params.tile_size = seg_params.width + ',' + seg_params.height;
					seg_params.patch_size = seg_params.width + ',' + seg_params.height;
					seg_params.zip_output = "output.zip";
					seg_params.out_folder = "./temp";
					seg_params.output_dir = "./";
					seg_params.analysis_id = "test:111";
					seg_params.case_id = wsi.case_id;
					seg_params.image_wsi = wsi.case_id;
					seg_params.subject_id = wsi.case_id;

					console.log("SEG PARAMS: " + JSON.stringify(seg_params));


					var segment_job = {};
					segment_job.type = "quip_cwl";
					segment_job.data = {};
					segment_job.data.name = "segmentation";
					segment_job.data.workflow = seg_params;

					request.post('http://quip-jobs:3000/job')
					.send(segment_job)
					.set("Content-Type","application/json")
					.end(function(err,res) {
						console.log("RESULT: " + JSON.stringify(res));
					});

				}
			}

		});
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
}

