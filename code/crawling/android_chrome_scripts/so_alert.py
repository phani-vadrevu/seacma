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

SHORT_PAUSE = 5
capabilities = {
  'chromeOptions': {
    'androidPackage': 'org.chromium.chrome',
  }
}
driver = webdriver.Remote('http://localhost:9515', capabilities)
url = "http://10.0.0.173:8888/alert.html"
driver.get(url)
time.sleep(SHORT_PAUSE)


element = driver.find_element_by_id("test")
element.click()
print "done clicking"

# Usually prints: "[u'CDwindow-0', u'CDwindow-1']" 
print driver.window_handles
time.sleep(SHORT_PAUSE)
driver.switch_to.window(driver.window_handles[1])

# Selenium is unresponsive after this and 
# never prints the below line
print "current url:", driver.current_url
alert = driver.switch_to.alert
print "switched to alert. Text:", alert.text
alert.accept()
print "Accepted modal dialog...."
