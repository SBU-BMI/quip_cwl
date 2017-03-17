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

