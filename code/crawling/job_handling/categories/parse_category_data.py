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

CATEGORY_DATA_FILE = "category_data.json"
PARSED_CATEGORY_FILE = "category_dict.json"

category_dict = {}
with open(CATEGORY_DATA_FILE) as f:
    for line in f:
        entry = json.loads(line)
        domain = entry['domain']
        categories = [e['name'] for e in entry['category']]
        category_dict[domain] = categories

print len(category_dict)
with open(PARSED_CATEGORY_FILE, 'wb') as f:
    f.write(json.dumps(category_dict))
