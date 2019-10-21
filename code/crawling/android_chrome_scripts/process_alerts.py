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


def process_alerts(driver, url, screenshot_counter, screenshots_path):
    processor = AlertProcessor(driver, screenshot_counter, screenshots_path)
    processor.check_and_handle_unresponsiveness()
    home_domain = tldextract.extract(url).registered_domain
    try:
        print "process_alerts: Window handles", driver.window_handles
    # Sometimes, all the windows get closed. Then the above might give an error
    except WebDriverException:
        return processor.screenshot_counter
    alert_count = 0
    # print "These are all the window handles:", driver.window_handles
    # print "Switched to another handle"
    for handle in driver.window_handles:
        try:
            if processor.accept_modal_dialog():
                alert_count += 1
            driver.switch_to.window(handle)
            processor.check_and_handle_unresponsiveness()
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
        processor.screenshot_counter = process_alerts(driver, url, processor.screenshot_counter,
                processor.screenshots_path)
    print "End of process alerts..."
    return processor.screenshot_counter


# Since this can fail sometimes due to a chromedriver bug, we will have this called
# in a separate process and will kill the process if its unresponsive
def accept_modal_dialog_webdriver(driver, screenshot_counter, screenshots_path, return_queue):
    try:
        print "Current URL:", driver.current_url
        print "Current window handle:", driver.current_window_handle
        WebDriverWait(driver, 2).until(EC.alert_is_present(),
           'Timed out waiting for alert popup to appear.')
        print "Now trying to switch to alert"
        alert = driver.switch_to.alert
        # print "switched to alert. Text:", alert.text
        
        driver.save_screenshot('%s/%s.png' % (screenshots_path, screenshot_counter))
        print "Screenshot saved", screenshots_path, screenshot_counter
        alert.accept()
        print "Accepted modal dialog...."
        return_queue.put("Found a dialog")
    except NoAlertPresentException:
        print "No alert found!"
    except TimeoutException:
        print "Time out waiting for alert"
    #TODO: Not sure why this is happening
    except NoSuchWindowException:
        print "No such window expection"


def print_url(driver):
    print "Current URL:", driver.current_url


class  AlertProcessor:

    def __init__(self, driver, screenshot_counter, screenshots_path):
        self.driver = driver
        self.screenshot_counter = screenshot_counter
        self.screenshots_path = screenshots_path


    def handle_ad_tab(self,):
        print "Handling ad tab....."
        domain = tldextract.extract(self.driver.current_url).registered_domain
        self.driver.save_screenshot('%s/%s.png' % (self.screenshots_path,
            self.screenshot_counter))
        print "Screenshot saved", self.screenshots_path, self.screenshot_counter
        self.screenshot_counter += 1
        print "Closing ad tab", self.driver.current_url, self.driver.current_window_handle
        self.driver.close()
        time.sleep(1)


    def accept_modal_dialog(self,):
        print "In accept modal dialog..."
        return_queue = multiprocessing.Queue()
        modal_process = multiprocessing.Process(target=accept_modal_dialog_webdriver,
                args=(self.driver, self.screenshot_counter, self.screenshots_path, return_queue))
        modal_process.start()
        time.sleep(MODAL_DIALOG_WAIT_TIME)
        if modal_process.is_alive():
            print "accept_modal_dialog() is unresponsive. Killing it..."
            modal_process.terminate()
            self.take_system_screenshot()
            self.accept_modal_dialog_crude()
            return True
        else:
            if not return_queue.empty():
                self.screenshot_counter += 1
            return not return_queue.empty()


    def take_system_screenshot(self,):
        subprocess.call("adb shell screencap -p /sdcard/screenshot.png", shell=True)
        subprocess.call("adb pull /sdcard/screenshot.png %s/%s.png" % (self.screenshots_path,
            self.screenshot_counter), shell=True) 
        print "Screenshot saved", self.screenshots_path, self.screenshot_counter
        self.screenshot_counter += 1


    def accept_modal_dialog_crude(self, tab_presses=2):
        print "****Trying to deal with modal dialog crudely..."
        for i in range(tab_presses):
            subprocess.call("adb shell input keyevent 61", shell=True)
        subprocess.call("adb shell input keyevent 66", shell=True)


    def check_unresponsiveness(self,):
        process = multiprocessing.Process(target=print_url, args=(self.driver,))
        process.start()
        time.sleep(VERY_SHORT_TIME)
        if process.is_alive():
            print "Current window is unresponsive."
            process.terminate()
            return True
        else:
            return False


    def check_and_handle_unresponsiveness(self,):
        for i in range(2, 4):
            if self.check_unresponsiveness():
                print "Taking system based screenshot"
                self.take_system_screenshot()
                self.accept_modal_dialog_crude(tab_presses=i)
            else:
                break
        if self.check_unresponsiveness():
            print "******* Window still unresponsive *******"
            time.sleep(5)
            print "Calling check_and_handle_unresponsiveness() again"
            self.check_and_handle_unresponsiveness()
        else:
            print "Yay! Window is now responsive"
