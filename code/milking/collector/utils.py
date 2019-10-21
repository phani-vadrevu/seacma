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
from urlparse import urlparse
import tldextract
import random


def split_url(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc, parsed_url.path


def get_sld(url):
    ext = tldextract.extract(url)
    return ext.registered_domain


def get_sleep_time(time):
    max_time = time * 2
    return random.randint(time, max_time)
