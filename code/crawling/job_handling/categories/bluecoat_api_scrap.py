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
# Adapted from: https://github.com/PoorBillionaire/sitereview
from argparse import ArgumentParser
from bs4 import BeautifulSoup
import json
import requests
import sys


class SiteReview(object):
    def __init__(self):
        self.baseurl = ""
        self.headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

    def sitereview(self, url):
        payload = {"url": url, "captcha":""}
        
        try:
            self.req = requests.post(
                self.baseurl,
                headers=self.headers,
                data=json.dumps(payload),
            )
        except requests.ConnectionError as e:
            print "conn. error", e
            sys.exit("[-] ConnectionError: " \
                     "A connection error occurred")

        # print self.req
        return json.loads(self.req.content.decode("UTF-8"))

    def check_response(self, response):
        if self.req.status_code != 200:
            return None
        else:
            self.category = response["categorization"][0]["name"]
            self.date = response["translatedRateDates"][0]["text"][0:35]
            self.url = response["url"]
            return response["categorization"]


def check_url(url):
    try:
        s = SiteReview()
        response = s.sitereview(url)
        # print response
        response = json.loads(response)
        # import ipdb; ipdb.set_trace()
        resp = s.check_response(response)
    except Exception as e:
        print "exception:", e
        return None
    return resp


def main(url):
    s = SiteReview()
    response = s.sitereview(url)
    resp = s.check_response(response)
    # print url
    # print resp



if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("url", help="Submit domain/URL to Symantec's Site Review")
    args = p.parse_args()

    main(args.url)
