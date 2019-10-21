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
# url = "https://www.w3schools.com/js/tryit.asp?filename=tryjs_alert"
url = "http://10.0.0.173:8888/alert.html"
driver.get(url)
time.sleep(SHORT_PAUSE)
print "URL:", driver.current_url


# log_lines = reader.get_log_lines()
# print "Here are the logs so far:", log_lines
# print "*" * 100

# driver.switch_to.frame(driver.find_element_by_id("iframeResult"))
# elements = driver.find_elements_by_xpath("//button[contains(text(), 'Try it')]")
element = driver.find_element_by_id("test")
element.click()
print "done clicking"

# print "Number of windows before click:", len(driver.window_handles)
# elements[0].click()
time.sleep(SHORT_PAUSE)
print "current url", driver.current_url
# print "Number of windows after click:", len(driver.window_handles)
print "Processing alerts...."
print "Now trying to switch to alert"
alert = driver.switch_to.alert
print "switched to alert. Text:", alert.text
alert.accept()
print "Accepted modal dialog...."
# process_alerts(driver, url)
