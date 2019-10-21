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
#!/usr/bin/env python

"""Keeps local Google Safe Browsing cache in sync.

Accessing Google Safe Browsing API requires API key, you can find
more info on getting it here:
https://developers.google.com/safe-browsing/lookup_guide#GettingStarted

"""

import sys
import time
from datetime import datetime

from gglsbl import SafeBrowsingList
import config
import db_operations


def run_sync(sbl):
    try:
        sbl.update_hash_prefix_cache()
    except (KeyboardInterrupt, SystemExit):
        print "Exiting"
        sys.exit(0)
    except:
        print "Error in syncing"
        time.sleep(3)


def main():
    sbl = SafeBrowsingList(config.gsb_key, db_path=config.gsb_db_path)
    dbo = db_operations.DBOperator()
    while True:
        slds = dbo.get_gsb_queryable_slds()
        query_time = datetime.now()
        print "GSB Update time:", str(query_time)
        run_sync(sbl)
        print "Got updated GSB list. Now looking up %s domains: %s" % (
                    len(slds), str(datetime.now()))
        for d in slds:
            try:
                result = sbl.lookup_url(d)
                result = "%s" % (result,)
                dbo.update_gsb_table(d, result, query_time)
            except Exception as e:
                print "Exception. Skipping this domain: ", d, e
            #print result
        print "Done inserting into DB. Will update GSB list again", str(datetime.now())

if __name__ == '__main__':
    main()
