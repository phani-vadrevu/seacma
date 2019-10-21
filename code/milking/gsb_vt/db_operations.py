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

    def insert_domain_gsb(self, domain):
        self.cursor.execute("""
            SElECT * FROM gsb WHERE domain = %s""", (domain,))
        if self.cursor.rowcount > 0:
            return
        self.cursor.execute("""
            INSERT INTO gsb(domain, first_seen)
            VALUES (%s, CURRENT_TIMESTAMP)""",
            (domain,))

    def get_gsb_queryable_slds(self,):
        # Will include both NULL and FALSE values
        self.cursor.execute("""
                SELECT domain FROM gsb WHERE last_flag IS NOT TRUE
            """)
        return [x[0] for x in self.cursor.fetchall()]

    def update_gsb_table(self, sld, result, query_time):
        flag = (result != "None")
        se_flag = flag and ("SOCIAL_ENGINEERING" in result)
        text = result if flag else ""
        self.cursor.execute("""
            SELECT first_query_time FROM gsb WHERE domain = %s""", (sld,))
        if self.cursor.rowcount == 0:
            return
        result = self.cursor.fetchone()
        if not result[0]:
            self.cursor.execute("""UPDATE gsb SET first_query_time = %s,
                                first_flag = %s, first_se_flag = %s,
                                first_result = %s WHERE domain = %s""",
                                (query_time, flag, se_flag, text, sld))
        self.cursor.execute(""" UPDATE gsb SET last_query_time = %s,
                            last_flag = %s,
                            last_se_flag = %s,
                            last_result = %s WHERE domain = %s""",
                            (query_time, flag, se_flag, text, sld))

    def insert_file_hash_vt(self, file_hash):
        self.cursor.execute("""
            SElECT * FROM vt WHERE file_hash = %s""", (file_hash,))
        if self.cursor.rowcount > 0:
            return
        self.cursor.execute("""
            INSERT INTO vt(file_hash, first_seen)
            VALUES (%s, CURRENT_TIMESTAMP)""",
            (file_hash,))

    def get_vt_file_hashes(self,):
        self.cursor.execute("""
                SELECT file_hash FROM vt WHERE query_time is NULL 
            """)
        return [x[0] for x in self.cursor.fetchall()]

    def update_vt_table(self, file_hash, json_resp, pos, total):
        if not json_resp:
            self.cursor.execute("""UPDATE vt SET query_time = CURRENT_TIMESTAMP
                                   WHERE file_hash = %s""", (file_hash,))
        self.cursor.execute("""UPDATE vt SET 
                               query_time = CURRENT_TIMESTAMP,
                               json = %s, positives = %s, total = %s
                               WHERE file_hash = %s""", 
                               (json_resp, pos, total, file_hash))

    def get_vt_file_hashes_with_report(self,):
        self.cursor.execute("""
                SELECT file_hash FROM vt WHERE positives > -1 
            """)
        return [x[0] for x in self.cursor.fetchall()]

    # Used before uploading files to vt
    def get_vt_uploads_file_hashes(self,):
        self.cursor.execute("""
                SELECT file_hash FROM vt_uploads
            """)
        return [x[0] for x in self.cursor.fetchall()]

    # Used before querying file_hashes with vt 
    def get_vt_uploads_file_hashes_2(self,):
        self.cursor.execute("""
                SELECT file_hash FROM vt_uploads 
                            WHERE positives IS NULL
            """)
        return [x[0] for x in self.cursor.fetchall()]

    def update_vt_uploads_table(self, file_hash, json_resp, pos, total):
        if not json_resp:
            self.cursor.execute("""UPDATE vt_uploads SET query_time = CURRENT_TIMESTAMP
                                   WHERE file_hash = %s""", (file_hash,))
        self.cursor.execute("""UPDATE vt_uploads SET 
                               query_time = CURRENT_TIMESTAMP,
                               json = %s, positives = %s, total = %s
                               WHERE file_hash = %s""", 
                               (json_resp, pos, total, file_hash))

    def insert_file_hash_vt_uploads(self, file_hash):
        self.cursor.execute("""
            SElECT * FROM vt_uploads WHERE file_hash = %s""", (file_hash,))
        if self.cursor.rowcount > 0:
            return
        self.cursor.execute("""
            INSERT INTO vt_uploads(file_hash)
            VALUES (%s)""", (file_hash,))

    def insert_ips(self, ip, domain):
        self.cursor.execute("""
            SElECT * FROM ips WHERE domain = %s and ip = %s""", (domain, ip))
        if self.cursor.rowcount > 0:
            return
        self.cursor.execute("""
            INSERT INTO ips(ip, domain, first_seen)
            VALUES (%s, %s, CURRENT_TIMESTAMP)""",
            (ip, domain))

    def bye(self,):
        self.cursor.close()
        self.conn.close()

def test():
    dbo = DBOperator()
    # print dbo.get_gsb_queryable_slds()
    dbo.insert_domain_gsb("prettyhorseand.tk")

if __name__ == "__main__":
    test()
