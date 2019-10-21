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
import dhash
from PIL import Image
import shutil

import ipdb


SCREENSHOTS_PATH = "/home/phani/se-hunter/logs/screenshots"
SEHUNTER_LOGS_PATH = "/home/phani/se-hunter/logs/sehunter_logs"
CLUSTER_DIR_PATH = '/home/phani/scratch/clusters'
# Only parse log files if their last mod time is > than this
PARSING_AGE = 300

class ImageClusterer:
    def __init__(self,):
        # IMAGE FILENAME --> [Ad URL, Ad URL domain, HOME DOMAIN URL]
        self.data_dict = {}
        self.log_file_paths = []
        self.tld_extract = tldextract.TLDExtract(suffix_list_urls=None)
        # Ad URL domain --> File path
        self.images = {}
        # Image hash --> file path
        self.clusters = {}

        self.fetch_data()
        self.compute_hashes()
        self.copy_image_clusters()

    def get_log_files(self,):
        log_files = os.listdir(SEHUNTER_LOGS_PATH)
        log_files = [k for k in log_files if not k.startswith('.')]
        current_time = time.time()
        for log_file in log_files:
            file_path = os.path.join(SEHUNTER_LOGS_PATH, log_file)
            mtime = os.path.getmtime(file_path)
            if (current_time - mtime) > PARSING_AGE:
                self.log_file_paths.append(file_path)

    def parse_log_file(self, log_file):
        home = ""
        with open(log_file) as f:
            while True:
                line = f.readline()
                if not line:
                    break
                if not home:
                    if ":Screenshot: " in line and "URL" in line:
                        home =  line.strip().rsplit(' ', 1)[1]
                if ":3rd party page URL: " in line:
                    next_line = f.readline()
                    if ":Screenshot: " in next_line:
                        ad_url = line.strip().rsplit(' ', 1)[1]
                        ad_url_domain =  self.tld_extract(ad_url).registered_domain
                        image_fpath = next_line.strip().rsplit(' ', 1)[1]
                        self.data_dict[image_fpath] = [ad_url, ad_url_domain, home]

    def get_images(self):
        for file_path, url_tuple in self.data_dict.iteritems():
            self.images[url_tuple[1]] = file_path

    # Fetch the relevant data into self.data_dict
    def fetch_data(self,):
        self.get_log_files()
        for log_file in self.log_file_paths:
            self.parse_log_file(log_file)
        self.get_images()
        print len(self.data_dict)
        print "# of images: %s" % (len(self.images),)
        #ipdb.set_trace()

    def compute_hashes(self,):
        for ad_domain, image_path in self.images.iteritems():
            image = Image.open(image_path)
            row, col = dhash.dhash_row_col(image)
            hash = dhash.format_hex(row, col)
            if hash not in self.clusters:
                self.clusters[hash] = []
            self.clusters[hash].append(image_path)

    def copy_image_clusters(self,):
        counter = 1
        total_clustered_images = 0
        for hash, image_list in self.clusters.iteritems():
            if len(image_list) == 1:
                continue
            cluster_dir_path = os.path.join(CLUSTER_DIR_PATH, "cluster_%s" % (counter,))
            if not os.path.exists(cluster_dir_path):
                os.mkdir(cluster_dir_path)
            print "Cluster # %s:" % (counter,)
            print [self.data_dict[i][1] for i in image_list]
            print "*" * 20
            total_clustered_images = total_clustered_images + len(image_list)
            for image in image_list:
                shutil.copy(image, cluster_dir_path)
            counter = counter + 1
        print "Total # of clustered images: %s" % (total_clustered_images,)



def main():
    ic = ImageClusterer()


if __name__ == "__main__":
    main()
