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
# driver.get('http://123moviesfree.com')
# url = "http://vmovee.click"
url = "http://123moviesfree.com"
driver.get(url)

time.sleep(SHORT_PAUSE)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(SHORT_PAUSE)
driver.execute_script("window.scrollTo(0,0);")
time.sleep(SHORT_PAUSE)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(SHORT_PAUSE)

log_lines = reader.get_log_lines()
print "Here are the logs so far:", log_lines
print "*" * 100

frames = driver.find_elements_by_tag_name("iframe")
print "Found %s iframes" % (len(frames),)

for frame in frames:
    # This allows the driver to come out of the previous frame.
    driver.switch_to_default_content()
    try:
        print "Src is:", frame.get_attribute("src"), frame.get_attribute("id")
        print "style is:", frame.get_attribute("style")
        driver.switch_to.frame(frame)
    except Exception as e:
        print "Exception in switching to frame", e
        continue
    # elements = driver.find_elements_by_xpath("//*[contains(text(), 'Click OK to continue')]")
    elements = driver.find_elements_by_xpath("//*[contains(text(), 'Watch Movies Online Now') or contains(text(), 'Click OK to continue')]")
    if len(elements) > 0:
        elements = driver.find_elements_by_xpath("//a[text()='OK']")
        if len(elements) > 0:
            print "Number of windows before click:", len(driver.window_handles)
            print "Found a custom alert window. Clicking on OK..."
            elements[0].click()
            print "Processing alerts...."
            time.sleep(SHORT_PAUSE)
            process_alerts(driver, url)
            # print "Number of windows after click:", len(driver.window_handles)
    else:
        print "Did not find an alert window"

driver.save_screenshot('screenshot.png')
time.sleep(SHORT_PAUSE)
time.sleep(SHORT_PAUSE)
log_lines = reader.get_log_lines()
print "Here are the logs so far:", log_lines
print "*" * 100

# try:
    # driver.switch_to.alert.accept()
    # print "Accepted alert!"
# except NoAlertPresentException:
    # print "No alert found"    


# driver.quit()
