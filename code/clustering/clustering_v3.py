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
from sklearn.cluster import DBSCAN
import sklearn.metrics
import json
import numpy as np
import scipy as sp
import time
import numexpr as ne
import urlparse


import ad_object
import image_hash_utils

ADOBJECTS_PATH = "/home/phani/ad_objects"
CLUSTER_SCREENSHOTS_PATH = "/home/phani/se_hunter_results/cluster_screenshots_v3"
ARCHIVES_DIR_PATH = "/data/se_hunter_1"
CLUSTERED_ADOBJECTS_PATH = "/home/phani/se_hunter_results/clustered_ad_objects_v3.json"
CLUSTERS_PATH = "/home/phani/se_hunter_results/clusters_v3.json"
IMAGE_EXTENSIONS_FILE = "image-extensions.json"

N_JOBS = 25
MIN_SAMPLES = 3
# Minum size of the cluster (after removing repeating ad domain samples). If not, weed out the cluster
MIN_CLUSTER_SIZE = 3 
# Minimum number of samples that should be core in a cluster, if not weed out the cluster
MIN_CORE_FRACTION = 0.5 

with open(IMAGE_EXTENSIONS_FILE) as f:
    image_extensions = set(json.loads(f.readline()))

def is_image_extension(url):
    try:
        url_struct = urlparse.urlparse(url)
        fname = os.path.basename(url_struct.path)
        ext = fname.rsplit(".", 1)[1] if "." in fname else ""
        if ext in image_extensions:
            # print ext
            # import ipdb; ipdb.set_trace()
            return True
    except:
        pass
    return False

