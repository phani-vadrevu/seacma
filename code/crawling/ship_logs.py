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
import sys
import shutil
import os

import config

"""
Copies the logs to a directory named ~/log_id
Compresses and ships them to config.FILE_SERVER:/data/se_hunter
Deletes the above directory
"""
def compress_logs(log_id, archive_path, milking):
    target_log_path = os.path.join(os.getenv('HOME'), log_id)
    shutil.rmtree(target_log_path, ignore_errors=True)
    os.mkdir(target_log_path)
    jsgraph_logs_path = os.path.join(config.MAIN_LOG_PATH, config.JSGRAPH_LOGS_DIR, log_id)
    shutil.copytree(jsgraph_logs_path, os.path.join(target_log_path, "jsgraph_logs"))
    sehunter_logs_path = os.path.join(config.MAIN_LOG_PATH, config.SEHUNTER_LOGS_DIR, "%s.log" % (log_id,))
    shutil.copy(sehunter_logs_path, os.path.join(target_log_path, "se_hunter.log"))
    screenshots_path = os.path.join(config.MAIN_LOG_PATH, config.SCREENSHOTS_DIR, log_id)
    shutil.copytree(screenshots_path, os.path.join(target_log_path, "screenshots"))
    html_logs_path = os.path.join(config.MAIN_LOG_PATH, config.HTML_LOGS_DIR, log_id)
    shutil.copytree(html_logs_path, os.path.join(target_log_path, "html_logs"))
    downloads_path = os.path.join(config.MAIN_LOG_PATH, config.DOWNLOADS_DIR)
    shutil.copytree(downloads_path, os.path.join(target_log_path, "downloads"))
    if not milking:
        ads_log_path = os.path.join(config.MAIN_LOG_PATH, config.AD_OBJECTS_DIR, "%s.txt" % (log_id,))
        shutil.copy(ads_log_path, os.path.join(target_log_path, "ads.txt"))
    #shutil.rmtree('
    subprocess.call(""" tar -C %s -czvf %s %s""" % 
                            (os.getenv('HOME'), archive_path, log_id), 
                   shell=True) 
    shutil.rmtree(target_log_path, ignore_errors=True)


#TEMP_LOGS_DIR = os.path.join(os.getevn('HOME'), 'temporrary_logs_dir')
def ship_logs(log_id, milking=False, residential=False):
    archive = "logs_%s.tar.gz" % (log_id,)
    archive_path = os.path.join(os.getenv('HOME'), archive)
    compress_logs(log_id, archive_path, milking)
    if milking:
        subprocess.call(""" scp %s %s:/data/se_hunter_milking/ """ % (
                            archive_path, config.FILE_SERVER),
                        shell=True)
    elif residential:
        subprocess.call(""" scp %s %s:/data/se_hunter/ """ % (
                            archive_path, config.FILE_SERVER_RESIDENTIAL),
                        shell=True)
        #subprocess.call("cp %s ~/shipped_logs.tar.gz" % (
                        #archive_path,), shell=True)
        #subprocess.call("echo '%s' > ~/log.txt" % (log_id,), shell=True)
    else:
        subprocess.call(""" scp %s %s:/data/se_hunter/ """ % (
                            archive_path, config.FILE_SERVER),
                        shell=True)
    os.remove(archive_path)


def main():
    log_id = sys.argv[1]
    ship_logs(log_id)


if __name__ == "__main__":
    main()
