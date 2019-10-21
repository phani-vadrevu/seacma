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
import os 
import collections
import json

import find_matching_cluster
import ad_object

RES_ADOBJECTS_PATH = "/home/phani/ad_objects_res"
RES_CLUSTERED_ADOBJECTS_PATH = "/home/phani/se_hunter_results/res_clustered_ad_objects_v4.json"
RES_CLUSTERS_PATH = "/home/phani/se_hunter_results/res_clusters_v4.json"


def residential_clusters():
    total_ads = 0
    cao_idx = 0
    clustered_ad_objects = []
    clusters = collections.defaultdict(list)
    cm = find_matching_cluster.ClusterMatcher()
    ad_obj_files = os.listdir(RES_ADOBJECTS_PATH)
    for ad_obj_file in ad_obj_files:
        ad_obj_fpath = os.path.join(RES_ADOBJECTS_PATH, ad_obj_file)
        ad_objs = ad_object.parse_ad_objects(ad_obj_fpath)
        for ad in ad_objs:
            total_ads += 1
            mr = cm.find_matching_cluster(ad.screenshot_hash)
            if mr != -1:
                clusters[mr].append(cao_idx)
                clustered_ad_objects.append(ad)
                cao_idx += 1
    print len(clustered_ad_objects), len(clusters), total_ads
    ad_object.dump_ad_objects(RES_CLUSTERED_ADOBJECTS_PATH, clustered_ad_objects)
    with open(RES_CLUSTERS_PATH, "wb") as f:
        f.write(json.dumps(clusters))


if __name__ == "__main__":
    residential_clusters()

