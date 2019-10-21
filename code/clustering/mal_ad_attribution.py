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
import json
import numpy as np
import scipy as sp
import time
import urlparse
import collections
import multiprocessing
import logging
import pprint
import random

# mpl = multiprocessing.log_to_stderr()
# mpl.setLevel(logging.INFO)
import ad_object
import image_hash_utils
from identify_ad_network import identify_ad_network, identify_ad_network_mp
from se_categories_v4 import se_categories

ADOBJECTS_PATH = "/home/phani/ad_objects"
RES_ADOBJECTS_PATH = "/home/phani/ad_objects_res"
CLUSTER_SCREENSHOTS_PATH = "/home/phani/se_hunter_results/cluster_screenshots_v4"
ARCHIVES_DIR_PATH = "/data/se_hunter_1"
CLUSTERED_ADOBJECTS_PATH = "/home/phani/se_hunter_results/clustered_ad_objects_v4.json"
CLUSTERS_PATH = "/home/phani/se_hunter_results/clusters_v4.json"
FILTERED_CLUSTERS_PATH = "/home/phani/se_hunter_results/filtered_clusters_v4.json"
IMAGE_EXTENSIONS_FILE = "image-extensions.json"
RES_CLUSTERED_ADOBJECTS_PATH = "/home/phani/se_hunter_results/res_clustered_ad_objects_v4.json"
RES_CLUSTERS_PATH = "/home/phani/se_hunter_results/res_clusters_v4.json"
ad_obj_files = os.listdir(ADOBJECTS_PATH)
res_ad_obj_files = os.listdir(RES_ADOBJECTS_PATH)
ad_obj_paths = [os.path.join(ADOBJECTS_PATH, f) for f in ad_obj_files]
res_ad_obj_paths = [os.path.join(RES_ADOBJECTS_PATH, f) for f in res_ad_obj_files if not
                    f.startswith('.')]
print "# Ad obj paths", len(ad_obj_paths)
print "# Res ad obj paths", len(res_ad_obj_paths)
with open(RES_CLUSTERS_PATH) as f:
    res_clusters = json.loads(f.readline())

# ad_obj_paths = ad_obj_paths[:100]
# res_ad_obj_paths = res_ad_obj_paths[:100]
all_ad_obj_paths = res_ad_obj_paths + ad_obj_paths

MIN_CLUSTER_SIZE = 5 

# Results for version_3
# ERROR_CLUSTERS = [103, 173] 
# ERROR_404_CLUSTERS =  [3, 73, 84, 120, 132, 138, 141, 150, 163, 168, 203]  # Covers 404 errors or parked domains
# ADULT_AD_CLUSTERS = [7, 118, 122, 198] 
# FULL_AD_CLUSTERS = [81, 91, 106, 117] 

# Results for version_4
# 749, 
ERROR_CLUSTERS = [12, 353, 746, 749]  # 749 has too close image hashes  but dissimilar images
# 12 is not really a 404 error cluster. We get these messages due to Palo Alto network filter.
ERROR_404_CLUSTERS =  [5, 211, 259, 452, 524, 537, 558, 572, 613, 679, 1008]  # Covers 404 errors or parked domains
ADULT_AD_CLUSTERS = [17, 447, 457, 691] 
FULL_AD_CLUSTERS = [241, 362, 445, 516] 

N_JOBS = 25
# N_JOBS = 1 
# Minum size of the cluster (after removing repeating ad domain samples). If not, weed out the cluster
MIN_CLUSTER_SIZE = 5 
# Minimum number of samples that should be core in a cluster, if not weed out the cluster
MIN_CORE_FRACTION = 0.5 


