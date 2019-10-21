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
import subprocess
import os
import json

import ad_object

ADOBJECTS_PATH = "/home/phani/ad_objects"
CLUSTER_SCREENSHOTS_PATH = "/home/phani/se_hunter_results/cluster_screenshots_v4"
ARCHIVES_DIR_PATH = "/data/se_hunter_1"
CLUSTERED_ADOBJECTS_PATH = "/home/phani/se_hunter_results/clustered_ad_objects_v4.json"
CLUSTERS_PATH = "/home/phani/se_hunter_results/clusters_v4.json"

def fetch_an_image(label, ad_objects, clusters):
    ad = ad_objects[clusters[label][0]]
    archive_path = os.path.join(ARCHIVES_DIR_PATH, "logs_%s.tar.gz" % (ad.log_id,))
    subprocess.call("tar -xzvf %s >/dev/null" % (archive_path,), shell=True)
    image_path = os.path.join(ad.log_id, "screenshots", ad.screenshot)
    target_image_path = os.path.join(CLUSTER_SCREENSHOTS_PATH, 
                                    "%s_%s.png" % (label, len(clusters[label])))
    subprocess.call("cp %s %s" % (image_path, target_image_path), shell=True)
    subprocess.call("rm -rf %s" % (ad.log_id,), shell=True)


def main():
    clustered_ad_objects = ad_object.parse_ad_objects(CLUSTERED_ADOBJECTS_PATH)
    with open(CLUSTERS_PATH) as f:
        clusters = json.loads(f.readline())
    import ipdb; ipdb.set_trace()
    for label in clusters:
        fetch_an_image(label, clustered_ad_objects, clusters)


if __name__ == "__main__":
    main()
