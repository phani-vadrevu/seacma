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
import urllib
import dhash
from PIL import Image
import json
import tldextract

import config
import ad_miner
import utils
from job_handling import client_milk_2
from log_parsing import processor as log_parser
from utils import us_timestamp_str
from ship_logs import ship_logs

MAX_WORKERS = 3 
# MAX_WORKERS = 2
SESSION_TIMEOUT = 90  # TODO
TOTAL_TIMEOUT = 300

# URL+Agent --> Log ID
log_ids = {}

# Get the SHA 256 file hashes
def get_downloaded_files_list():
    downloads_path = os.path.join(config.MAIN_LOG_PATH, config.DOWNLOADS_DIR)
    downloaded_files = [x for x in os.listdir(downloads_path) if 
                                                    (x != 'raw') and
                                                    not x.startswith('.')] 
    return_str = json.dumps(downloaded_files)
    return return_str

# Parse the se_hunter.log file and get the loaded page's image hash,
# its URL and if there were any files downloaded after interaction 
# from that file
def get_milking_return_data(log_id):
    log_path = os.path.join(config.MAIN_LOG_PATH, config.SEHUNTER_LOGS_DIR, "%s.log" % (log_id,))
    with open(log_path) as f:
        screenshot_path = None
        home_url = None
        downloaded_file = False
        for line in f:
            if "The screenshot of loaded home page" in line:
                screenshot_path = line.strip().rsplit(' ', 1)[1]
            if "Home URL: " in line:
                home_url = line.strip().rsplit(' ', 1)[1]
            if "Downloaded a file: " in line:
                downloaded_file = True
    if screenshot_path:
        image = Image.open(screenshot_path)
        row, col = dhash.dhash_row_col(image)
        screenshot_hash = dhash.format_hex(row, col)
    else:
        screenshot_hash = None
    return screenshot_hash, home_url, downloaded_file 


@timeout_decorator.timeout(SESSION_TIMEOUT)
def run_adminer(adminer):
    try:
        print "Log ID for this session:", adminer.log_id
        adminer.run(num_actions=2)
        adminer.bi.log_downloads()
        adminer.cleanup()
    except Exception as e:
        print e
        print "Exception in run_adminer. Here's the traceback:"
        traceback.print_exc()
        if adminer is not None:
            # Sometimes, the browser shuts down due to an error. But, there could be
            # downloaded files in the raw dir
            adminer.bi.log_downloads()
            adminer.bi.devtools_client.close_browser()
        raise e


def worker(url, agent, vmhost):
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
    image_hash, loaded_url, downloaded_files = get_milking_return_data(log_id)
    file_hashes = get_downloaded_files_list()
    loaded_sld = ""
    if loaded_url:
        ext = tldextract.extract(loaded_url)
        loaded_sld = '.'.join(part for part in ext if part)
    # Sending logs:
    ship_logs(log_id, milking=True)
    return {"log_id": log_id, 
            "error": error,
            "image_hash": image_hash,
            "loaded_url": loaded_url,
            "loaded_sld": loaded_sld,
            "downloaded_files": downloaded_files,
            "file_hashes": file_hashes}


# When calling without docker, you can run this directly
@timeout_decorator.timeout(TOTAL_TIMEOUT)
def main_process(vmhost=""):
    job = client_milk_2.get_job()
    if not job:
        time.sleep(60)
        return
    agent, encoded_url = job.split(':')
    url = urllib.unquote_plus(encoded_url) 
    start_time = time.time()
    stats = worker(url, agent, vmhost)
    crawl_time = time.time()
    stats['total_time'] = crawl_time - start_time
    stats['job_name'] = job
    stats['agent'] = agent
    client_milk_2.post_job(stats)
    print "Here are all the stats:", stats
            #break
    #sleep(100)

def main():
    if len(sys.argv) >=2:
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
