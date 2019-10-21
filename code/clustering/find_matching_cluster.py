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
import random
import json

import ad_object
import image_hash_utils
IMAGE_HASH_SIMILARIY_THRESHOLD = 13

# code to match a given image hash to a cluster ID (works by first finding the closest cluster
# and then checking for all the hashes in that cluster)
CLUSTERED_ADOBJECTS_PATH = "/home/phani/se_hunter_results/clustered_ad_objects_v4.json"
CLUSTERS_PATH = "/home/phani/se_hunter_results/filtered_clusters_v4.json"

class ClusterMatcher(object):
    def __init__(self,):
        clustered_ad_objects = ad_object.parse_ad_objects(CLUSTERED_ADOBJECTS_PATH)
        with open(CLUSTERS_PATH) as f:
            clusters = json.loads(f.readline())

        # print len(clusters)
        # print sorted([int(x) for x in clusters.keys()])
        # hash_sample_member --> (label, all_hashes_list) for a cluster
        self.sample_hashes_dict = {}

        # Matches hash to cluster
        self.hash_cluster_dict = {}
        for label, ad_idx_list in clusters.iteritems():
            img_hash_set = set()
            for ad_idx in ad_idx_list:
                img_hash =  clustered_ad_objects[ad_idx].screenshot_hash
                self.hash_cluster_dict[img_hash] = label
                img_hash_set.add(img_hash)
            self.sample_hashes_dict[list(img_hash_set)[0]] = (label, list(img_hash_set))

    # Check hashes quickly
    def find_quick_matching_cluster(self, image_hash):
        if image_hash not in self.hash_cluster_dict:
            return -1
        return self.hash_cluster_dict[image_hash]

    # Returns cluster ID
    def find_matching_cluster(self, image_hash):
        quick_match = self.find_quick_matching_cluster(image_hash)
        if quick_match != -1:
            return quick_match
        # return -1
        for cluster_hash in self.sample_hashes_dict:
            if image_hash_utils.find_different_bits(image_hash, cluster_hash) < IMAGE_HASH_SIMILARIY_THRESHOLD:
                return self.sample_hashes_dict[cluster_hash][0]
        return -1


if __name__ == "__main__":
    cm = ClusterMatcher()
    img = "2dc48e822b23b62b7fff00ffff7f3400"
    print cm.find_matching_cluster(img)
