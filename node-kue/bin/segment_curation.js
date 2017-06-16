// script to generate composite dataset for given user and image case_id

print("-- script to generate composite dataset for given user and image case_id -- \n");

var annotation_execution_id=user+"_composite_input";
var polygon_execution_id=user+"_composite_dataset";

db.createCollection("newcollection");
 //empty the newcollection
db.newcollection.remove({});

print("-- get segmentations within annotation ... \n");
//get segmentations within annotation 
db.objects.find({"provenance.image.case_id":case_id,                
                 "provenance.analysis.execution_id":annotation_execution_id
                  }).forEach( function(annotation)
                   {db.objects.aggregate([ { $match: {"provenance.image.case_id":case_id,                                                     
                                                      "provenance.analysis.execution_id":annotation.algorithm,                                                      
                                                       x : { '$gte':annotation.geometry.coordinates[0][0][0], '$lte':annotation.geometry.coordinates[0][2][0]},
                                                       y : { '$gte':annotation.geometry.coordinates[0][0][1], '$lte':annotation.geometry.coordinates[0][2][1]}                       
                                                      } }, { $out: "tmpCollection" } ]);  
                    db.tmpCollection.copyTo("newcollection");                                                       
                   } ); 				   
 
db.newcollection.find().count();
 
db.tmpCollection.drop();
  
print("-- update execution_id for this new collection:");   
// update execution_id for this new collection
db.newcollection.update({},
                        {$set : {"provenance.analysis.execution_id":polygon_execution_id}},
                        {upsert:false, multi:true});
                        
 
print("-- delete all old composite dataset of segmentations:");  
// delete all merged segmentations
 db.objects.remove({"provenance.image.case_id":case_id,                        
                         "provenance.analysis.execution_id":polygon_execution_id 			                                                    
                       } );

print("-- insert new dataset from newcollection as array:");  
 //insert from newcollection as array
 db.objects.insert( db.newcollection.find({ },{"_id":0}).toArray() ); 

db.newcollection.drop();

//insert new metadate document of merging dataset to the metadata collection 
var merge_execution_id_records= db.metadata.find({"image.case_id":case_id,"provenance.analysis_execution_id":polygon_execution_id}).count();
		
if(merge_execution_id_records == 0){
 print("-- insert new metadate document of merging dataset to the metadata collection:");  
   db.metadata.insert(
   { 
    "title" : polygon_execution_id, 
    "user":user,
    "provenance" : {
        "analysis_execution_id" : polygon_execution_id, 
        "type" : "human"}, 
    "image" : {
        "case_id" : case_id       
       }
  });
}	

print("-- End of Script -- \n");
