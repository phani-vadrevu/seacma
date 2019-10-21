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
from PIL import Image, ImageDraw
from math import floor
import time
import os
import hashlib
import shutil
import psutil
import subprocess
import socket
import random

from config import MAIN_LOG_PATH, DOWNLOADS_DIR, RAW_DOWNLOADS_DIR
from config import MIN_CHROME_DEBUG_PORT, MAX_CHROME_DEBUG_PORT

# This can be used for giving unique names to files, directories etc.
# Strangely, time.clock() didn't have micro-second precision.
# Also, we don't want clock to reset for every process. So, time.time() is more apt
def us_timestamp_str():
    return str(int(time.time() * 1000000))

# Round x to nearest multiple of 'base'
def any_round(x, base=50):
    return base * floor(x / base)

def mark_coordinates(coords, fname):
    im = Image.open(fname)
    draw = ImageDraw.Draw(im)
    draw.ellipse((coords[0] - 10, coords[1] - 10,
                coords[0] + 10, coords[1] + 10),
                fill = 'red',
                outline = 'red')
    im.save(fname)

def compute_file_hash(file_path):
    with open(file_path, mode='rb') as f:
        d = hashlib.sha256()
        while True:
            buf = f.read(4096)  # 128 is smaller than the typical filesystem block
            if not buf:
                break
            d.update(buf)
        return d.hexdigest()

# This function will check for new files in the downloads/raw directory.
# If found, it will compute the hash of each of those files
# Rename the hashed files and move them to downloads/ directory.
# Returns: [(hash, file_name), .... ]
def check_for_downloads():
    return_list = []
    raw_dir_path = os.path.join(MAIN_LOG_PATH, RAW_DOWNLOADS_DIR)
    downloaded_files = os.listdir(raw_dir_path)
    downloaded_files = [k for k in downloaded_files if not k.startswith('.')] 
    for fname in downloaded_files:
        file_path = os.path.join(raw_dir_path, fname)
        file_hash = compute_file_hash(file_path)
        return_list.append((fname, file_hash))
        dest_path = os.path.join(MAIN_LOG_PATH, DOWNLOADS_DIR, "%s" % (file_hash,))
        shutil.move(file_path, dest_path)
    return return_list

# Kill all processes whose name matches name and whose age is > age seconds.
def kill_old_processes(name, age):
    for p in psutil.process_iter():
        try:
            name_ = p.name()
        except Exception as e:
            continue
        process_age = (time.time() - p.create_time())
        if name in name_ and process_age > age :
            print "Found an old process with age: %s, pid: %s, name: %s" % (process_age, p.pid, name_)
            subprocess.call("kill %s >/dev/null 2>&1" % (p.pid,), shell=True)
            # p.kill()


# Kill all process with a matching name and a
# matching string in the commandline arguments.
def kill_processes_by_cmdline(name, cmdline_str):
    for p in psutil.process_iter():
        try:
            name_ = p.name()
        except Exception as e:
            continue
        if name in name_ and any(cmdline_str in arg for arg in p.cmdline()):
            subprocess.call("kill %s >/dev/null 2>&1" % (p.pid,), shell=True)
            # p.kill()


# Deletes all files in a directory that end with a specific string and whose age is > age seconds
def delete_old_files(dir_path, name, age):
    assert name
    current_time = time.time()
    files = os.listdir(dir_path)
    for f in files:
        if not f.endswith(name):
            continue
        fpath = os.path.join(dir_path, f)
        if (current_time - os.path.getmtime(fpath)) > age:
            os.remove(fpath)


def is_port_free(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    status = False
    try:
        s.bind(("127.0.0.1", port))
    except socket.error as e:
        pass
    else:
        status = True
    s.close()
    return status

def fetch_random_free_port():
    while True:
        candidate_port = random.randint(MIN_CHROME_DEBUG_PORT, MAX_CHROME_DEBUG_PORT)
        if is_port_free(candidate_port):
            return candidate_port
