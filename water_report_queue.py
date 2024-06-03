import subprocess
import time
import os
import sys
import argparse
import json
import subprocess
import gzip

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

PRINT_LOG = False

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

    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)    
    res = pipe.communicate()
    
    dlog("retcode = {}".format(pipe.returncode))
#    print("res =", res)
#    print("stderr =", res[1])
    
    log_path = "{}/exec_report_log.txt".format(record['base_dir'])
    
    with open(log_path, 'w') as queue_file:
        if res:            
            dlog("writing exec output to logfile {}".format(log_path))
            queue_file.write(res[0].decode(encoding='utf-8')) #std out from script
            queue_file.write(res[1].decode(encoding='utf-8')) #std err from script
            
    #now gzip the log file so we don't take too much space?
    with open(log_path, 'rb') as orig_file:
        with gzip.open(log_path, 'wb') as zipped_file:
            zipped_file.writelines(orig_file)
        
#    for line in res[0].decode(encoding='utf-8').split('\n'):
#        print(line)

#    out, err = proc.communicate()
#
#    if err:
#        output = err.decode()
#        return output

#    return "Invoked without errors: {}".format(cmd)
    
    #todo: parse output(res[0]) and decide whether or not something blew up
    status = "Success"
    return status
    

def update_status(record, state):
    now = int(time.time())
    
    record['status'] = state
    
    if state == "In Progress":
        record['started'] = now
    elif state == "Complete":
        record['ended'] = now
    #might have to do special stuff like retry later so put in seperate elif
    elif state == "Failed":        
        record['ended'] = now

def read_queue_file(queue_file_path):
    queue_data = []
    try:        
        with open(queue_file_path, 'r') as queue_file:
            queue_data = json.load(queue_file)            
    except FileNotFoundError as e:
        dlog("Report Queue File not found: {}".format(queue_file_path))
        return None
    
    return queue_data

def update_queue_file(queue_file_path, record):
    #read the queue data in to make sure we have the latest data
    queue_data = read_queue_file(queue_file_path)
    
    #loop through the queue and find the item we need to update
    for i in range(0, len(queue_data)):
        if queue_data[i]['key'] == record['key']:
            queue_data[i] = record
            dlog("Updating record {}".format(record['key']))
            break
            
    with open(queue_file_path, 'w') as queue_file:
        queue_file.seek(0)
        queue_file.write(json.dumps(queue_data, indent=4))
        queue_file.truncate()
        
def process_report(queue_file_path, record):
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

        update_status(record, status)

        #update the queue file again with the final status
        update_queue_file(queue_file_path, record)    
    except Exception as e:
        status_msg = str(e)
        dlog("Failed to process {}\n\nCaused by: {}".format(record, status_msg))
        record['status_msg'] = status_msg
        update_status(record, "Failed")
        update_queue_file(queue_file_path, record)
             
#scan the report queue for any files that are "Pending"             
def check_report_queue(queue_file_path):    
    queue_data = read_queue_file(queue_file_path)
    if not queue_data:
        dlog("No reports to process")
        return
    
    for record in queue_data:
        if record['status'] == "Pending":
            dlog("\n>>> Found Pending item in queue_file {}".format(queue_file_path))
            #update the queue file right away so we see the "In Progress"
            update_status(record, "In Progress")            
            update_queue_file(queue_file_path, record)
            
            process_report(queue_file_path, record)
            
            # exit loop after processing one so we can make sure the queue_data gets synced
            break
    
def main():
    global DEFAULT_QUEUE
    
    parser = argparse.ArgumentParser(description='Read off the report queue and invoke water-rights-visualizer-backend')
    parser.add_argument('-q', '--queue', default=DEFAULT_QUEUE, help='path to queue location')
    
    args = parser.parse_args()
    queue = args.queue
 
    while True:
        check_report_queue(queue)
        time.sleep(60)        

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
        f.seek(0)
        f.write(pid)
        f.truncate()
    
    try:
        print("{}: Starting up water_report_queue.py".format(str(now)))
        main()
    finally:
        os.unlink(pidfile)