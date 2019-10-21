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
import os
import json
import random
import sys
import time

import bluecoat_api_scrap as bluecoat_api

HOME = os.environ['HOME']
res_jobs_file = "../residential_list.txt"
non_res_jobs_file = "../non_residential_list.txt"
category_data_file = "category_data.json"
JOBS_DIR = "jobs"


def main(pub_domains):
    print len(pub_domains)
    for domain in pub_domains:
        resp = bluecoat_api.check_url(domain)
        # If unresolvable, it is "Uncategorized", if 'category' is empty, that means there was
        # an error
        json_line = json.dumps({'domain': domain, 'category': resp if resp is not None else ""})
        if resp is None:
            continue
            # return
        print json_line
        with open(category_data_file, 'ab') as f:
            f.write(json_line + '\n')
        # time.sleep(random.randint(0.1, 1))
        # time.sleep(random.random())
        # time.sleep(0.2)
    

if __name__ == "__main__":
    job_num = int(sys.argv[1])
    fpath = os.path.join(JOBS_DIR, "job_%s.txt" % (job_num,))
    with open(fpath) as f:
        pub_domains = [line.strip() for line in f]
    main(pub_domains)
