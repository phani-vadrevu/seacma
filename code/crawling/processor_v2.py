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
import subprocess
import multiprocessing
from multiprocessing.dummy import Pool as ThreadPool
from functools import partial
import traceback
import time

from config import CHROME_BINARY_PATH
from ad_miner import AdMiner

def worker(url, agent):
    try:
        adminer = AdMiner(start_url=url, agent_name=agent)
        adminer.run()
        adminer.cleanup()
    except Exception as e:
        print "Adminer Exception!", e
        traceback.print_exc()
        # TODO: Needs to change?
        subprocess.call('rm -rf %s/*.jsgraph.log' % (CHROME_BINARY_PATH,), shell=True)

def abortable_worker(func, *args, **kwargs):
    print "there"
    timeout = kwargs.get('timeout', None)
    p = ThreadPool(1)
    res = p.apply_async(func, args=args)
    try:
        out = res.get(timeout)  # Wait timeout seconds for func to complete.
        return out
    except multiprocessing.TimeoutError:
        print("Aborting due to timeout")
        p.terminate()
        #raise

def main():
    print "# CPUs: %s" % (multiprocessing.cpu_count(),)
    pool = multiprocessing.Pool()
    file_path = "/home/phani/se-hunter/seeds/popads_1.txt"
    #agents = ['ie_win', 'edge_win', 'chrome_mac']
    agents = ['chrome_android']
    with open(file_path) as f:
        for i, line in enumerate(f):
            for agent in agents:
                domain = line.split(';')[0]
                print "Processing domain #: %s, %s" % (i + 1, domain)
                url = "http://www." + domain
                args = (url, agent)
                abortable_func = partial(abortable_worker, worker, timeout=5)
                pool.apply_async(abortable_func, args=args)
    pool.close()
    pool.join()
    time.sleep(10)
    print "done"

if __name__ == "__main__":
    main()