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
"""
Process alerts processes any modal dialogs or 3rd party windows
that might pop-up during browsing
"""
from selenium.common.exceptions import NoAlertPresentException, UnexpectedAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchWindowException, WebDriverException
import tldextract
import logging
import time
import subprocess

import multiprocessing
logging.basicConfig()

VERY_SHORT_TIME = 1
MODAL_DIALOG_WAIT_TIME = 5


def process_alerts(driver, url, screenshot_counter, screenshots_path_string):
    processor = AlertProcessor(driver, screenshot_counter, screenshots_path_string)
    home_domain = tldextract.extract(url).registered_domain
    try:
        print "process_alerts: Window handles", driver.window_handles
    # Sometimes, all the windows get closed. Then the above might give an error
    except WebDriverException:
        return processor.screenshot_counter, processor.ad_urls_dict
    alert_count = 0
    # print "These are all the window handles:", driver.window_handles
    # print "Switched to another handle"
    for handle in driver.window_handles:
        try:
            if processor.accept_modal_dialog():
                alert_count += 1
            driver.switch_to.window(handle)
            print "Switched to this window handle..... %s" % (driver.current_url,)
            if tldextract.extract(driver.current_url).registered_domain != home_domain:
                alert_count += 1
                processor.handle_ad_tab()
        except UnexpectedAlertPresentException: 
            print "Found an unexpected alert....."
            processor.accept_modal_dialog()
            alert_count += 1
            # Accepting a modal dialog might result in a switch to a new window.
            continue
            
    print "Done with window handles...."
    # Keep processing until no more new alerts are being generated.
    # Sometimes, closing of an ad or accepting a dialog might generate new alerts
    if alert_count > 0:
        print "Processing alerts again..."
        processor.screenshot_counter, ad_urls_subset = process_alerts(driver, url, processor.screenshot_counter,
                processor.screenshots_path_string)
        processor.ad_urls_dict.update(ad_urls_subset)
    print "End of process alerts..."
    return processor.screenshot_counter, processor.ad_urls_dict




def print_url(driver):
    print "Current URL:", driver.current_url


class  AlertProcessor:
    def __init__(self, driver, screenshot_counter, screenshots_path_string):
        self.driver = driver
        self.screenshot_counter = screenshot_counter
        self.screenshots_path_string = screenshots_path_string
        self.ad_urls_dict = {}


    def handle_ad_tab(self,):
        print "Handling ad tab. URL:", self.driver.current_url
        # domain = tldextract.extract(self.driver.current_url).registered_domain
        screenshot_file = '%s_%s.png' % (self.screenshots_path_string, self.screenshot_counter)
        self.ad_urls_dict[screenshot_file] = self.driver.current_url
        self.driver.save_screenshot(screenshot_file)
        print "Screenshot saved: %s URL: %s" % (screenshot_file, self.driver.current_url)
        self.screenshot_counter += 1
        print "Closing ad tab", self.driver.current_url, self.driver.current_window_handle
        self.driver.close()
        time.sleep(1)


    def accept_modal_dialog(self,):
        try:
            print "accept_modal_dialog(): Current URL:", self.driver.current_url
            print "Current window handle:", self.driver.current_window_handle
            WebDriverWait(self.driver, 2).until(EC.alert_is_present(),
               'Timed out waiting for alert popup to appear.')
            print "Now trying to switch to alert"
            alert = self.driver.switch_to.alert
            # print "switched to alert. Text:", alert.text
            
            screenshot_file = '%s_%s.png' % (self.screenshots_path_string, self.screenshot_counter)
            self.ad_urls_dict[screenshot_file] = self.driver.current_url
            self.driver.save_screenshot(screenshot_file)
            print "Screenshot saved: %s URL: %s" % (screenshot_file, self.driver.current_url)
            self.screenshot_counter += 1
            alert.accept()
            print "Accepted modal dialog...."
            return  True
        except NoAlertPresentException:
            print "No alert found!"
        except TimeoutException:
            print "Time out waiting for alert"
        #TODO: Not sure why this is happening
        except NoSuchWindowException:
            print "No such window expection"
        return False
