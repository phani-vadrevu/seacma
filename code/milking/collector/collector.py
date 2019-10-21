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
import sched
import time
import requests
from datetime import datetime

from feeders import feeders
from parsers import *
import db_operations
import utils


def update_db(feeder, url, db_operator):
    db_operator.insert_url(url, feeder['Campaign'], 'feeder')


def make_request(feeder):
    headers = {
        "User-Agent": feeder["User-Agent"]
    }
    response = requests.get(
        feeder["URL"],
        headers=headers,
        allow_redirects=feeder["Allow-Redirects"])
    return response


def process_response(feeder, response, db_operator):
    url = feeder["Parser"](response)
    print "Received the following URL: ", url
    if url is not None:
        update_db(feeder, url, db_operator)


def run_event(scheduler, feeder, db_operator):
    response = make_request(feeder)
    process_response(feeder, response, db_operator)
    sleep_time = utils.get_sleep_time(feeder["Frequency"])
    time_now = datetime.now()
    print ("run_event(), time: %s, campaign:%s, sleep: %s" % (
           str(time_now), feeder["Campaign"], sleep_time))
    scheduler.enter(sleep_time, 1, run_run_event, (scheduler, feeder, db_operator))


def run_run_event(scheduler, feeder, db_operator):
    try:
        run_event(scheduler, feeder, db_operator)
    except Exception as e:
        print "Exception: ", e


def setup():
    scheduler = sched.scheduler(time.time, time.sleep)
    db_operator = db_operations.DBOperator()
    for feeder in feeders:
        print "Scheduling an event"
        print feeder
        scheduler.enter(0, 1, run_run_event, (scheduler, feeder, db_operator))
    scheduler.run()

if __name__ == "__main__":
    setup()
