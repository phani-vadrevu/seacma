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
import time

capabilities = {
  'chromeOptions': {
    'androidPackage': 'org.chromium.chrome',
  }
}
driver = webdriver.Remote('http://localhost:9515', capabilities)
driver.get('http://123movies.com')
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(15)
driver.quit()
