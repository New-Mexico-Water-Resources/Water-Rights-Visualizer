import subprocess
import time
import os
import sys
import argparse
import json
import subprocess

from datetime import datetime

DEFAULT_QUEUE = "/root/data/water_rights_runs/report_queue.json"

#some things we need for cleanup...
#reset In Progress to Pending in case things get hung
#clear out "Failed" runs
#clear out json file completely
#read from an "archived_runs.json"

class WaterReportException(Exception):
    pass

def exec_report(record):                       
    cmd = record['cmd'].split(" ")
    print("invoking cmd: {}".format(cmd))

    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)    
    res = pipe.communicate()
    
    print("retcode =", pipe.returncode)
    print("res =", res)
    print("stderr =", res[1])
    
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
    now = datetime.now()
    
    record['status'] = state
    
    if state == "In Progress":
        record['started'] = str(now)    
    elif state == "Invoked without errors":
        record['ended'] = str(now)
    #might have to do special stuff like retry later so put in seperate elif
    elif state == "Failed":        
        record['ended'] = str(now)

def read_queue_file(queue_file_path):
    queue_data = []
    try:        
        with open(queue_file_path, 'r') as queue_file:
            queue_data = json.load(queue_file)            
    except FileNotFoundError as e:
        print("Report Queue File not found: {}".format(queue_file_path))
        return None
    
    return queue_data

def update_queue_file(queue_file_path, record):
    #read the queue data in to make sure we have the latest data
    queue_data = read_queue_file(queue_file_path)
    
    #loop through the queue and find the item we need to update
    for i in range(0, len(queue_data)):
        if queue_data[i]['key'] == record['key']:
            queue_data[i] = record
            print("Updating record {}".format(record['key']))
            break
            
    with open(queue_file_path, 'w') as queue_file:
        queue_file.seek(0)
        queue_file.write(json.dumps(queue_data, indent=4))
        queue_file.truncate()
        
def process_report(queue_file_path, record):
    try:
        status_msg = exec_report(record)
        print("Status of invocation: {}".format(status_msg))
        record['status_msg'] = status_msg

        status = None
        if status_msg == "success":
            status = "Complete"
        else:
            status = "Failed"

        update_status(record, status)

        #update the queue file again with the final status
        update_queue_file(queue_file_path, record)    
    except Exception as e:
        status_msg = str(e)
        print("Failed to process {}\n\nCaused by: {}".format(record, status_msg))
        record['status_msg'] = status_msg
        update_status(record, "Failed")
        update_queue_file(queue_file_path, record)
             
#scan the report queue for any files that are "Pending"             
def check_report_queue(queue_file_path):
    now = datetime.now()
    print("Reading queue_file from {} at {}".format(queue_file_path, str(now)))
    
    queue_data = read_queue_file(queue_file_path)
    if not queue_data:
        print("No reports to process")
        return
    
    for record in queue_data:
        if record['status'] == "Pending":       
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
    
if __name__ == "__main__":
    pid = str(os.getpid())
    pidfile = "/tmp/water_report_queue.pid"

    if os.path.isfile(pidfile):
        print("{} already exists, exiting".format(pidfile))
        sys.exit()
        
    with open(pidfile, 'w') as f:
        f.seek(0)
        f.write(pid)
        f.truncate()
    
    try:
        main()
    finally:
        os.unlink(pidfile)