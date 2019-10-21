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
import requests
import os

from config import vt_keys
import db_operations

SLEEP_INTERVAL = 3
TIMEOUT = 10

MILKED_FILES_PATH = "/home/phani/se_hunter_results/milked_files"

def send_file_to_vt(file_hash):
    file_path = os.path.join(MILKED_FILES_PATH, file_hash)
    params = {'apikey': get_vt_key()}
    files = {'file': ('myfile.exe', open(file_path, 'rb'))}
    response = requests.post('https://www.virustotal.com/vtapi/v2/file/scan', files=files,
            params=params)
    json_response = response.json()
    # import ipdb; ipdb.set_trace()
    return json_response

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
        print response
    except Exception as e:
        print "get_vt_report: Exception occured", e
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
    file_hashes = set(os.listdir(MILKED_FILES_PATH))
    file_hashes_with_report = dbo.get_vt_file_hashes_with_report()
    sent_file_hashes = dbo.get_vt_uploads_file_hashes() 
    file_hashes = file_hashes.difference(sent_file_hashes)
    file_hashes = file_hashes.difference(file_hashes_with_report)
    print len(file_hashes)
    for file_hash in file_hashes:
        try:
            response = send_file_to_vt(file_hash)
            if response['response_code'] != 1:
                print response
                return
        except Exception as e:
            print "Exception", e
            continue
        # import ipdb; ipdb.set_trace()
        dbo.insert_file_hash_vt_uploads(file_hash)
        time.sleep(SLEEP_INTERVAL)
        # break
        # pass
    # while True:
        # # time.sleep(SLEEP_INTERVAL)
        # file_hashes = dbo.get_vt_file_hashes()
        # # print "# file hashes", file_hashes
        # if len(file_hashes) > 0:
            # print "Sending %s file_hashes to VT" % (len(file_hashes),)
        # for file_hash in file_hashes:
            # json_resp, pos, total = get_vt_report(file_hash)
            # dbo.update_vt_table(file_hash, json_resp, pos, total)
            # time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    main()
