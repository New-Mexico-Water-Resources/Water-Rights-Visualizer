#!/bin/bash
/etc/init.d/cron start
tail -f /tmp/cron_log.txt