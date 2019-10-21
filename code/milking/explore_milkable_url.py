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
import sys
import ad_object


def explore(fpath):
    ad_objects = ad_object.parse_ad_objects(fpath)
    for ad in ad_objects:
        print ad
        print "*" * 50


if __name__ == "__main__":
    fpath = sys.argv[1]
    explore(fpath)
