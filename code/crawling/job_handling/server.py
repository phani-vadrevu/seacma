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
import config
HOME = os.getenv('HOME')


res_jobs = []
non_res_jobs = []
res_job_file_path = os.path.join(HOME, 'se-hunter/selenium/job_handling/', config.RES_JOBS_FILE)
non_res_job_file_path = os.path.join(HOME, 'se-hunter/selenium/job_handling/', config.NONRES_JOBS_FILE)

finished_res_jobs = set()
finished_non_res_jobs = set()
finished_res_jobs_file_path =  os.path.join(HOME, 'se-hunter/selenium/job_handling/done_res_jobs.txt')
finished_non_res_jobs_file_path = os.path.join(HOME, 'se-hunter/selenium/job_handling/done_non_res_jobs.txt')

with open(res_job_file_path) as f:
    res_jobs = [l.strip() for l in f]
with open(non_res_job_file_path) as f:
    non_res_jobs = [l.strip() for l in f]

app = Flask(__name__)

@app.route('/s3hunt3r/fetch', methods=['GET'])
def get_non_res_job():
    if len(non_res_jobs) > 0:
        # DEBUG THIS: it gives different results for docker, 3p windows are opened but closed
        # immediately!
        # return "chrome_mac:tubepork.com"
        return non_res_jobs.pop(0)
    else:
        return ""


@app.route('/s3hunt3r/fetch_residential', methods=['GET'])
def get_res_job():
    if len(res_jobs) > 0:
        # DEBUG THIS: it gives different results for docker, 3p windows are opened but closed
        # immediately!
        # return "chrome_mac:tubepork.com"
        return res_jobs.pop(0)
    else:
        return ""


@app.route('/s3hunt3r/post', methods=['POST'])
def post_finished_job():
    if "job_name" not in request.form or "ip_type" not in request.form:
        return ""
    job_name =  request.form['job_name']
    ip_type = request.form['ip_type']
    stats = request.form.to_dict()
    stats['machine_ip'] = request.remote_addr
    #print "Type of posted request:", type(request.form)
    #print stats
    if ip_type == "residential":
        finished_res_jobs.add(job_name)
        with open(finished_res_jobs_file_path, "ab") as f:
            f.write(json.dumps(stats) + "\n")
    else:
        finished_non_res_jobs.add(job_name)
        with open(finished_non_res_jobs_file_path, "ab") as f:
            f.write(json.dumps(stats) + "\n")
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=14283)
