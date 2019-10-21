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
# TODO: Figure out how to have logging when there are simultaneous multiple BI objects
# TODO: Add a process number here to add to the log_id
# TODO: Change subprocess.call() in cleanup code

# TODO: Setup a log line marker for all log lines?

import logging
import os
import shutil
import subprocess
import random
import traceback
import time
import glob

from browser_interactor import BrowserInteractor
from action_tree import ActionTree
import config

class AdMiner:
    # TODO: Add a process number here to add to the log_id
    def  __init__(self, start_url, log_id, agent_name="edge_win"):
        self.start_url = start_url

        self.log_id = log_id
        # TODO: Setup a log line marker for all log lines?
        self.logger = logging.getLogger(self.log_id)
        # Log id gives a unique file name to different log files / directories
        log_path = os.path.join(config.MAIN_LOG_PATH, config.SEHUNTER_LOGS_DIR, "%s.log" % (self.log_id,))

        # TODO: Figure out how to have logging when there are simultaneous multiple BI objects
        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(filename=log_path)
        # Passing this level directly to get logger
        # enables this mode for all the imported packages as well;
        # Hence, we use setLevel
        self.logger.setLevel(logging.DEBUG)

        self.logger.info("******************START******************")
        self.logger.info("log_id: %s", self.log_id)
        self.logger.info("start url: %s, agent: %s", start_url, agent_name)


        self.bi = BrowserInteractor(self.log_id, start_url=start_url, agent_name=agent_name)
        self.action_tree = ActionTree(self.log_id, self.bi)


    def run(self, num_actions=2):
        #ipdb.set_trace()
        # TODO: Rewrite to take actions until the tree is fully explored.
        print "Started Adminer run; Time:", time.time()
        for _ in range(num_actions):
            self.action_tree.take_next_action()
            print "Did one action; Time:", time.time()
        # self.action_tree.take_next_action()
        #self.action_tree.take_next_action()
        #self.action_tree.take_next_action()
        #self.action_tree.take_next_action()
        # Otherwise, the devtools client complains about unexpected log closing
        #self.bi.devtools_client.close_tab(self.bi.driver.current_window_handle)

    def cleanup(self,):
        # This is non-trivial if we are using docker; even otherwise, we can kill the browser
        # processes later on. So, we ignore this error for now
        try:
            self.bi.devtools_client.close_browser()
        except Exception as e:
            pass
        self.logger.info("Closed all tabs")

        # Create a new directory inside jsgraph_logs dir and copy all the jsgraph logs related
        # to this session here.
        target_log_dir_path = os.path.join(config.MAIN_LOG_PATH,
                                       config.JSGRAPH_LOGS_DIR,
                                       '%s' % (self.log_id,))
        print "target_log_dir_path", target_log_dir_path
        os.mkdir(target_log_dir_path)
        target_glob = os.path.join(config.CHROME_BINARY_PATH, '%s_*.jsgraph.log' % (self.log_id,))
        jsgraph_log_file_paths = glob.glob(target_glob)
        #print "jsgraph_logfiles:", jsgraph_log_files
        for jsgraph_log_path in jsgraph_log_file_paths:
            shutil.move(jsgraph_log_path, target_log_dir_path)

        # TODO: Remove JSGraph logs; comment out later.
        #shutil.rmtree(target_log_dir_path)

        # Remove chromedata dir
        chrome_data_path = os.path.join(config.MAIN_LOG_PATH,
                                        config.CHROMEDATA_DIR,
                                        "%s" % (self.log_id,))
        shutil.rmtree(chrome_data_path)
        self.logger.info("End of Adminer cleanup")



def main():
    file_path = "/home/phani/se-hunter/seeds/adcash.txt"
    #agents = ['ie_win', 'edge_win', 'chrome_mac']
    agents = ['chrome_mac']
    with open(file_path) as f:
        for agent in agents:
            for i, line in enumerate(f):
                try:
                    domain = line.split(';')[0]
                    print "Processing domain #: %s, %s" % (i+1, domain)
                    url = "http://www." + domain
                    adminer = AdMiner(start_url=url, agent_name=agent)
                    adminer.run()
                    adminer.cleanup()
                except Exception as e:
                    print "Adminer Exception!", e
                    traceback.print_exc()

                    # TODO: Needs to change?
                    subprocess.call('rm -rf %s/*.jsgraph.log' % (
                                    config.CHROME_BINARY_PATH,), shell=True)
                #break
            #break



def test():
    #test_url = "https://moviesonline.fm" # +1, with multiple next actions!
    #test_url = "http://livestream.sx" #  +1, works well
    #test_url = "https://onlinetviz.com"  # +1, mostly works, I might have gotten blocked as well after many tries!
    #test_url = "http://www.bankinfoindia.com"
    # to debug: http://www.new-mastermovie.com
    test_url = "https://themovie24k.tv/"
    #test_url = "http://www.mydevice.io"
    #test_url = "https://www.w3schools.com/Jsref/tryit.asp?filename=tryjsref_win_open"
    #test_url = "http://www.phanivadrevu.com/tests/window_open.html"
    #test_url = "http://mqtest.io"
    #test_url = "http://www.romeltea.com/"
    #test_url = "http://www.wikipedia.org"
    #adminer = AdMiner(start_url=test_url, agent_name="chrome_android")
    adminer = AdMiner(start_url=test_url, agent_name="chrome_mac")
    time.sleep(20)
    #ipdb.set_trace()
    #adminer.run()
    adminer.cleanup()

if __name__ ==  "__main__":
    main()
    #test()
