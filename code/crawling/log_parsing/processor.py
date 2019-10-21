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
import os
import sys
import pprint
import time
import logging
import traceback

from ad_object import AdObject, dump_ad_objects, parse_ad_objects
import extract_chain
from config import MAIN_LOG_PATH, AD_OBJECTS_DIR, JSGRAPH_LOGS_DIR, SEHUNTER_LOGS_DIR, AD_CHAIN_PROCESS_LOG
from utils import get_old_files, get_image_hash

# Only parse log files if their last mod time is > than this
PARSING_AGE = 300
NAP_TIME = 120
LOG_NAME = 'ad_chain_process'

class Processor(object):
    def __init__(self, log_id, logger):
        self.logger = logger
        self.ad_objects = []
        jsgraph_log_file=None
        self.log_file_path = os.path.join(MAIN_LOG_PATH, SEHUNTER_LOGS_DIR, "%s.log" %(log_id,))
        self.logger.info("Starting log_parsing for log ID: %s", log_id)
        with open(self.log_file_path) as f:
            home = []
            while True:
                line = f.readline()
                if not line:
                    break
                if not home:
                    if ":Screenshot: " in line and "URL" in line:
                        home = line.strip().rsplit(' ', 1)[1]
                if "JSGraph log file: " in line:
                    jsgraph_log_file = line.strip().rsplit(' ', 1)[1]
                if ":3rd party page URL: " in line:
                    f.readline()  # This is for HTML code log line
                    next_line = f.readline()
                    if ":Screenshot: " in next_line:
                        ad_url = line.strip().rsplit(' ', 1)[1]
                        image_fpath = next_line.strip().rsplit(' ', 1)[1]
                        image_hash = get_image_hash(image_fpath)
                        image_name = os.path.basename(image_fpath)
                        self.ad_objects.append(AdObject(
                                            log_id=log_id,
                                            screenshot=image_name,
                                            screenshot_hash=image_hash,
                                            ad_url=ad_url,
                                            jsgraph_log=jsgraph_log_file,
                                            home_url=home))

    def get_redirect_chains(self,):
        jsgraph_fname = None
        for ad in self.ad_objects:
            try:
                if jsgraph_fname != ad.jsgraph_log:
                    jsgraph_fname = ad.jsgraph_log
                    jsgraph_path = os.path.join(MAIN_LOG_PATH, JSGRAPH_LOGS_DIR, ad.log_id, ad.jsgraph_log)
                    ce = extract_chain.ChainExtractor(jsgraph_path, ad.home_url)
                redirections = ce.get_redirect_chain(ad.ad_url)
                #print "Redirections:"
                #pprint.pprint(redirections)
            except Exception as e:
                self.logger.info("Exception in get_redirect_chains while parsing: %s", ad.jsgraph_log)
                print "Exception in get_redirect_chains while parsing: %s" % (ad.jsgraph_log,)
                print e, traceback.print_exc()
                self.logger.info(e)
                self.logger.info(traceback.format_exc())
            else:
                if redirections is not None:
                    ad.redirections = redirections
                else:
                    print "***Redirections is None from get_redirect_chain!!****"
        return self.ad_objects

# Process the session (i.e. parse the sehunter_log and jsgraph_logs with the given ID)
# and dumps all the ad chains found in the jsgraph logs
def process_session(log_id, logger):
    pro = Processor(log_id, logger)
    #print pro.ad_objects
    try:
        ad_objs = pro.get_redirect_chains()
        serial_path = os.path.join(MAIN_LOG_PATH, AD_OBJECTS_DIR, '%s.txt' % (log_id,))
        dump_ad_objects(serial_path, ad_objs)
    except Exception as e:
        print "Exception in parsing logs!!", e
        traceback.print_exc()
    return ad_objs

# Old code; can be used to batch process JSGraph logs to get ad chains
def session_processor_background(logger):
    se_hunter_logs_dir_path = os.path.join(MAIN_LOG_PATH, SEHUNTER_LOGS_DIR)
    while True:
        se_hunter_log_paths = get_old_files(se_hunter_logs_dir_path, PARSING_AGE)
        log_ids = [os.path.basename(x) for x in se_hunter_log_paths]
        for log_id in log_ids:
            process_session(log_id, logger)
        time.sleep(NAP_TIME)


# Old code; can be used when we need to separately get the ad chains.
def main():
    logger = logging.getLogger(LOG_NAME)
    log_path = os.path.join(MAIN_LOG_PATH, AD_CHAIN_PROCESS_LOG)
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(filename=log_path)
    logger.setLevel(logging.DEBUG)

    if len(sys.argv) == 2:
        log_id = sys.argv[1].strip()
        print process_session(log_id, logger)
    else:
        session_processor_background(logger)


if __name__ == "__main__":
    main()
