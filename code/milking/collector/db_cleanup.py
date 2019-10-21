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
from config import *

# Connect to database
try:
    conn = psycopg2.connect("dbname=%s host=%s user=%s password=%s"
                            % (db_name, db_host, db_user, db_password))
except:
    print "Unable to connect to database: " + db_name

# Use Autocommit mode for database connection
conn.set_isolation_level(0)
cursor = conn.cursor()

cursor.execute("""DROP TABLE IF EXISTS urls, slds, campaigns,
        domains_seen, gsb
        """)
print """Dropped the tables:
        urls, slds, campaigns, domains_seen, gsb
        """
cursor.execute("DROP TYPE IF EXISTS url_type")

cursor.close()
conn.close()
