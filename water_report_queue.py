###############################################################################
# This script fires off once a minute to read the report_queue.json file and
# invokes some OS calls to run the water-rights-visualizer-backend scripts
# Logs for this script are written to /tmp/wrq_log.txt via the dlog() function 
###############################################################################

import subprocess
import time
import os
import sys
import argparse
import json
import subprocess
import pymongo

from datetime import datetime

DEFAULT_QUEUE = "/root/data/water_rights_runs/report_queue.json"

#some things we need this script or some other cleanup/maintenance script to do
# -reset In Progress to Pending in case things get hung
# -clear out "Failed" runs
# -clear out json file completely
# -move successful runs into a "completed_runs.json"
# -rotate cron log in /tmp/cron_log.txt
# -write output from exec_report into a logfile?
#     -rotate contents of logfile when it gets too big
#     -maybe just do a tail -5000 on the log file after every run to keep it trimmed?
# -decide "official" status(e.g. Complete, Failed, Pending, etc) and turn those into ENUMs in the code

class WaterReportException(Exception):
    pass

PRINT_LOG = True

def build_mongo_client_and_collection():
    #todo: read from ENV vars and then use defaults if not available
    user = os.environ.get("MONGO_INITDB_ROOT_USERNAME", "admin")
    cred = os.environ.get("MONGO_INITDB_ROOT_USERNAME", "mypassword")
    host = os.environ.get("MONGO_HOST", "water-rights-visualizer-water_mongo-1")
    #host = os.environ.get("MONGO_HOST", "localhost")
    port = os.environ.get("MONGO_PORT", 27017)

    database = os.environ.get("MONGO_DATABASE", "water")
    collection = os.environ.get("MONGO_COLLECTION", "report_queue")
    
    mongo_str = 'mongodb://{}:{}@{}:{}'.format(user, cred, host, port)
    
    client = pymongo.MongoClient(
        host = host,
        username = user,
        password = cred,
        port = port        
    )
    
    db = client[database]
    collect = db[collection]
    
    return collect
        
#does a system call to tail -1000 to make sure files do not grow too large
def tail_cleanup(filepath):
    cmd = ["/usr/bin/tail", "-1000", filepath]    
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)    
    res = pipe.communicate()
    
    if res:     
        stdout = res[0].decode(encoding='utf-8')
        err = res[1].decode(encoding='utf-8')
        
        with open(filepath, 'w') as file:
            file.write(stdout)
        
def cleanup_files():
    log_files = [
        "/tmp/wrq_log.txt",
        "/tmp/cron_log.txt"
    ]
    
    for lf in log_files:
        tail_cleanup(lf)        
    
#writes to the daemon log file
#todo: check logsize and tail -1000 if it is too long
def dlog(text, new_line=True):
    global PRINT_LOG    
    log_path = "/tmp/wrq_log.txt"
    
    now = datetime.now()    
    text = str(now) + " - " + text
    
    with open(log_path, 'a+') as log_file:
        log_file.write(text)
        
        if new_line:
            log_file.write("\n")
            
    if PRINT_LOG:
        print(text)
        
def exec_report(record):                       
    cmd = record['cmd'].split(" ")
    dlog("invoking cmd: {}".format(cmd))
    
    log_path = "{}/exec_report_log.txt".format(record['base_dir'])
    dlog("writing exec output to logfile {}".format(log_path))
    with open(log_path, 'w') as log_file:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)        
        
        #update the record with the pid we just launched
        record['pid'] = process.pid
        write_record(record)
        
        #streams the output 'c' in chars and writes them one by one to logfile
        for c in iter(lambda: process.stdout.read(1), b""):
            #sys.stdout.buffer.write(c)
            log_file.buffer.write(c)
    
        res = process.communicate()
        retcode = process.returncode

        if retcode != 0:
            dlog("Found non-zero return code {} from {}".format(retcode, cmd))
            raise WaterReportException("Error: Return code from visualizer backend {}".format(retcode))
        
        #think we might be able to read stdout here isntead of opening the logfile for the output below
        #do not have time to test this right now though so leaving it alone
        #stdout = res[0].decode(encoding='utf-8')
        #stderr = res[1].decode(encoding='utf-8')    
    
    #todo: figure out how to read the log as it is streaming above
    # currenlty each 'c' in the loop is a char so it is just one letter making it
    # a bit hard to parse for error messages
    #check the output of the logfile for errors
    with open(log_path, 'r') as log_file:
        err_msg = ""
        figure_err_check = "problem producing figure for" 
        csv_err_check = "problem producing CSV for"
        log_body = log_file.read()
        
        dlog("checking log file for errors")
        if figure_err_check in log_body:
            err_msg += "Error producing figure png file.\n"   

        if csv_err_check in log_body:
            err_msg += "Error producing csv file.\n"

        if err_msg:
            raise WaterReportException("Error processing file: {}".format(err_msg))
    
    #todo: run tail_cleanup() on the log files after we have run this tool in prod for awhile
    # and we are sure the err checks above catch all the problems
    status = "Success"
    return status
    

