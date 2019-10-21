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
#!/usr/bin/env python

"""Keeps local Google Safe Browsing cache in sync.

Accessing Google Safe Browsing API requires API key, you can find
more info on getting it here:
https://developers.google.com/safe-browsing/lookup_guide#GettingStarted

"""

import sys
import time
from datetime import datetime
import json
import tldextract
import collections

from gglsbl import SafeBrowsingList
from se_categories_v4 import se_categories
import ad_object

print "# of SE clusters:",  sum([len(x) for x in se_categories.values()])
# sys.exit()

gsb_key = ''
# gsb_db_path = '/home/phani/se-hunter/milking/gsb_vt/gsb_v4.db'
gsb_db_path = 'gsb_v4.db'
CLUSTERED_ADOBJECTS_PATH = "/home/phani/se_hunter_results/clustered_ad_objects_v4.json"
CLUSTERS_PATH = "/home/phani/se_hunter_results/filtered_clusters_v4.json"
RES_CLUSTERED_ADOBJECTS_PATH = "/home/phani/se_hunter_results/res_clustered_ad_objects_v4.json"
RES_CLUSTERS_PATH = "/home/phani/se_hunter_results/res_clusters_v4.json"
CATEGORY_DICT = "/home/phani/se-hunter/selenium/job_handling/categories/category_dict.json"
ALL_OBJECT_STATS = "/home/phani/se_hunter_results/all_object_dump.json"
POPULARITY_RANKS = "/home/phani/se-hunter/seeds/seed_rankings.txt"
PUBLISHER_SITES_ATTEMPTED = "/home/phani/se-hunter/selenium/job_handling/done_jobs_domains.txt"
POPULARTIY_GRAPH_DATA = "/home/phani/se_hunter_results/popularity_graph_data.json"
SEED_DOMAIN_DATA = "/home/phani/se_hunter_results/misc_ad_object_info.txt"
SEED_DOMAIN_DATA_2 = "/home/phani/se_hunter_results/misc_ad_object_info_2.txt"

clustered_ad_objects = ad_object.parse_ad_objects(CLUSTERED_ADOBJECTS_PATH)
with open(CATEGORY_DICT) as f:
    categories_dict = json.loads(f.readline())
with open(CLUSTERS_PATH) as f:
    clusters = json.loads(f.readline())
res_clustered_ad_objects = ad_object.parse_ad_objects(RES_CLUSTERED_ADOBJECTS_PATH)
with open(RES_CLUSTERS_PATH) as f:
    res_clusters = json.loads(f.readline())
with open(ALL_OBJECT_STATS) as f:
    all_object_stats = json.loads(f.readline())
with open(POPULARITY_RANKS) as f:
    popularity_ranks = json.load(f)
with open(PUBLISHER_SITES_ATTEMPTED) as f:
    publisher_sites_attempted = json.loads(f.readline())
with open(SEED_DOMAIN_DATA) as f:
    seed_domain_data = json.load(f)
with open(SEED_DOMAIN_DATA_2) as f:
    seed_domain_data.update(json.load(f))
all_pub_fqd = all_object_stats['all_pub_fqd']
all_land_tlds = all_object_stats['all_land_tlds']
image_hash_count = all_object_stats['image_hash_count']
image_domain_dict = all_object_stats['image_domain_dict']
image_home_domain_dict = all_object_stats['image_home_domain_dict']
image_seed_domain_dict = all_object_stats['image_seed_domain_dict']
mal_ad_hashes = set()

print "Length of all publisher fqd:", len(all_pub_fqd) 
# print "Length of all publisher fqd:", len(all_pub_fqd) 

# tld_list = [(x[0], len(x[1])) for x in all_land_tlds.iteritems()]
# tld_list = sorted(tld_list, key=lambda x:x[1], reverse=True)
# print tld_list[:30]
# import ipdb; ipdb.set_trace()


extractor = tldextract.TLDExtract(suffix_list_urls=None)

def get_ad_objects(label):
    ad_objs = [clustered_ad_objects[i] for i in clusters[label]]
    res_ad_objs = []
    if label in res_clusters:
        res_ad_objs = [res_clustered_ad_objects[i] for i in res_clusters[label]]
    # return []
    # return res_ad_objs
    return ad_objs + res_ad_objs


def get_category_stats(all_domains):
    # the category stats have domains exclude www in the beginning, so we should remove it as
    # well to match
    all_domains = [x[4:] for x in all_domains]
    category_count = collections.defaultdict(int)
    category_set = collections.defaultdict(set)
    not_in = 0
    for domain in all_domains:
        if domain not in categories_dict:
            # print domain, "not in dict"
            not_in += 1
            continue
        categories_list = categories_dict[domain]
        for cat in categories_list:
            category_count[cat] += 1
            category_set[cat].add(domain)
    for category in category_set:
        print category, random.sample(category_set[category], 3)
    print "not ins:", not_in
    del category_count['Uncategorized'] # Removing "Uncategorized" publisher domains
    sorted_items = sorted(category_count.items(), reverse=True, key=lambda x: x[1])
    total = sum([x[1] for x in sorted_items])
    print "Total home domains categorized:", total
    for cat, count in sorted_items[:20]:
        print cat, "\t&", count, "\t&", "%.2f" % (count*100.0/total),"\\\\"
    # import ipdb; ipdb.set_trace()

