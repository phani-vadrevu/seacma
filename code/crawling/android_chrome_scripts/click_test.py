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
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
import time

import subprocess

from log_reader import LogReader
from process_alerts import process_alerts

SHORT_PAUSE = 5
VERY_SHORT_PAUSE = 0.5

reader = LogReader()
capabilities = {
  'chromeOptions': {
    'androidPackage': 'org.chromium.chrome',
  }
}
driver = webdriver.Remote('http://localhost:9515', capabilities)
url = "http://onlinemoviescinema.com"
driver.get(url)

time.sleep(SHORT_PAUSE)

log_lines = reader.get_log_lines()
# print "Here are the logs so far:", log_lines
# print "*" * 100


elem = driver.find_element_by_xpath("//*[@class='col-sm-2 col-xs-6 item responsive-height post video-37427']")
print "Number of windows before click:", len(driver.window_handles)
elem.click()
time.sleep(SHORT_PAUSE)
# print "Number of windows after click:", len(driver.window_handles)
print "Processing alerts...."
process_alerts(driver, url)
print "Done processing..."

time.sleep(SHORT_PAUSE)
log_lines = reader.get_log_lines()
# print "Here are the logs so far:", log_lines
# print "*" * 100

# try:
    # driver.switch_to.alert.accept()
    # print "Accepted alert!"
# except NoAlertPresentException:
    # print "No alert found"    


# driver.quit()