class MalAdAttributer:
    def __init__(self,):
        self.ad_objects = []
        self.tld_extract = tldextract.TLDExtract(suffix_list_urls=None)
        # Stores the set of unique domain.hash  to reduce load on the clustering algo
        self.domain_hashes = set()

        # domain_ids... maps a domain to an integer ID
        self.domain_ids = {}

        # ad_objects indices of samples being considered for clustering 
        self.input_indices = []
        self.feature_matrix_hash = []
        self.feature_matrix_domain = []

        # label --> [index in ad_objects] 
        self.clusters = {}
        # self.fetch_data()
        self.fetch_clustered_data()
        print len(self.clusters)
        self.filter_clusters()
        print "Number of clusters after filtering:", len(self.clusters)
        print "# of SE clusters:",  sum([len(x) for x in se_categories.values()])
        se_clusters_1 = set([int(x) for x in self.clusters.keys()])
        se_clusters_2 = set()
        for cluster_list in se_categories.values():
            se_clusters_2 = se_clusters_2.union(set(cluster_list))
        print se_clusters_1
        print "***" * 10
        print se_clusters_2
        print "***" * 10
        print "Missing clusters:", se_clusters_1.difference(se_clusters_2)

        print "Different clusters:"
        self.fetch_mal_ad_hashes()
        self.fetch_ad_network_counts()

    def fetch_mal_ad_hashes(self,):
        self.mal_ad_hashes = set()
        self.mal_ads = 0
        for key in self.clusters:
            for ad_obj_idx in self.clusters[key]:
                mal_ad_obj = self.clustered_ad_objs[ad_obj_idx]
                self.mal_ad_hashes.add(mal_ad_obj.screenshot_hash)
                self.mal_ads = self.mal_ads + 1
            # import ipdb; ipdb.set_trace()
            if key not in self.res_clusters:
                continue
            for ad_obj_idx in self.res_clusters[key]:
                mal_ad_obj = self.res_clustered_ad_objs[ad_obj_idx]
                self.mal_ad_hashes.add(mal_ad_obj.screenshot_hash)
                self.mal_ads = self.mal_ads + 1
        print "# of mal_ad_hashes:", len(self.mal_ad_hashes)
        print "# of mal ads:", self.mal_ads 

    def fetch_ad_network_counts(self,):
        ans = ["RevenueHits" , "PopCash" , "AdCash" , "PopAds" , "PopMyAds" , "AdSterra" ,
                "HilltopAds" , "Clicksor" , "Propeller", "Clickadu", "AdMaven", "Unknown"]
        
        self.ad_counts = {}
        self.mal_ad_counts = {}
        # multiprocessing stuff
        # pm = multiprocessing.Manager()
        # self.ad_counts = pm.dict()
        # self.mal_ad_counts = pm.dict()
        for an in ans:
            self.ad_counts[an] = 0
            self.mal_ad_counts[an] = 0
        # self.mal_ad_hashes_dict = pm.dict()  # For use with mp as there are no sets in
                                            # Manager()
        # for ih in self.mal_ad_hashes:
            # self.mal_ad_hashes_dict[ih] = 1

        # pool = multiprocessing.Pool(N_JOBS)
        # results = []

        # for ad_obj_file in ad_obj_files:
            # ad_obj_fpath = os.path.join(ADOBJECTS_PATH, ad_obj_file)
            # r = pool.apply_async(identify_ad_network_mp,
                                # (ad_obj_fpath, self.ad_counts,
                                 # self.mal_ad_counts,
                                 # self.mal_ad_hashes_dict))
            # r = identify_ad_network_mp(ad_obj_fpath, self.ad_counts,
                                 # self.mal_ad_counts,
                                 # self.mal_ad_hashes_dict)
            # results.append(r)

        # ad_objs = ad_object.parse_ad_objects(ad_path)
        # for ad_obj in ad_objs:
            # ani = AdNetworkIdentifier(ad_obj)
            # an = ani.identify()
            # for r in results:
                # r.wait()
                # single processing
        ad_net_domains = collections.defaultdict(set)
        for ad_obj_fpath in all_ad_obj_paths:
            ad_objs = ad_object.parse_ad_objects(ad_obj_fpath)
            # if len(ad_objs) > 1:
                # print len(ad_objs)
            for ad in ad_objs:
                an, ad_net_domain = identify_ad_network(ad)
                if an:
                    if an != "Unknown":
                        ad_net_domains[an].add(ad_net_domain)
                    if ad.screenshot_hash in self.mal_ad_hashes:
                        self.mal_ad_counts[an] = self.mal_ad_counts[an] + 1
                    self.ad_counts[an] = self.ad_counts[an] + 1
        print "Ad net domains:"
        for ad_net, domains in ad_net_domains.iteritems():
            if len(domains) > 10:
                print ad_net, len(domains), random.sample(domains, 10)
            else:
                print ad_net, len(domains), domains
        # print "Ad net domains:", pprint.pprint(ad_net_domains)
                    

            # print "Ad network:", an
            # import ipdb; ipdb.set_trace()
        print "Malicious ad network counts:", self.mal_ad_counts
        print "Ad network counts:", self.ad_counts
        print "Total # of SE attacks", sum([x for x in self.mal_ad_counts.values()])
        print "Total # of landing pages", sum([x for x in self.ad_counts.values()])

    # Remove clusters of size < MIN_CLUSTER_SIZE and ERROR_CLUSTERS
    def filter_clusters(self,):
        original_clusters = len(self.clusters)
        under_sized_clusters = 0
        error_clusters = 0
        for key in self.clusters.keys():
            if len(self.clusters[key]) < MIN_CLUSTER_SIZE:
                del self.clusters[key]
                under_sized_clusters = under_sized_clusters + 1
            elif (int(key) in ERROR_CLUSTERS or int(key) in ADULT_AD_CLUSTERS or 
                int(key) in ERROR_404_CLUSTERS or int(key) in FULL_AD_CLUSTERS):
                del self.clusters[key]
                error_clusters = error_clusters + 1
        print "Under-sized clusters: ", under_sized_clusters
        print "Original clusters (after removing under-sized):", original_clusters - under_sized_clusters 
        print "Non-malicious clusters:", error_clusters
        print "# SE ad clusters:", len(self.clusters) 
        with open(FILTERED_CLUSTERS_PATH, "wb") as f:
            f.write(json.dumps(self.clusters))
        import ipdb; ipdb.set_trace()

    def fetch_clustered_data(self,):
        self.clustered_ad_objs = ad_object.parse_ad_objects(CLUSTERED_ADOBJECTS_PATH)
        self.res_clustered_ad_objs = ad_object.parse_ad_objects(RES_CLUSTERED_ADOBJECTS_PATH)
        with open(CLUSTERS_PATH) as f:
            self.clusters = json.loads(f.readline())
        with open(RES_CLUSTERS_PATH) as f:
            self.res_clusters = json.loads(f.readline())
        print len(self.clusters)
        print len(self.clustered_ad_objs)
            
    # Fetch the relevant data into self.data_dict
    def fetch_data(self,):
        ad_obj_files = os.listdir(ADOBJECTS_PATH)
        print len(ad_obj_files)
        for ad_obj_file in ad_obj_files:
            ad_obj_fpath = os.path.join(ADOBJECTS_PATH, ad_obj_file)
            ad_objs = ad_object.parse_ad_objects(ad_obj_fpath)
            self.ad_objects = self.ad_objects + ad_objs
        print "Done loading all ad_objects into memory; %s ads" % (len(self.ad_objects),)

def main():
    t1 = time.time()
    ma = MalAdAttributer()
    t2 = time.time()
    print "Time:", t2-t1


if __name__ == "__main__":
    main()
