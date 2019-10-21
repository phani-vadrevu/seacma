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
from flask import Flask, request
import json
import os
import urllib
import random

import config

HOME = os.getenv('HOME')
milking_data_file = os.path.join(HOME, 'se-hunter/milking/milking_urls.json')
finished_jobs_file_path =  os.path.join(HOME, 'se-hunter/selenium/job_handling/done_milking_1_jobs.txt')
# Repeat each milking URL,AGENT combination "REPEAT" number of times
REPEAT = 5
job_queue = []
finished_jobs = set()

with open(milking_data_file) as f:
    milking_data = json.loads(f.readline())
milking_urls = milking_data['milking_urls']
# import ipdb; ipdb.set_trace()

for url in milking_urls:
    encoded_url = urllib.quote_plus(url)
    jobs = [agent + ":" + encoded_url for agent in config.USER_AGENTS.keys()] 
    job_queue = job_queue + jobs
job_queue = job_queue * REPEAT
random.shuffle(job_queue)
print "Number of milking_urls", len(milking_urls)
print "Number of jobs", len(job_queue)
# raw_input()

jobs = []
#job_file_path = os.path.join(HOME, 'se-hunter/selenium/job_handling/', config.RES_JOBS_FILE)


#with open(job_file_path) as f:
    #res_jobs = [l.strip() for l in f]

app = Flask(__name__)

@app.route('/s3hunt3r_milk_1/fetch_job', methods=['GET'])
def get_job():
    # return job_queue[0]
    if len(job_queue) > 0:
        # DEBUG THIS: it gives different results for docker, 3p windows are opened but closed
        # immediately!
        # return "chrome_mac:tubepork.com"
        return job_queue.pop(0)
    else:
        return ""


@app.route('/s3hunt3r_milk_1/post', methods=['POST'])
def post_finished_job():
    if "job_name" not in request.form:
        return ""
    job_name =  request.form['job_name']
    stats = request.form.to_dict()
    stats['machine_ip'] = request.remote_addr
    print stats
    #print "Type of posted request:", type(request.form)
    #print stats
    with open(finished_jobs_file_path, "ab") as f:
        f.write(json.dumps(stats) + "\n")
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=14284)
