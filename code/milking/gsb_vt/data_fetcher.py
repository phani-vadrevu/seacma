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
import json
import random
import time
from subprocess import check_output
import re

import db_operations


#SERVER_ADDRESS = "http://lancia.cs.uga.edu:14283"
QUERY_FREQUENCY = 60  # seconds - Query frequency for fetching data from milking server
SERVER_ADDRESS = "http://ec2-34-219-9-37.us-west-2.compute.amazonaws.com:14285"
ip_pat = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

def get_data():
    job_fetch_url = SERVER_ADDRESS + '/s3hunt3r_milk_2/fetch_gsb_vt_data'
    r = requests.get(job_fetch_url)
    data_dict = r.text.strip()
    data_dict = json.loads(data_dict)
    return data_dict


def insert_ip_data(domain, dbo):
    dig_out = check_output(["dig", "+short", domain])
    ips = dig_out.strip().split('\n')
    for ip in ips:
        if ip_pat.match(ip):
            dbo.insert_ips(ip, domain)

def main():
    dbo = db_operations.DBOperator()
    while True:
        data_dict = get_data()
        for domain in data_dict['domains']:
            dbo.insert_domain_gsb(domain)
            insert_ip_data(domain, dbo)
        for file_hash in data_dict['file_hashes']:
            dbo.insert_file_hash_vt(file_hash)
        print "Got and inserted %s domains and %s file_hashes:" % (
                            len(data_dict['domains']), len(data_dict['file_hashes']))
        time.sleep(QUERY_FREQUENCY)


if __name__ == "__main__":
    main()
