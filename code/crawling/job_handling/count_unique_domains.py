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
# TODO: If jobs is empty, make sure finished jobs equals jobs count; if not, refill jobs list
# and serve to the client who requests it
import json
import os
import collections
HOME = os.getenv('HOME')


finished_res_jobs_file_path =  os.path.join(HOME, 'se-hunter/selenium/job_handling/done_res_jobs.txt')
finished_non_res_jobs_file_path = os.path.join(HOME, 'se-hunter/selenium/job_handling/non_residential_list.txt')
finished_job_domains = os.path.join(HOME, 'se-hunter/selenium/job_handling/done_jobs_domains.txt')

res_domains = set() 
non_res_domains = set() 
time = 0
sessions = 0
with open(finished_res_jobs_file_path) as f:
    for line in f:
        entry = json.loads(line)
        res_domains.add(entry['domain'])
        time += float(entry['total_time'])
        sessions += 1
print len(res_domains), time/sessions

with open(finished_non_res_jobs_file_path) as f:
    for line in f:
        non_res_domains.add(line.strip().split(':')[1])
        time += float(entry['total_time'])
        sessions += 1
print len(non_res_domains), time/sessions

domains = res_domains.union(non_res_domains)
print "Total number of domains:", len(res_domains.union(non_res_domains))
with open(finished_job_domains, 'wb') as f:
    f.write(json.dumps(list(domains)))


import ipdb; ipdb.set_trace()
