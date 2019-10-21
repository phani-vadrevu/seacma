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
import psycopg2
from datetime import datetime

from config import *
import utils


class DBOperator:
    def __init__(self,):
        # Connect to database
        try:
            self.conn = psycopg2.connect("dbname=%s host=%s user=%s password=%s"
                                         % (db_name, db_host, db_user, db_password))
        except:
            print "Unable to connect to database: " + db_name
            sys.exit()
        print "Successfully connected!"
        self.cursor = self.conn.cursor()
        self.conn.set_session(autocommit=True)

    def get_gsb_queryable_slds(self,):
        self.cursor.execute("""
            SELECT distinct sld FROM slds WHERE sld NOT IN
                (SELECT domain FROM gsb WHERE last_flag IS TRUE)
            """)
        return [x[0] for x in self.cursor.fetchall()]

    def update_gsb_table(self, sld, result, query_time):
        flag = (result != "None")
        se_flag = flag and ("SOCIAL_ENGINEERING" in result)
        text = result if flag else ""
        self.cursor.execute("""
            SELECT * FROM gsb WHERE domain = %s""", (sld,))
        if self.cursor.rowcount == 0:
            self.cursor.execute(""" INSERT INTO gsb (first_query_time, first_flag,
                                first_se_flag, first_result, domain) VALUES
                                (%s, %s, %s, %s, %s)""",
                                (query_time, flag, se_flag, text, sld))
        self.cursor.execute(""" UPDATE gsb SET last_query_time = %s,
                            last_flag = %s,
                            last_se_flag = %s,
                            last_result = %s WHERE domain = %s""",
                            (query_time, flag, se_flag, text, sld))

    def bye(self,):
        self.cursor.close()
        self.conn.close()

    def update_urls_table(self, url, campaign, url_type, domain, url_path):
        self.cursor.execute("""
            SELECT count FROM urls WHERE domain = %s
            AND url_path = %s AND campaign = %s""", (domain, url_path, campaign))
        if self.cursor.rowcount == 0:
            self.cursor.execute(
                """
                INSERT INTO urls (url, domain, url_path, class,
                                  campaign, count)
                VALUES (%s, %s, %s, %s, %s, 1)""",
                (url, domain, url_path, url_type, campaign))
        else:
            self.cursor.execute("""
                UPDATE urls SET url = %s, count = count + 1
                WHERE domain = %s AND url_path = %s AND
                campaign = %s
                """, (url, domain, url_path, campaign))

    def update_domains_seen_table(self, campaign, domain, time_seen):
        self.cursor.execute("""
            SELECT * FROM domains_seen WHERE domain = %s AND
            campaign = %s
            """, (domain, campaign))
        if self.cursor.rowcount == 0:
            self.cursor.execute(
                """
                INSERT INTO domains_seen (domain, campaign,
                                  first_seen, last_seen)
                VALUES (%s, %s, %s, %s)""",
                (domain, campaign, time_seen, time_seen))
        else:
            self.cursor.execute("""
                UPDATE domains_seen SET last_seen = %s
                WHERE domain = %s AND campaign = %s
                """, (time_seen, domain, campaign))

    def update_slds_table(self, domain):
        self.cursor.execute("""
            SELECT domain FROM slds WHERE domain = %s
            """, (domain,))
        if self.cursor.rowcount == 0:
            sld = utils.get_sld(domain)
            self.cursor.execute(
                """
                INSERT INTO slds (sld, domain)
                VALUES (%s, %s)""",
                (sld, domain))

    def update_campaigns_table(self, campaign, last_seen):
        self.cursor.execute("""
            SELECT * FROM campaigns WHERE campaign = %s
            """, (campaign,))
        if self.cursor.rowcount == 0:
            self.cursor.execute(
                """
                INSERT INTO campaigns (campaign, last_seen)
                VALUES (%s, %s)""",
                (campaign, last_seen))
        else:
            self.cursor.execute(
                """
                UPDATE campaigns SET last_seen = %s
                WHERE campaign = %s
                """, (last_seen, campaign))

    # Note we only insert a new url if it has a different
    # domain or url path. If both are same, we just update
    # an old entry even if the whole URL is different from the
    # stored one.
    def insert_url(self, url, campaign, url_type):
        domain, url_path = utils.split_url(url)
        time_seen = datetime.now()
        self.update_urls_table(url, campaign, url_type, domain, url_path)
        self.update_domains_seen_table(campaign, domain, time_seen)
        self.update_slds_table(domain)
        self.update_campaigns_table(campaign, time_seen)


def test():
    dbo = DBOperator()
    print dbo.get_gsb_queryable_slds()

if __name__ == "__main__":
    test()
