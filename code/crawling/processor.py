#! /usr/bin/python
###########################################################################
# Copyright (C) 2018 Phani Vadrevu                                        #
# phani@cs.uno.edu                                                        #
#                                                                         #
# Distributed under the GNU Public License                                #
# http://www.gnu.org/licenses/gpl.txt                                     #
#                                                                         #
# This program is free software; you can redistribute it and/or modify    #
# it under the terms of the GNU General Public License as published by    #
# the Free Software Foundation; either version 2 of the License, or       #
# (at your option) any later version.                                     #
#                                                                         #
###########################################################################
# NOTE: For some reason, multiprocessing code doesn't play well at all with ipdb.
# Even if the module is just imported. So, make sure you don't use this code
# when trying to use ipdb anywhere.
import os
from time import sleep
import time
import logging
import timeout_decorator
import traceback
import sys
import socket

import config
import ad_miner
import utils
from job_handling import client
from log_parsing import processor as log_parser
from utils import us_timestamp_str
from ship_logs import ship_logs

MAX_WORKERS = 3 
# MAX_WORKERS = 2
SESSION_TIMEOUT = 90  # TODO
TOTAL_TIMEOUT = 300

# URL+Agent --> Log ID
log_ids = {}

@timeout_decorator.timeout(SESSION_TIMEOUT)
def run_adminer(adminer):
    try:
        print "Log ID for this session:", adminer.log_id
        adminer.run()
        adminer.cleanup()
    except Exception as e:
        print e
        print "Exception in run_adminer. Here's the traceback:"
        traceback.print_exc()
        if adminer is not None:
            adminer.bi.devtools_client.close_browser()
        raise e

def worker(url, agent, vmhost, residential=False):
    # Only useful when testing outside of Docker; Can be removed later
    utils.kill_old_processes('chrome', age=config.OBSOLETE_PROCESS_AGE)
    utils.delete_old_files(config.CHROME_BINARY_PATH, 'jsgraph.log', config.OBSOLETE_PROCESS_AGE)

    print "%s started. Domain: %s; Agent: %s" % (os.getpid(), url, agent)
    tabs_opened = 0 
    log_id = "_".join((vmhost, socket.gethostname(), us_timestamp_str()))
    error = False
    adminer = None
    try:
        adminer = ad_miner.AdMiner(start_url=url, log_id=log_id, agent_name=agent)
        tabs_opened = run_adminer(adminer)
    except Exception as e:
        error = True
        print "Got exception: for %s" % (os.getpid())
        print e
        #import ipdb; ipdb.set_trace()
        if adminer is not None:
            utils.kill_processes_by_cmdline('chrome', adminer.log_id)   # Kill relevant chrome and chromedriver processes
            adminer.cleanup()
        print "Killed browser for a broken session: %s" % (log_id,)
    # print "tabs opened:", tabs_opened
    ads_opened = 0
    if adminer is not None:
        tabs_opened = adminer.bi.overall_tabs_opened
        log_id = adminer.log_id
        logger = logging.getLogger(log_id)
        logger.info("END OF CRAWLER LOGS")
        ad_objects = log_parser.process_session(log_id, logger)
        if ad_objects is not None:
            ads_opened = len([x for x in ad_objects if len(x.redirections) > 0])

    # Sending logs:
    if ads_opened > 0:
        ship_logs(log_id, residential=residential)

    print "**************NUMBER OF TABS OPENED HERE: %s*************" % (tabs_opened,)
    print "**************URL: %s, AGENT: %s, Log ID: %s*************" % (url, agent, log_id)
    downloads_path = os.path.join(config.MAIN_LOG_PATH, config.DOWNLOADS_DIR)
    print "******* DOWNLOADS seen:", os.listdir(downloads_path)

    return {"log_id": log_id, 
            "tabs_opened": tabs_opened,
            "error": error,
            "ads_opened": ads_opened}

# When calling without docker, you can run this directly
@timeout_decorator.timeout(TOTAL_TIMEOUT)
def main_process(vmhost="", is_residential=""):
    job = client.get_job(is_residential)
    if not job:
        return
    agent, domain = job.split(':')
    url = "http://www." + domain
    start_time = time.time()
    stats = worker(url, agent, vmhost, residential=is_residential)
    crawl_time = time.time()
    stats['total_time'] = crawl_time - start_time
    stats['job_name'] = job
    stats['agent'] = agent
    stats['domain'] = domain
    client.post_job(stats, is_residential)
    print "Here are all the stats:", stats
            #break
    #sleep(100)

def main():
    if len(sys.argv) >= 3:
        if sys.argv[2] == "residential":
            print "****************CALLING FOR RESIDENTIAL NETWORK DOMAINS***************"
            main_process(sys.argv[1], is_residential=True)
        else:
            return
    elif len(sys.argv) >=2:
        main_process(sys.argv[1])
    else:
        main_process()
    

def test():
    # url = "http://www.putlockertv.io"
    # url = "http://www.freemovieswatchonline.com"
    # url = "http://www.myhotzpic.com"
    #url = "http://www.funmazaa.fun"
    # fuckedx.com
    # http://xxxgaysporno.com/
    url = "http://www.naughtyza.co.za"
    print "Started process; Time:", time.time()
    start = time.time()
    stats = worker(url, "chrome_mac", "debug")
    end = time.time()
    print "Finished process; Time:", time.time()
    print "Time: ", end - start
    print "Stats:", stats

if __name__ == '__main__':
    #test()
    main()