def update_status(record, state):
    now = int(time.time() * 1000) #convert to milliseconds to match javascript epoch
    
    record['status'] = state
    
    if state == "In Progress":
        record['started'] = now
    elif state == "Complete":
        record['ended'] = now
    #might have to do special stuff like retry later so put in seperate elif
    elif state == "Failed":        
        record['ended'] = now

#finds the next Pending item in the queue to process
def find_pending_record():
    report_queue = build_mongo_client_and_collection() #should build the client each time in case it times out    
    record = report_queue.find_one({'status': 'Pending'}, sort=[('submitted', pymongo.ASCENDING)])
    
    #data['_id'] = str(data['_id']) #this will blow up json.dumps if we do not cast to string
    if record:
        del record['_id'] #this will blow up json.dumps
        #dlog("Found Pending record: {}".format(json.dumps(record, indent=4)))        
        
    return record

def write_record(record):
    key = record['key']
    dlog("Updating record: {}".format(key))
    
    db_filter = { 'key' : key }
    report_queue = build_mongo_client_and_collection()
    report_queue.replace_one(db_filter, record, upsert=True)    
        
def process_report(record):
    try:
        status_msg = exec_report(record)
        dlog("Status of invocation: {}".format(status_msg))
        record['status_msg'] = status_msg

        status = None
        
        #todo: update status based on parse status_msg
        if status_msg == "Success":
            status = "Complete"
        else:
            status = "Failed"

        #update the queue file again with the final status
        update_status(record, status)
        write_record(record)    
    except Exception as e:
        status_msg = str(e)
        dlog("Failed to process {}\n\nCaused by: {}".format(record, status_msg))
        record['status_msg'] = status_msg
        update_status(record, "Failed")
        write_record(record)
             
#scan the report queue for any files that are "Pending"             
def check_report_queue():    
    record = find_pending_record()
    if not record:
        dlog("No Pending reports to process")
        return
    
    dlog(">>> Found Pending item {}".format(record['key']))
    #update the queue file right away so we see the "In Progress"
    update_status(record, "In Progress")            
    write_record(record)

    process_report(record)
            
            

def main():
    global DEFAULT_QUEUE
    
#    parser = argparse.ArgumentParser(description='Read off the report queue and invoke water-rights-visualizer-backend')
#    parser.add_argument('-q', '--queue', default=DEFAULT_QUEUE, help='path to queue location')
#    
#    args = parser.parse_args()
#    queue = args.queue
 
    while True:        
        check_report_queue()        
        time.sleep(60)        
        cleanup_files() #put this after the sleep so you have a minute to look at things before cleanup
        
def is_running(pid):
    #only run this check if the /proc dir exists(on linux systems only)
    if os.path.isdir('/proc'):
        if os.path.isdir('/proc/{}'.format(pid)):
            return True
    
    return False

if __name__ == "__main__":
    now = datetime.now()
    
    pid = str(os.getpid())    
    pidfile = "/tmp/water_report_queue.pid"

    if os.path.isfile(pidfile):
        with open(pidfile, 'r') as pid_data:
            existing_pid = pid_data.read()           
            
            if is_running(existing_pid):
                print("{}: {} already exists, exiting".format(str(now), pidfile))
                sys.exit()
        
    with open(pidfile, 'w') as f:
        dlog("Writing pid file with value {}".format(pid))
        f.seek(0)
        f.write(pid)
        f.truncate()
    
    try:
        dlog("Starting up water_report_queue.py".format(str(now)))
        main()
    finally:
        os.unlink(pidfile)