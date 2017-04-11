

var config = {
    "orders":
    {
        "redis":
        {
            "host": "quip-jobs",
            "port": "6379",
            "channel": "q:events"
        },
        "kue":
        {
            "host": "quip-jobs",
            "port": "3000",
            "path": "/job/"
        }
    }  
};

var exec = require("child_process").exec;
var async = require("async");

var kue = require('kue'),
    queue = kue.createQueue({
		redis: {
			host: config.orders.redis.host
		}
	});
	
var http = require('http');

var superagent = require('superagent');

var fs = require("fs");

var server = http.createServer(function(request, response){
    response.end("Hello");
});


queue.process("composite_order", function(job, done){
    console.log(job.id);
	
    var composite_order = job.data.composite_order;
	 console.log(composite_order);
	 
	var user = composite_order.user;
	var case_id = composite_order.case_id;	
    
    var executive_file = "/tmp/segment_curation.sh";

	var command = "mongo < " + executive_file + ' '+ user + ' '+  case_id					

	try{	
		console.log("Executing: ");
		console.log(command);

		exec(command, function(err, stdout, stderr){
			if(err){
				console.log("Error: "+err);
				done(err);
			}
			if(stderr){
				console.log("Error: "+err);
				done(err);
			}
			console.log(stdout);	    
		});	
	} catch(e) {
		console.log("Error! "+e);
		done(e);			
	}


});

server.listen(3030);
console.log("Daemon running!");
