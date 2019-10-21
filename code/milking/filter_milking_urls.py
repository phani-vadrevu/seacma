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
import os
import urllib
import tldextract
import itertools

import config
import image_hash_utils
HOME = os.getenv('HOME')
MILKING_URLS_PATH = os.path.join(HOME, 'se-hunter/milking/milking_urls.json')
MILKING_PART1_DATA_PATH = os.path.join(HOME, 'se-hunter/selenium/job_handling/done_milking_1_jobs.txt')
FILTERED_MILKING_SOURCES = os.path.join(HOME,
                            'se-hunter/selenium/job_handling/filtered_milkingsources.json')
# Preference order for UAs used in milking; useful when filtering jobs based on UAs
UA_PREF_ORDER = ["edge_win", "chrome_mac", "ie_win", "chrome_android"]

    
def get_milking_part1_data_dump():
    milking_part1_data = []
    with open(MILKING_PART1_DATA_PATH) as f:
        for line in f:
            milking_part1_data.append(json.loads(line))
    return milking_part1_data

# Take the milking_part1_data and arrange it in a dictionary 
def get_milking_part1_data():
    milking_part1_data_dump = get_milking_part1_data_dump()  
    print len(milking_part1_data_dump)
    milking_part1_dict = {}
    for entry in milking_part1_data_dump:
        agent, url = entry['job_name'].split(':')
        url = urllib.unquote_plus(url)
        if (agent, url) not in milking_part1_dict:
            milking_part1_dict[(agent, url)] = []
        milking_part1_dict[(agent, url)].append(entry)
    return milking_part1_dict

# If a milking job results in same final domains as we already know
# in all the attempt, we can safely eliminate them
def filter_same_ad_domains(milking_part1_dict, ad_domains):
    tld_extractor = tldextract.TLDExtract(suffix_list_urls=None)
    new_milking_part1_dict = {}
    for entry_key, entry_list in milking_part1_dict.iteritems():
        different_ad_domain = False
        for entry in entry_list:  
            final_domain = tld_extractor(entry['loaded_url']).registered_domain
            if final_domain not in ad_domains:
                different_ad_domain = True
        if different_ad_domain:
            new_milking_part1_dict[entry_key] = entry_list
    return new_milking_part1_dict


# Remove jobs that have hashes that are unrelated to the known image hashes
def filter_different_hash_jobs(milking_part1_dict, image_hashes):
    new_milking_part1_dict = {}
    same_hash_counter = 0
    similar_hash_counter = 0
    for entry_key, entry_list in milking_part1_dict.iteritems():
        same_hash = False
        for entry in entry_list:  
            if entry['image_hash'] in image_hashes:
                same_hash = True
                break
        if same_hash:
            same_hash_counter = same_hash_counter + 1
            new_milking_part1_dict[entry_key] = entry_list
            continue
        similar_hash = False
        for entry in entry_list:  
            if image_hash_utils.is_known_similar_hash(entry['image_hash'], image_hashes):
                similar_hash = True
                break
        if similar_hash:
            similar_hash_counter = similar_hash_counter + 1
            new_milking_part1_dict[entry_key] = entry_list
        
    print "Jobs with atleast 1 known image hash", same_hash_counter
    print "Jobs with atleast 1 similar known image hash", similar_hash_counter
    return new_milking_part1_dict

def inspect_homogenity_of_hashes(milking_part1_dict):
    homogenous = 0
    non_homogenous = 0
    for entry_key, entry_list in milking_part1_dict.iteritems():
        image_hash_list = [e['image_hash'] for e in entry_list]
        image_hashes = set(image_hash_list)
        if image_hash_utils.are_homogenous_hashes(image_hashes):
            homogenous = homogenous + 1
        else:
            import ipdb; ipdb.set_trace()
            non_homogenous = non_homogenous + 1
    print "Homogenous job: %s, Non-homogenous jobs: %s" % (homogenous, non_homogenous)
        
