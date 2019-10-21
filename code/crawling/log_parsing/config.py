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
HOME = os.getenv('HOME')
CHROME_BINARY_PATH = os.path.join (HOME, "chrome_binary/")  # The path of the binary
MAIN_LOG_PATH = os.path.join(HOME, "se-hunter/logs/")
SCREENSHOTS_DIR = "screenshots"
SEHUNTER_LOGS_DIR = "sehunter_logs"
JSGRAPH_LOGS_DIR = "jsgraph_logs"
CHROMEDRIVER_LOGS_DIR = "chromedriver_logs"
CHROMEDATA_DIR = "chrome_data"
DOWNLOADS_DIR = "downloads"
RAW_DOWNLOADS_DIR = "downloads/raw"
HTML_LOGS_DIR = "html_logs"
AD_OBJECTS_DIR = "ads"
AD_CHAIN_PROCESS_LOG = 'ad_chain_process.log'

FILE_SERVER = "uname@server"
FILE_SERVER_RESIDENTIAL = "uname@server"

RESIDENTIAL_SEEDS = ['apu_php.txt']
RES_JOBS_FILE = "residential_list.txt"
NONRES_JOBS_FILE = "non_residential_list.txt"

OBSOLETE_PROCESS_AGE = 100  # Kill orphan processes older than x seconds.

MIN_CHROME_DEBUG_PORT = 10000
MAX_CHROME_DEBUG_PORT = 40000

USER_AGENTS = {
    # Emulate a 1920x1080 (1785,993) desktop; Other variant: 1440x900 (1375,738-win_size_cmd)
    "chrome_mac": {
        "user_agent": ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_0) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'),
        "window_size_cmd": (1785, 993),
        "device_size": (1920, 1080),
        "device_scale_factor": 1,
        "mobile": False,
    },

    "ie_win": {
        "user_agent": ('Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)'),
        "window_size_cmd": (1785, 993),
        "device_size": (1920, 1080),
        "device_scale_factor": 1,
        "mobile": False,

    },

    "edge_win": {
        "user_agent": ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'),
        "window_size_cmd": (1785, 993),
        "device_size": (1920, 1080),
        "device_scale_factor": 1,
        "mobile": False,
    },

    # Samsung Galaxy S9 Plus; personal test: win size: (412, 718); 1440 * 2960 is the screen size;
    # win size From: https://mediag.com/news/popular-screen-resolutions-designing-for-all/ (360, 740)
    # Also here: https://www.mydevice.io/#compare-devices
    "chrome_android": {
        "user_agent": ('Mozilla/5.0 (Linux; Android 8.0.0; SM-G965F Build/R16NW) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/65.0.3325.109 Mobile Safari/537.36'),
        "window_size_cmd": (360, 740),
        #"device_size": (1440, 2960),
        "device_size": (360, 740),
        "device_scale_factor": 4,
        "mobile": True,

    }

}
