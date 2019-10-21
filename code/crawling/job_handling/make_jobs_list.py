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
import random
import json

import config

HOME = os.getenv('HOME')
SEEDS_DIR_PATH = os.path.join(HOME, "se-hunter/seeds/seed_lists")
RANKS_PATH = os.path.join(HOME, "se-hunter/seeds/seed_rankings.txt")
# The interval indicates how many seeds are taken from sorted list in order to randomize. This will ensure
# that not all servers will visit the same website at the same time
RANDOMIZATION_INTERVAL = 100
ua_names =  config.USER_AGENTS.keys()


# Randomizes the seeds, pairs with all UAs and gives a list of job strings
# Example: ["chrome_mac:mp3clouddownload.com", "ie_win:yahoo.com"]
def get_jobs(seeds):
    job_list = ["%s:%s" % (ua, s[0]) for ua in ua_names for s in seeds]
    random.shuffle(job_list)
    return job_list


def write_jobs_list(seed_list, file_name):
    file_ptr = open(file_name, "wb")
    while len(seed_list) > 0:
        current_seeds = seed_list[:RANDOMIZATION_INTERVAL]
        seed_list = seed_list[RANDOMIZATION_INTERVAL:]
        jobs = get_jobs(current_seeds)
        for job in jobs:
            file_ptr.write(job + "\n")
    file_ptr.close()

def write_popularity_ranks(seed_files):
    seeds = set()
    ranks_dict = {}
    for seed_file in seed_files:
        seed_file_path = os.path.join(SEEDS_DIR_PATH, seed_file)
        seeds.update(get_seeds_from_file(seed_file_path))
    for domain, rank in seeds:
        ranks_dict[domain] = rank
    with open(RANKS_PATH, 'wb') as f:
        json.dump(ranks_dict, f)



# Of the form: (domain, rank)
def get_seeds_from_file(seed_file_path):
    seeds = []
    with open(seed_file_path) as f:
        for line in f:
            # Using a tuple to make it hashable
            seed = tuple(line.strip().split(';'))
            if (seed[1] != ">30M"):
                seed = (seed[0], int(seed[1]))
            else:
                seed = (seed[0], 30 * 10 ** 6)
            seeds.append(seed)
    return set(seeds)


def get_seed_domains(res_seed_files, non_res_seed_files):
    res_seeds = set()
    non_res_seeds = set()
    for seed_file in res_seed_files:
        seed_file_path = os.path.join(SEEDS_DIR_PATH, seed_file)
        res_seeds.update(get_seeds_from_file(seed_file_path))
    for seed_file in non_res_seed_files:
        seed_file_path = os.path.join(SEEDS_DIR_PATH, seed_file)
        non_res_seeds.update(get_seeds_from_file(seed_file_path))
    non_res_seeds = non_res_seeds - res_seeds
    print "Residential seeds: %s, Non-residential seeds: %s" % (len(res_seeds), len(non_res_seeds))
    return res_seeds, non_res_seeds


def main():
    seed_files = os.listdir(SEEDS_DIR_PATH)
    seed_files = set([f for f in seed_files if not f.startswith('.')])
    res_seed_files = set(config.RESIDENTIAL_SEEDS)
    non_res_seed_files = seed_files - res_seed_files
    print res_seed_files, non_res_seed_files
    res_seeds, non_res_seeds = get_seed_domains(res_seed_files, non_res_seed_files)
    res_seeds_list, non_res_seeds_list = list(res_seeds), list(non_res_seeds)
    res_seeds_list.sort(key=lambda x:x[1])
    non_res_seeds_list.sort(key=lambda x:x[1])
    print len(res_seeds_list), len(non_res_seeds_list)
    # write_jobs_list(res_seeds_list, config.RES_JOBS_FILE)
    # write_jobs_list(non_res_seeds_list, config.NONRES_JOBS_FILE)
    write_popularity_ranks(seed_files)


if __name__ == "__main__":
    main()
