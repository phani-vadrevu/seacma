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
import dhash
from PIL import Image


# https://stackoverflow.com/questions/4978235/absolute-urls-omitting-the-protocol-scheme-in-order-to-preserve-the-one-of-the
# Should we also do this? https://webmasters.stackexchange.com/questions/56840/what-is-the-purpose-of-leading-slash-in-html-urls
def process_urls(url, ref_url):
    if url.startswith('//') and ref_url.startswith('http://'):
        url = "http://" + url[2:]
    if url.startswith('//') and ref_url.startswith('https://'):
        url = "https://" + url[2:]
    return url


def get_old_files(dir_path, age):
    log_file_paths = []
    log_files = os.listdir(dir_path)
    log_files = [k for k in log_files if not k.startswith('.')]
    current_time = time.time()
    for log_file in log_files:
        file_path = os.path.join(dir_path, log_file)
        mtime = os.path.getmtime(file_path)
        if (current_time - mtime) > age:
            log_file_paths.append(file_path)
    return log_file_paths


def get_image_hash(image_path):
    image = Image.open(image_path)
    row, col = dhash.dhash_row_col(image)
    hash_str = dhash.format_hex(row, col)
    return hash_str
