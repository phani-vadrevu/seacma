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
import cPickle
import os

pkl_file = 'pickles/file_url_dict.pkl'

def update(url_dict_subset):
    url_dict = get_dict()
    url_dict.update(url_dict_subset)
    set_dict(url_dict)


def set_dict(url_dict):
    with open(pkl_file, 'wb') as f:
        cPickle.dump(url_dict, f)


def get_dict():
    if not os.path.exists(pkl_file):
        set_dict({})
        return {}
    with open(pkl_file) as f:
        url_dict = cPickle.load(f)
        return url_dict

def print_results():
    url_dict = get_dict()
    items = sorted(url_dict.iteritems(), key=lambda x:x[0])
    for file_path, url in items:
        print "%s : %s" % (file_path, url)

if __name__ == "__main__":
    print_results()
