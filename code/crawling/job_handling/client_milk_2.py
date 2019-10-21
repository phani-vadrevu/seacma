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
# This is for milking part #1. 
import requests
import random
import time

# TODO: Use urllib.unquote_plus and quote_plus
#SERVER_ADDRESS = "http://lancia.cs.uga.edu:14284"
SERVER_ADDRESS = "http://ec2-34-219-9-37.us-west-2.compute.amazonaws.com:14285"
def get_job():
    job_fetch_url = SERVER_ADDRESS + '/s3hunt3r_milk_2/fetch_job'
    r = requests.get(job_fetch_url)
    job = r.text.strip()
    print "Job name from server:", job
    return job

def post_job(stats,):
    job_post_url = SERVER_ADDRESS + '/s3hunt3r_milk_2/post'
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