class ImageClusterer:
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
        self.fetch_data()
        self.cluster_images()

    def fetch_an_image(self, label):
        ad = self.ad_objects[self.clusters[label][0]]
        archive_path = os.path.join(ARCHIVES_DIR_PATH, "logs_%s.tar.gz" % (ad.log_id,))
        subprocess.call("tar -xzvf %s >/dev/null" % (archive_path,), shell=True)
        image_path = os.path.join(ad.log_id, "screenshots", ad.screenshot)
        target_image_path = os.path.join(CLUSTER_SCREENSHOTS_PATH, 
                                        "%s_%s.png" % (label, len(self.clusters[label])))
        subprocess.call("cp %s %s" % (image_path, target_image_path), shell=True)
        subprocess.call("rm -rf %s" % (ad.log_id,), shell=True)
        
    # Fetch the relevant data into self.data_dict
    def fetch_data(self,):
        ad_obj_files = os.listdir(ADOBJECTS_PATH)
        print len(ad_obj_files)
        for ad_obj_file in ad_obj_files:
            ad_obj_fpath = os.path.join(ADOBJECTS_PATH, ad_obj_file)
            ad_objs = ad_object.parse_ad_objects(ad_obj_fpath)
            self.ad_objects = self.ad_objects + ad_objs
        print "Done loading all ad_objects into memory; %s ads" % (len(self.ad_objects),)

    def cluster_images(self,):
        domain_id_ctr = 0
        for index, ad in enumerate(self.ad_objects):
            ad_domain =  self.tld_extract(ad.ad_url).registered_domain
            if (ad_domain + "." + ad.screenshot_hash) in self.domain_hashes:
                continue
            if ad_domain not in self.domain_ids:
                self.domain_ids[ad_domain] = domain_id_ctr
                domain_id_ctr = domain_id_ctr + 1
            self.domain_hashes.add(ad_domain + "." + ad.screenshot_hash)
            self.input_indices.append(index)
            self.feature_matrix_hash.append(
                    image_hash_utils.convert_image_hash_to_array(ad.screenshot_hash))
            self.feature_matrix_domain.append(
                    [self.domain_ids[ad_domain]]) 
            
        print "Done with feature extraction", len(self.feature_matrix_hash), len(self.feature_matrix_domain)
        t1 = time.time()
        self.feature_matrix_hash = np.array(self.feature_matrix_hash)
        # distance_matrix = sklearn.metrics.pairwise.pairwise_distances(
                            # self.feature_matrix, metric=distance_metric, n_jobs=1)
        distance_matrix_hash = sklearn.metrics.pairwise.pairwise_distances(
                            self.feature_matrix_hash, metric="hamming", n_jobs=N_JOBS)
        t2 = time.time()
        self.feature_matrix_domain = np.array(self.feature_matrix_domain)
        print "Dist. matrix 1 computation time:", t2 - t1
        distance_matrix_domain = sklearn.metrics.pairwise.pairwise_distances(
                            self.feature_matrix_domain, metric="hamming", n_jobs=N_JOBS)
        t3 = time.time()
        print "Dist. matrix 2 computation time:", t3 - t2
        # import ipdb; ipdb.set_trace()
        # distance_matrix = sp.sparse.csr_matrix(distance_matrix_domain).multiply(sp.sparse.csr_matrix(distance_matrix_hash))
        distance_matrix = ne.evaluate('distance_matrix_domain * distance_matrix_hash')
        t4 = time.time()
        print "Dist. matrix 3 computation time:", t4 - t3
        # distance_matrix_domain = 1 - sp.sparse.csr_matrix(distance_matrix_domain)
        # distance_matrix_domain = sp.sparse.csr_matrix(distance_matrix_domain)
        # distance_matrix_domain.data *= -1
        # distance_matrix_domain.data += 1
        distance_matrix_domain = ne.evaluate('1 - distance_matrix_domain')
        t5 = time.time()
        print "Dist. matrix 4 computation time:", t5 - t4
        distance_matrix = ne.evaluate('distance_matrix + distance_matrix_domain')
        t6 = time.time()
        print "Dist. matrix 5 computation time:", t6 - t5
        db = DBSCAN(eps=0.05, min_samples=MIN_SAMPLES, n_jobs=N_JOBS, metric="precomputed").fit(distance_matrix)
        t7 = time.time()
        print "Dist. matrix 6 computation time:", t7 - t6
        print "Done with clustering", len(db.labels_)

        # import ipdb; ipdb.set_trace()
        for index, label in enumerate(db.labels_):
            if label == -1:
                continue
            ad_object_index = self.input_indices[index]
            if label not in self.clusters:
                self.clusters[label] = []
            self.clusters[label].append(ad_object_index)

        print "# of clusters:", len(self.clusters)
        # prune clusters to remove clusters that:
        # a. don't have distinct domains 
        # b. dhave < MIN_CLUSTER_SIZE distinct ad_domains
        # also, remove repeated domain ad_objects
        for label in self.clusters.keys():
            ad_domains = set()
            new_index_list = []
            core_sample_count = 0
            image_count = 0
            for i in self.clusters[label]:
                ad_domain =  self.tld_extract(self.ad_objects[i].ad_url).registered_domain
                if is_image_extension(self.ad_objects[i].ad_url):
                    image_count = image_count + 1
                if ad_domain not in ad_domains:
                    ad_domains.add(ad_domain)
                    new_index_list.append(i)
                # Note: i is the ad_object index, we then get input_indices index and the query it
                # in  core_sample_indices_
                input_indices_index = self.input_indices.index(i)
                if input_indices_index in db.core_sample_indices_:
                    core_sample_count = core_sample_count + 1
            # print core_sample_count, len(self.clusters[label])
            core_fraction = (core_sample_count * 1.0) / len(self.clusters[label])
            # print core_fraction
            # print ad_domains
            if (len(ad_domains) < MIN_CLUSTER_SIZE) or (core_fraction < MIN_CORE_FRACTION) or (image_count > 0):
                del self.clusters[label]
            else:
                self.clusters[label] = new_index_list

        print "# of clusters after pruning:", len(self.clusters)
        import ipdb; ipdb.set_trace()

        clustered_ad_objects = []
        clustered_ad_objects_index = 0
        dump_clusters = {}   # 
        cluster_screenshots = []
        # We use int() as label names are all integers
        # cluster_screenshots = set([int(x.split('_')[0]) for x in os.listdir(CLUSTER_SCREENSHOTS_PATH)])
        for label, ad_object_indices in self.clusters.iteritems():
            if label == -1:
                continue
            # if label not in cluster_screenshots:
                # self.fetch_an_image(label)
            dump_clusters[label] = []
            for index in ad_object_indices:
                clustered_ad_objects.append(self.ad_objects[index])
                dump_clusters[label].append(clustered_ad_objects_index)
                clustered_ad_objects_index = clustered_ad_objects_index + 1
        ad_object.dump_ad_objects(CLUSTERED_ADOBJECTS_PATH, clustered_ad_objects)
        with open(CLUSTERS_PATH, "wb") as f:
            f.write(json.dumps(dump_clusters))
        print "Dumped only the clustered ad_objects; %s ads" % (len(clustered_ad_objects),)
        # import ipdb; ipdb.set_trace()


def main():
    t1 = time.time()
    ic = ImageClusterer()
    t2 = time.time()
    print "Time:", t2-t1


if __name__ == "__main__":
    main()