def get_popularity_stats(domains):
    # the popularity stats have domains exclude www in the beginning, so we should remove it as
    # well to match
    domains = [x[4:] for x in domains]
    popularity_tiers = [1000, 5000, 10000, 50000, 100000, 500000, 10**6, 30 * 10**6, 31 * 10**6]
    popularity_counts = [0] * len(popularity_tiers)
    not_ins = 0
    se_ad_pub_rank_list = []
    all_pub_rank_list = []
    for domain in domains:
        if domain not in popularity_ranks:
            not_ins += 1
            continue
        rank = popularity_ranks[domain]
        se_ad_pub_rank_list.append(rank)
        if rank < 5000:
            print domain, rank
        for i in range(len(popularity_tiers)):
            # if rank < popularity_tiers[i] and (i==0 or rank >= popularity_tiers[i-1]):
            if rank < popularity_tiers[i]:
                popularity_counts[i] += 1
    print "Not ins: ", not_ins
    print popularity_tiers 
    print popularity_counts
    not_ins = 0
    for pub_site in publisher_sites_attempted:
        if pub_site not in popularity_ranks:
            not_ins += 1
            continue
        rank = popularity_ranks[pub_site]
        all_pub_rank_list.append(rank)
    print "Not ins: ", not_ins
    with open(POPULARTIY_GRAPH_DATA, 'wb') as f:
        f.write(json.dumps({'se_ad_pub_rank_list': se_ad_pub_rank_list,
                            'all_pub_rank_list': all_pub_rank_list}))

def main():
    total_attacks = 0
    sbl = SafeBrowsingList(gsb_key, db_path=gsb_db_path)
    all_home_domains = set()
    counted_hashes = set()
    for name, labels in se_categories.iteritems():
        camp_domains = set()
        camp_gsb_clusters = 0
        camp_total_count = 0
        home_domains_campaign_set = set()
        for label in labels:
            cluster_gsb = False
            cluster_domains = set()
            ad_objs = get_ad_objects(str(label))
            # camp_total_count += len(ad_objs)
            for ad_obj in ad_objs:
                domain = extractor(ad_obj.ad_url).registered_domain
                e = extractor(ad_obj.ad_url)
                land_fqd =  '.'.join(part for part in e if part) 
                # home_domain = extractor(ad_obj.home_url).registered_domain
                e = extractor(seed_domain_data[ad_obj.log_id][0])
                home_domain = '.'.join(part for part in e if part) 
                # camp_domains.add(domain)
                if ad_obj.screenshot_hash in image_domain_dict:
                # if domain in all_land_tlds:
                    if ad_obj.screenshot_hash not in counted_hashes:
                        mal_ad_hashes.add(ad_obj.screenshot_hash)
                        camp_total_count += image_hash_count[ad_obj.screenshot_hash]
                        counted_hashes.add(ad_obj.screenshot_hash)
                        # home_domains_campaign_set = home_domains_campaign_set.union(image_home_domain_dict[ad_obj.screenshot_hash])
                        home_domains_campaign_set = home_domains_campaign_set.union(image_seed_domain_dict[ad_obj.screenshot_hash])
                        camp_domains = camp_domains.union(image_domain_dict[ad_obj.screenshot_hash])
                        cluster_domains = cluster_domains.union(image_domain_dict[ad_obj.screenshot_hash])
                        # all_home_domains = all_home_domains.union(image_home_domain_dict[ad_obj.screenshot_hash])
                        all_home_domains = all_home_domains.union(image_seed_domain_dict[ad_obj.screenshot_hash])
                else:
                    print "!!Not here!!"
                    camp_domains.add(land_fqd)
                    cluster_domains.add(land_fqd)
                    camp_total_count += 1
                    # import ipdb; ipdb.set_trace()
                    all_home_domains.add(home_domain)
            for domain in cluster_domains:
                if not domain:
                    continue
                # print "domain:", domain
                result = sbl.lookup_url(domain.strip())
                if result:
                    cluster_gsb = True
            if cluster_gsb:
                camp_gsb_clusters += 1
            # print result
        print name, '\t&',  camp_total_count, '\t&', len(camp_domains), '\t&', len(labels), '\t&', camp_gsb_clusters, '\\\\'
        print len(home_domains_campaign_set)
        total_attacks += camp_total_count
    print "# of mal ad hashes:", len(mal_ad_hashes)
    print "# of unique publisher domains associated with SE ads:", len(all_home_domains)
    print "# of total SE attacks:", total_attacks
    # get_category_stats(all_home_domains)
    get_popularity_stats(all_home_domains)

if __name__ == '__main__':
    main()
