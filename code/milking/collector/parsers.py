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
# Parsers should return None when there is unexpected output


def redirect(response):
    if response.status_code == 302 and 'location' in response.headers:
        return response.headers['location']
    else:
        print "Error: Unexpected response: ", response.status, response.headers
        return None


def meta_refresh(response):
    if response.status_code == 200:
        r = response.text
        if "url=" in r and '"</html>' in r:
            url = r[r.find('url=') + 4: r.find('"</html>')]
            return url
    print "Error: Unexpected response: ", response.status, response.headers, response.text
    return None


def multiple_nojs_redirects(response):
    if response.status_code == 200:
        return response.url
    print "Error: Unexpected response: ", response.status, response.headers, response.text
    return None
