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
import pprint

class AdObject(object):
    def __init__(self, log_id=None, screenshot=None, screenshot_hash=None,
                jsgraph_log=None, redirections=None, home_url=None,
                ad_url=None):
        self.log_id = log_id
        self.screenshot = screenshot
        self.screenshot_hash = screenshot_hash
        self.jsgraph_log = jsgraph_log
        if redirections is None:
            self.redirections = []
        else:
            self.redirections = redirections
        self.home_url = home_url
        self.ad_url = ad_url

    @classmethod
    def parse_ad_object(cls, ad_obj_str):
        ad_obj_dict = json.loads(ad_obj_str)
        ad_obj = cls(**ad_obj_dict)
        return ad_obj

    def dump_ad_object(self):
        ad_obj_dict = vars(self)
        line = json.dumps(ad_obj_dict)
        return line

    def __repr__(self,):
        return self.__str__()

    def __str__(self):
        return pprint.pformat(self.redirections)


def dump_ad_objects(log_path, ad_objs):
    with open(log_path, 'wb') as f:
        for ad_obj in ad_objs:
            line = ad_obj.dump_ad_object()
            f.write(line + '\n')


def parse_ad_objects(log_path):
    with open(log_path) as f:
        ad_objs = [AdObject.parse_ad_object(l.strip()) for l in f]
    return ad_objs
