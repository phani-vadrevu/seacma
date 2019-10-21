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
from collections import deque
from flask import Flask, request
import json
import os
import urllib
import random
import time
from datetime import datetime

import config
import image_hash_utils

HOME = os.getenv('HOME')
FILTERED_MILKING_SOURCES = os.path.join(HOME,
                            'se-hunter/selenium/job_handling/filtered_milkingsources.json')
FINISHED_JOBS_FILE_PATH =  os.path.join(HOME, 'se-hunter/selenium/job_handling/done_milking_2_jobs.json')
MILKING_CYCLES_DATA =  os.path.join(HOME, 'se-hunter/selenium/job_handling/milking_cycles.txt')
UPSTREAM_FREQUENCY = 3600  # Frequency for milking upstream cateogry urls

milking_jobs = set()  # a permanent list of all milking job_names
upstream_jobs = set() # a permanent list of all upstream job_names
jobs_dict = {}  # maps job name to the data from filtered_milking_sources 
job_queue = deque()
finished_jobs = set()
gsb_queue = deque()  # contains slds of loaded urls
vt_queue = deque()  # contains sha256 hashes of all downloaded files
last_upstream_time = time.time()
seen_domains = set()
seen_file_hashes = set()

with open(FILTERED_MILKING_SOURCES) as f:
    for line in f:
        entry = json.loads(line)
        jobs_dict[entry['job_name']] = entry
        if entry['category'] == 'MILKING':
            milking_jobs.add(entry['job_name'])
        else:
            upstream_jobs.add(entry['job_name'])

print len(milking_jobs), len(upstream_jobs)
# import sys; sys.exit()
app = Flask(__name__)


def reload_job_queue():
    global last_upstream_time
    with open(MILKING_CYCLES_DATA, "ab") as f:
        current_time = time.time()
        if current_time - last_upstream_time > UPSTREAM_FREQUENCY:
            job_queue.extend(upstream_jobs)
            f.write("**Reloaded Upstream URLs: %s** \n" % (str(datetime.now()),))
            last_upstream_time = current_time
        job_queue.extend(milking_jobs)
        f.write("**Reloaded Milking URLs: %s** \n" % (str(datetime.now()),))

def append_gsb_vt_data(stats):
    # Commenting below to Send to gsb regardless of whether or not its a milking job
    # if stats['job_name'] not in milking_jobs:
        # return
    # if not image_hash_utils.is_known_similar_hash(
                    # stats['image_hash'], jobs_dict[stats['job_name']]['image_hashes']):
        # return
    if stats['loaded_sld'] not in seen_domains:
        seen_domains.add(stats['loaded_sld'])
        gsb_queue.append(stats['loaded_sld'])
    for file_hash in stats['file_hashes']:
        if file_hash not in seen_file_hashes:
            seen_file_hashes.add(file_hash)
            vt_queue.append(file_hash)
        

@app.route('/s3hunt3r_milk_2/fetch_gsb_vt_data', methods=['GET'])
def get_gsb_vt_data():
    return_dict = {}
    return_dict['domains'] = [gsb_queue.popleft() for _ in range(len(gsb_queue))]
    return_dict['file_hashes'] = [vt_queue.popleft() for _ in range(len(vt_queue))]
    return json.dumps(return_dict)


@app.route('/s3hunt3r_milk_2/fetch_job', methods=['GET'])
def get_job():
    if len(job_queue) == 0:
        reload_job_queue()
    return job_queue.popleft()


@app.route('/s3hunt3r_milk_2/post', methods=['POST'])
def post_finished_job():
    if not("job_name" in request.form and
            "image_hash" in request.form and
            "loaded_sld" in request.form and
            "file_hashes" in request.form):
        return ""
    job_name =  request.form['job_name']
    stats = request.form.to_dict()
    stats['machine_ip'] = request.remote_addr
    stats['timestamp'] = time.time()
    stats['file_hashes'] = json.loads(stats['file_hashes'])
    append_gsb_vt_data(stats)
    #print "Type of posted request:", type(request.form)
    #print stats
    with open(FINISHED_JOBS_FILE_PATH, "ab") as f:
        f.write(json.dumps(stats) + "\n")
    return "OK"


if __name__ == "__main__":
    # reload_job_queue()
    # print job_queue.popleft()['job_name']
    app.run(host="0.0.0.0", port=14285)
