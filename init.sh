#!/bin/bash
/etc/init.d/cron start
/opt/conda/bin/python /app/water_report_queue.py >> /tmp/cron_log.txt 2>&1
tail -f /tmp/cron_log.txt