def find_an_image_hash(image_hash, milking_part1_dict):
    for entry_key, entry_list in milking_part1_dict.iteritems():
        image_hash_list = [e['image_hash'] for e in entry_list]
        image_hashes = set(image_hash_list)
        if image_hash_utils.is_known_similar_hash(image_hash, image_hashes):
            print "Found a milking cluster for ", image_hash
            import ipdb; ipdb.set_trace()

def filter_upstream_milking_urls(milking_part1_dict, milking_jobs):
    new_milking_part1_dict = {}
    other_milking_dict = {}
    for entry_key, entry_list in milking_part1_dict.iteritems():
        if entry_key in milking_jobs:
            new_milking_part1_dict[entry_key] = entry_list
        else:
            other_milking_dict[entry_key] = entry_list
    return new_milking_part1_dict, other_milking_dict
    
def filter_more_upstream_milking_urls(milking_part1_dict, upstream_milking_dict, upstream_domains):
    new_milking_part1_dict = {}
    tld_extractor = tldextract.TLDExtract(suffix_list_urls=None)
    for entry_key, entry_list in milking_part1_dict.iteritems():
        agent, milking_url = entry_key
        milking_domain = tld_extractor(milking_url).registered_domain
        if not milking_domain in upstream_domains:
            new_milking_part1_dict[entry_key] = entry_list
        else: 
            upstream_milking_dict[entry_key] = entry_list
    return new_milking_part1_dict, upstream_milking_dict

def get_milking_jobs_for_url(milking_part1_dict, url):
    return set([(a, url) for a in UA_PREF_ORDER if (a, url) in milking_part1_dict])
    

def are_jobs_similar(milking_part1_dict, job1, job2):
    loaded_urls_1 = set([e['loaded_url'] for e in milking_part1_dict[job1]]) 
    loaded_urls_2 = set([e['loaded_url'] for e in milking_part1_dict[job2]]) 
    if loaded_urls_1 != loaded_urls_2:
        return False
    image_hashes_1 = set([e['image_hash'] for e in milking_part1_dict[job1]])
    image_hashes_2 = set([e['image_hash'] for e in milking_part1_dict[job2]])
    return image_hash_utils.are_hashes_similar(image_hashes_1, image_hashes_2)


def get_unique_jobs(milking_part1_dict, url):
    milking_jobs_set = get_milking_jobs_for_url(milking_part1_dict, url)
    remove_jobs_set = set()
    job_combines = [x for x in itertools.combinations(milking_jobs_set, 2)]
    for j1, j2 in job_combines:
        if (j1 in remove_jobs_set) or (j2 in remove_jobs_set):
            continue
        if not are_jobs_similar(milking_part1_dict, j1, j2):
            continue
        # print "%s and %s jobs are ssimilar for url %s" % (j1[0], j2[0], j1[1])
        if UA_PREF_ORDER.index(j1[0]) < UA_PREF_ORDER.index(j2[0]):
            remove_jobs_set.add(j2)
        else:
            remove_jobs_set.add(j1)
    return milking_jobs_set.difference(remove_jobs_set) 


def filter_repeated_by_agent(milking_part1_dict):
    new_milking_part1_dict = {}
    milking_url_set = set([m for (a, m) in milking_part1_dict])
    for url in milking_url_set:
        unique_jobs = get_unique_jobs(milking_part1_dict, url)
        for job in unique_jobs:
            new_milking_part1_dict[job] = milking_part1_dict[job]
    return new_milking_part1_dict


def measure_time_per_job(milking_part1_dict):
    total_time_taken = 0
    total_jobs = 0
    for entry_key, entry_list in milking_part1_dict.iteritems():
        for e in entry_list:
            total_time_taken = total_time_taken + float(e['total_time'])
            total_jobs = total_jobs + 1
    print "Total time: %s, Total jobs: %s" % (total_time_taken, total_jobs)
    print "Avg time: %s" % (total_time_taken / total_jobs)

