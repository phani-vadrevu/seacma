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
import requests

import random
import time

#SERVER_ADDRESS = "http://lancia.cs.uga.edu:14283"
SERVER_ADDRESS = "http://ec2-34-219-9-37.us-west-2.compute.amazonaws.com:14283"
def get_job(is_residential=False):
    if is_residential:
        job_fetch_url = SERVER_ADDRESS + '/s3hunt3r/fetch_residential'
    else:
        job_fetch_url = SERVER_ADDRESS + '/s3hunt3r/fetch'
    r = requests.get(job_fetch_url)
    job = r.text.strip()
    print "Job name from server:", job
    return job

def post_job(stats, is_residential=False):
    job_post_url = SERVER_ADDRESS + '/s3hunt3r/post'
    if is_residential:
        stats['ip_type'] = "residential"
    else:
        stats['ip_type'] = "non_residential"
    r = requests.post(job_post_url, data=stats)
    server_ack = r.text.strip()
    print "Ack from server:", server_ack

# get_job()
# Code for testing
def test():
    num_replies = 0
    while True:
        # sleep_time = random.randint(5,15)
        sleep_time = 0.1
        time.sleep(sleep_time)
        reply = get_job()
        if not reply:
            break
        num_replies = num_replies + 1
        time.sleep(sleep_time)
        post_job(reply)
    print "Number of replies:", num_replies


if __name__ == "__main__":
    test()
