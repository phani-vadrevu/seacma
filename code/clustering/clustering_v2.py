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
import time
import tldextract
import subprocess
# import ipdb

import ad_object

ADOBJECTS_PATH = "/home/phani/ad_objects"
CLUSTER_SCREENSHOTS_PATH = "/home/phani/se_hunter_results/cluster_screenshots"
ARCHIVES_DIR_PATH = "/data/se_hunter"
CLUSTERED_ADOBJECTS_PATH = "/home/phani/se_hunter_results/clustered_ad_objects.json"

MIN_CLUSTER_SIZE = 3

class ImageClusterer:
    def __init__(self,):
        self.ad_objects = []
        self.tld_extract = tldextract.TLDExtract(suffix_list_urls=None)
        # Stores the set of unique domains for each cluster
        # IMAGE_HASH --> set(Ad URL DOMAINS) 
        self.cluster_domains = {}

        # IAMGE_HASH --> [index in ad_objects] 
        self.clusters = {}
        self.fetch_data()
        self.cluster_images()

    def fetch_an_image(self, img_hash):
        ad = self.ad_objects[self.clusters[img_hash][0]]
        archive_path = os.path.join(ARCHIVES_DIR_PATH, "logs_%s.tar.gz" % (ad.log_id,))
        subprocess.call("tar -xzvf %s" % (archive_path,), shell=True)
        image_path = os.path.join(ad.log_id, "screenshots", ad.screenshot)
        target_image_path = os.path.join(CLUSTER_SCREENSHOTS_PATH, "%s.png" % (img_hash,))
        subprocess.call("cp %s %s" % (image_path, target_image_path), shell=True)
        subprocess.call("rm -rf %s" % (ad.log_id,), shell=True)
        
    # Fetch the relevant data into self.data_dict
    def fetch_data(self,):
        ad_obj_files = os.listdir(ADOBJECTS_PATH)
        for ad_obj_file in ad_obj_files:
            ad_obj_fpath = os.path.join(ADOBJECTS_PATH, ad_obj_file)
            ad_objs = ad_object.parse_ad_objects(ad_obj_fpath)
            self.ad_objects = self.ad_objects + ad_objs
        print "Done loading all ad_objects into memory; %s ads" % (len(self.ad_objects),)

    def cluster_images(self,):
        for index, ad in enumerate(self.ad_objects):
            ad_domain =  self.tld_extract(ad.ad_url).registered_domain
            if ad.screenshot_hash not in self.cluster_domains:
                self.cluster_domains[ad.screenshot_hash] = set()
                self.clusters[ad.screenshot_hash] = []
            if ad_domain in self.cluster_domains[ad.screenshot_hash]:
                continue
            self.cluster_domains[ad.screenshot_hash].add(ad_domain)
            self.clusters[ad.screenshot_hash].append(index)

        print "Done with basic clustering"

        # Prune clusters and get a representative screenshot if it doesn't exist
        for h in self.clusters.keys():
            if len(self.clusters[h]) < MIN_CLUSTER_SIZE:
                del self.clusters[h]

        print "Pruned clusters; %s final clusters" % (len(self.clusters),)
        cluster_screenshots = set([x.split('.')[0] for x in os.listdir(CLUSTER_SCREENSHOTS_PATH)])
        clustered_ad_objects = []
        for h in self.clusters.keys():
            if h not in cluster_screenshots:
                self.fetch_an_image(h)
            for index in self.clusters[h]:
                clustered_ad_objects.append(self.ad_objects[index])
        ad_object.dump_ad_objects(CLUSTERED_ADOBJECTS_PATH, clustered_ad_objects)
        print "Dumped only the clustered ad_objects; %s ads" % (len(clustered_ad_objects),)

        # import ipdb; ipdb.set_trace()


def main():
    ic = ImageClusterer()


if __name__ == "__main__":
    main()