def measure_num_downloads(milking_part1_dict):
    total_jobs_download = 0
    total_jobs = 0
    milkers_with_no_downloads = 0
    for entry_key, entry_list in milking_part1_dict.iteritems():
        atleast_one_download = False
        for e in entry_list:
            if e['downloaded_files'] == "True":
                total_jobs_download = total_jobs_download + 1
                atleast_one_download = True
            total_jobs = total_jobs + 1
        if not atleast_one_download:
            # import ipdb; ipdb.set_trace()
            milkers_with_no_downloads = milkers_with_no_downloads + 1
    print "Jobs with downloads: ", total_jobs_download
    print "Total jobs: ", total_jobs
    print "Milkers with no downloads: ", milkers_with_no_downloads
    

def get_milking_source_line(entry_key, entry_list, category):
    milking_sources_dict = {}
    milking_sources_dict['job_name'] = entry_list[0]["job_name"]
    milking_sources_dict['image_hashes'] = list(set(
        [e['image_hash'] for e in entry_list if e['image_hash'] != image_hash_utils.ZERO_HASH]))
    milking_sources_dict['category'] = category
    return json.dumps(milking_sources_dict)


def generate_milk_sources_file(milking_part1_dict, upstream_milking_dict):
    with open(FILTERED_MILKING_SOURCES, 'wb') as f:
        for entry_key, entry_list in milking_part1_dict.iteritems():
            f.write(get_milking_source_line(entry_key, entry_list, "MILKING") + '\n')
        for entry_key, entry_list in upstream_milking_dict.iteritems():
            f.write(get_milking_source_line(entry_key, entry_list, "UPSTREAM") + '\n')
    print len(milking_part1_dict), len(upstream_milking_dict)


def main():
    with open(MILKING_URLS_PATH) as f:
        milking_urls_data = json.loads(f.readline())
    milking_urls = milking_urls_data['milking_urls']
    ad_domains = set(milking_urls_data['ad_domains'])
    image_hashes = set(milking_urls_data['image_hashes'])
    upstream_domains = set(milking_urls_data['upstream_domains'])
    # milking_jobs will get progressively filtered by this script
    milking_jobs = set([(a, m) for m in milking_urls for a in config.USER_AGENTS.keys()])
    milking_part1_dict = get_milking_part1_data()
    print len(milking_jobs), len(milking_part1_dict)
    # print len(set([y for (x,y) in milking_part1_dict.keys()]))

    milking_part1_dict = filter_same_ad_domains(milking_part1_dict, ad_domains)
    print "After same domain filtering, # of jobs left:", len(milking_part1_dict)

    milking_part1_dict = filter_different_hash_jobs(milking_part1_dict, image_hashes)
    print "After removing jobs that result in unknown hashes, # of jobs left", len(milking_part1_dict) 

    # There was a bug in the initial milking url extraction script that casued 
    # upstream URLs from broken redirections to be included in the milking URLs
    # Here, we filter that data from the results of part1 expeirment 
    # milking_jobs now contains the correct milking jobs
    milking_part1_dict, upstream_milking_dict = filter_upstream_milking_urls(
                                                            milking_part1_dict,
                                                            milking_jobs)
    print "After removing upstream URL jobs, # of jobs left", len(milking_part1_dict) 

    milking_part1_dict, upstream_milking_dict = filter_more_upstream_milking_urls(
                                milking_part1_dict, upstream_milking_dict, upstream_domains)
    print "After removing more upstream URL jobs, # of jobs left", len(milking_part1_dict) 

    milking_part1_dict = filter_repeated_by_agent(milking_part1_dict)
    print "After retaining only jobs with useful UAs,  # of jobs left", len(milking_part1_dict) 

    # inspect_homogenity_of_hashes(milking_part1_dict)
    # Amazon lucky draw
    # find_an_image_hash("160e0f74d91b8e70ff001e64c37fbe00", milking_part1_dict)
    # Windows support scams
    # find_an_image_hash("24828c8c93b00c00fc836018bf00fc00", milking_part1_dict)
    # find_an_image_hash("c3848c848b848000e3778870ab000000", milking_part1_dict)
    find_an_image_hash("b2920e53170e0c0cf7ff0880773e081c", milking_part1_dict)
    # measure_time_per_job(milking_part1_dict)
    # measure_num_downloads(milking_part1_dict)
    # generate_milk_sources_file(milking_part1_dict, upstream_milking_dict)


if __name__ == "__main__":
    main()
