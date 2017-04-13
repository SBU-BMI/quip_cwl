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

var jobs = kue.createQueue({
	prefix: 'q',
	redis: {
		port: redis_port,
		host: redis_host
	}
});

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
		// console.log('Pinging Redis.');
		redisCache.set('ping', 'pong');
	}, timeDelay);

	jobs.on('error', function( err ) {
  		console.log( 'ERROR: ', err );
	});



	jobs.process('quip_composite_cwl', function(job,done) {
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
					console.log("ERRRORRRRR");
					console.log(error);
					done(new Error("Execution error: " + error));
				}
				console.log("SUCCESSSS");
				console.log(stdout);
				done(null,stdout);
			});
		}
	});

}

