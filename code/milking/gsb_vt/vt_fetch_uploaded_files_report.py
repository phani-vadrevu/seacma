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
import json
import time
import random
import urllib
import urllib2

from config import vt_keys
import db_operations

SLEEP_INTERVAL = 3
TIMEOUT = 10

def get_vt_key():
    #random.seed()
    k = random.randint(0, len(vt_keys) - 1)
    print "Using VT API key number", k
    return vt_keys[k]  # vt_keys must be a list of valid virust_total API keys

# Return json, positives, total
def get_vt_report(resource):
    url = "https://www.virustotal.com/vtapi/v2/file/report"
    parameters = {"resource": resource,
                  "apikey": get_vt_key()}
    data = urllib.urlencode(parameters)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req, timeout=TIMEOUT)
    except Exception as e:
        print "get_vt_report: Exception occured", e
        time.sleep(SLEEP_INTERVAL)
        return
    json_resp = response.read()
    if not json_resp:
	return None, None, None
    result = json.loads(json_resp)
    if result['response_code'] != 1:
        return json_resp, -1, -1
    return json_resp, result['positives'], result['total']

def main():
    dbo = db_operations.DBOperator()
    # time.sleep(SLEEP_INTERVAL)
    file_hashes = dbo.get_vt_uploads_file_hashes_2()
    print len(file_hashes)
    # print "# file hashes", file_hashes
    if len(file_hashes) > 0:
        print "Sending %s file_hashes to VT" % (len(file_hashes),)
    for file_hash in file_hashes:
        resp = get_vt_report(file_hash)
        if resp:
            json_resp, pos, total = resp
        else:
            continue
        if pos and pos != -1:
            dbo.update_vt_uploads_table(file_hash, json_resp, pos, total)
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    main()
