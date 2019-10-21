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
import dhash

IMAGE_HASH_SIMILARIY_THRESHOLD = 13
ZERO_HASH = "0" * 32

# Given an image hash string of 128 bits as a hex string
# convert it to an array of '1', '0's of length 128
def convert_image_hash_to_array(hash_str):
    # return [int(x) for x in list(bin(int(hash_str, 16))[2:].zfill(128))]
    return list(bin(int(hash_str, 16))[2:].zfill(128))

def find_different_bits(h1, h2):
    if h1 == h2:
        return 0
    h1i = int(h1, 16)
    h2i = int(h2, 16)
    return dhash.get_num_bits_different(h1i, h2i)

def is_known_similar_hash(candidate, image_hashes):
    for h in image_hashes:
        if find_different_bits(candidate, h) <= IMAGE_HASH_SIMILARIY_THRESHOLD:
            return True
    return False

def are_homogenous_hashes(hashes):
    hashes = hashes.difference([ZERO_HASH]) 
    if len(hashes) <= 1:
        return True
    hash_combines = [x for x in itertools.combinations(hashes, 2)]
    for hc in hash_combines:
        if find_different_bits(*hc) > IMAGE_HASH_SIMILARIY_THRESHOLD:
            return False
    return True

# hashes_1 and hashes_2 should be sets
def are_hashes_similar(hashes_1, hashes_2):
    hashes_1 = hashes_1.difference(hashes_2)
    hashes = set([(h1, h2) for h1 in hashes_1 for h2 in hashes_2])
    for h1, h2 in hashes:
        if find_different_bits(h1, h2) > IMAGE_HASH_SIMILARIY_THRESHOLD:
            return False
    return True
