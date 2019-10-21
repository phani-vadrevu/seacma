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
import json
import sys
import subprocess


JOBS_DIR = "jobs"

HOME = os.environ['HOME']
res_jobs_file = "../residential_list.txt"
non_res_jobs_file = "../non_residential_list.txt"
category_data_file = "category_data.json"

def get_publisher_domains():
    publisher_domains = set()
    logged_domains = set()
    with open(res_jobs_file) as f:
        for line in f:
            publisher_domains.add(line.split(':')[1].strip())
    with open(non_res_jobs_file) as f:
        for line in f:
            publisher_domains.add(line.split(':')[1].strip())

    with open(category_data_file) as f:
        for line in f:
            entry = json.loads(line)
            if entry['category']:
                logged_domains.add(entry['domain'])
    domains = list(publisher_domains.difference(logged_domains))
    return domains
        

def main(num_jobs):
    subprocess.call('rm -rf %s/*' % (JOBS_DIR,), shell=True)
    pub_domains = get_publisher_domains()
    open_fps = []
    for i in range(num_jobs):
        fp = open(os.path.join(JOBS_DIR, 'job_%s.txt' % (i,)), 'wb') 
        open_fps.append(fp)
    i = 0
    for domain in pub_domains:
        open_fps[i].write(domain + '\n')
        i = 0 if i == (num_jobs - 1) else (i + 1)
    for i in range(num_jobs):
        open_fps[i].close()


if __name__ == "__main__":
    num_jobs = int(sys.argv[1])
    main(num_jobs)
