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
import sys

from config import *

# Connect to database
try:
    conn = psycopg2.connect("dbname=%s host=%s user=%s password=%s"
                            % (db_name, db_host, db_user, db_password))
except:
    print "Unable to connect to database: " + db_name
    sys.exit()

conn.set_session(autocommit=True)

print "Successfully connected!"
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS gsb (
        domain VARCHAR(1024) PRIMARY KEY,
        first_seen TIMESTAMP,
        first_query_time TIMESTAMP, first_flag BOOLEAN,
        first_se_flag BOOLEAN, first_result TEXT,
        last_query_time TIMESTAMP, last_flag BOOLEAN,
        last_se_flag BOOLEAN, last_result TEXT)
        """)
cursor.execute("""
    CREATE INDEX IF NOT EXISTS last_flag_idx ON gsb (last_flag) """)
cursor.execute("""
    CREATE INDEX IF NOT EXISTS first_flag_idx ON gsb (first_flag) """)

cursor.execute("""
    CREATE TABLE IF NOT EXISTS vt (
        file_hash VARCHAR(64) PRIMARY KEY,
        first_seen TIMESTAMP, query_time TIMESTAMP,
        json TEXT, positives INT, total INT) """)
cursor.execute("""
    CREATE INDEX IF NOT EXISTS pos_idx ON vt (positives) """)

cursor.execute("""
    CREATE TABLE IF NOT EXISTS vt_uploads (
        file_hash VARCHAR(64) PRIMARY KEY,
        query_time TIMESTAMP,
        json TEXT, positives INT, total INT)""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS ips (
    ip VARCHAR(20),
    domain VARCHAR(1024), first_seen TIMESTAMP)""") 
cursor.execute("""
    CREATE INDEX IF NOT EXISTS ip_idx ON ips (ip) """)
cursor.execute("""
    CREATE INDEX IF NOT EXISTS domain_idx ON ips (domain) """)

print "Created all tables and indices"
cursor.close()
conn.close()
