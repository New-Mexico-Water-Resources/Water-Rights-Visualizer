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

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if err:
        output = err.decode()
        return output

    return "Invoked without errors: {}".format(cmd)

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
        
#completely overwrite the contents of the queue_file_path with queue_data
def update_queue_file(queue_file_path, queue_data):
    with open(queue_file_path, 'w') as queue_file:
        queue_file.seek(0)
        queue_file.write(json.dumps(queue_data, indent=4))
        queue_file.truncate()
                
def check_report_queue(queue_file_path):    
    print("Reading queue_file from {}".format(queue_file_path))
    
    try:
        queue_data = []
        with open(queue_file_path, 'r') as queue_file:
            queue_data = json.load(queue_file)
        
        for record in queue_data:
            if record['status'] == "Pending":                    
                update_status(record, "In Progress")

                #update the queue file right away so we see the "In Progress"
                update_queue_file(queue_file_path, queue_data)

                status_msg = exec_report(record)
                record['status_msg'] = status_msg
                
                status = None
                if status_msg.startswith("Invoked without errors"):
                    status = "Invoked without errors"
                else:
                    status = "Failed"
                    
                update_status(record, status)
                
                #update the queue file again with the final status
                update_queue_file(queue_file_path, queue_data)    
    except FileNotFoundError as e:
        print("Report Queue File not found: {}".format(queue_file_path))
    
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