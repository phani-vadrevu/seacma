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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os.path
import time
import sys
''' 
options = webdriver.ChromeOptions()
#options.binary_location = '/usr/bin/google-chrome-unstable'
options.binary_location = '/home/phani/malvertising/chromium/src/out/Default/chrome'
options.add_argument('headless')
driver = webdriver.Chrome(chrome_options=options)
driver.get('https://facebook.com')
driver.get_screenshot_as_file('main-page.png')
'''

options = Options()
#options.binary_location = '/usr/bin/google-chrome-unstable'
options.binary_location = '/home/phani/jsgraph/chromium/src/out/Default/chrome'
options.add_argument( '--headless')
options.add_argument( '--incognito')
options.add_argument('--enable-logging=test1.log')
options.add_argument('--disk-cache-size=1')
options.add_argument('--user-agent="Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)"')
options.add_argument('--user-data-dir=/home/phani/chrome_data')
driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), 
			  chrome_options=options)
driver.get('http://www.whatsmyua.info/')
time.sleep(2)
driver.get_screenshot_as_file('main-page.png')

