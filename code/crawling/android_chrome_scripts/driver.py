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
import time
from selenium import webdriver
# import selenium.webdriver.chrome.service as service
import subprocess
# import signal
from selenium.common.exceptions import ElementNotVisibleException, WebDriverException
import os
import tldextract
import multiprocessing
import subprocess

from process_alerts import process_alerts
from get_clickable_elements import get_clickable_elements, print_elements
# from log_reader import LogReader

DEPTH = 2
REPEAT = 5
MAX_ELEMENTS_CLICK = 3

SHORT_PAUSE = 5
VERY_SHORT_PAUSE = 1
CHROME_DRIVER_PATH = '/home/clicker/malvertising/chrome_driver/chromedriver'
SCREENSHOTS_PARENT_DIR = '/home/clicker/malvertising/chrome_driver/screenshots'

def make_click(element):
    element.click()


class Driver:
    """
    selections: list of length "DEPTH" showing which
    element to interact with at each level
    """
    def __init__(self, url, selections):
        self.url = url
        self.domain = tldextract.extract(url).registered_domain
        self.selections = selections
        capabilities = {
          'chromeOptions': {
            'androidPackage': 'org.chromium.chrome',
          }
        }
        # The below lines don't seem to work. We can start ChromeDriver but after a few calls
        # to the driver an exception is raised. Instead, lets use subprocess
        # chrome_driver = service.Service('/home/clicker/malvertising/chrome_driver/chromedriver')
        # chrome_driver.start()
        # print "Service URL:", chrome_driver.service_url
        self.chrome_driver = subprocess.Popen('exec %s' % (CHROME_DRIVER_PATH,), shell=True) 
        # Wait for Chrome driver server to start
        time.sleep(SHORT_PAUSE)
        self.driver = webdriver.Remote('http://localhost:9515', capabilities)

        # signal.signal(signal.SIGINT, self.signal_handler)
        self.driver.get(url)
        self.setup_screenshots()
        # Sometimes, websites might redirect to a different site. We would like to use the
        # name of this redirected site instead of the original one
        self.url = self.driver.current_url


    def setup_screenshots(self,): 
        self.screenshot_counter = 1
        screenshot_dir = self.domain + "_" + "_".join([str(x) for x in self.selections])
        self.screenshots_path = os.path.join(SCREENSHOTS_PARENT_DIR, screenshot_dir)
        try:
            os.mkdir(self.screenshots_path)
        except OSError: 
            pass

    
    def tear_down(self,):
        print "Tearing down..."
        time.sleep(VERY_SHORT_PAUSE)
        self.driver.close()
        self.driver.quit()
        self.chrome_driver.kill()


    def click_helper(self, element):
        click_process = multiprocessing.Process(target=make_click,
                args=(element,))
        click_process.start()
        time.sleep(1)
        if click_process.is_alive():
            print "click is stuck!"
            self.screenshot_counter = process_alerts(self.driver, self.url, self.screenshot_counter,
                    self.screenshots_path)


    def run(self,):
        click_element_indices = []
        for i, s in enumerate(self.selections):
            elements = get_clickable_elements(self.driver)
            print "Got these:"
            print_elements(elements, self.driver)
            while s < len(elements):
                try:
                    print "Clicking an element"
                    element = elements[s]
                    print_elements([element], self.driver)
                    self.click_helper(element)
                    print "Done clicking an element"
                    print "The URL:", self.driver.current_url
                except (ElementNotVisibleException, WebDriverException):
                    print "Element couldn't be clicked. Discarding this selection", len(elements), s
                    s += 1
                # If try is successful
                else:
                    time.sleep(SHORT_PAUSE)
                    self.screenshot_counter = process_alerts(self.driver, self.url, self.screenshot_counter,
                            self.screenshots_path)
                    # Note that we require the below navigation to only happen once. Even if
                    # this happens only on the first click that will suffice
                    if self.screenshot_counter == 0 and self.driver.current_url == self.url:
                        print "The click didn't event result in a navigation. Discarding this selection..."
                        s += 1
                        continue
                    else:
                        print "Succesful click. Yay!"
                        click_element_indices.append(s)
                        break
            else:
                print "Ran out of elements at depth %s" % (i,)
                return None, i 
        return self.screenshot_counter, click_element_indices 
           


    def signal_handler(self, signal, frame):
        print "User request to tear down"
        self.tear_down() 

            
def get_next_click_at_depth(current_indices, clicks_so_far, depth):
    print "get_next_click_at_depth:", depth, current_indices, clicks_so_far
    if clicks_so_far[depth] < MAX_ELEMENTS_CLICK:
        clicks_so_far[depth] += 1
        current_indices[depth] += 1
        return current_indices
    else:
        if depth == 0:
            return None
        return get_next_click_at_depth(current_indices, clicks_so_far, depth-1)
        

# Arguments:
# current_indices: A list of length DEPTH containing the element indices for the last successful click
# If, while attempting the last click we ran out of elements, then we pass the selection list that was passed 
# to Driver constructor function instead.
# ran_out_depth: If the last click attempt ran out of elements we pass the depth at which that
# happened. Depth starts at 0
# clicks_so_far: A list of length DEPTH listing how many clicks have been made at each depth
# level
# 
# Returns:
# None if we are done clicking all indices
# Click
def get_next_click_element_indices(current_indices, clicks_so_far, ran_out_depth=None):
    if ran_out_depth is not None:
        # If we run out of elements at 0 level, then we are done
        if ran_out_depth == 0:
            return None
        return get_next_click_at_depth(current_indices, clicks_so_far, ran_out_depth)
    else:
        return get_next_click_at_depth(current_indices, clicks_so_far, DEPTH-1)



def main():
    test_url = "http://onlinemoviescinema.com"
    # test_url = "http://einthusan.tv"
    # driver = Driver(test_url, [8,1])
    # screenshots_taken = driver.run()

    # Number of clicks at each level including the currently planned click
    # Note that this will be incremented by get_next_click_element_indices() 
    # even though the click hasn't yet been made
    clicks_so_far = [1] * DEPTH
    current_click_attempt = [0] * DEPTH

    while True:
        print "*" * 100
        print "*" * 100
        driver = Driver(test_url, current_click_attempt)
        print "Attempting click: ", current_click_attempt
        screenshots_taken, current_click_actual = driver.run()
        print "Click done. It returned: ", screenshots_taken, current_click_actual
        if screenshots_taken is None:
            ran_out_depth = current_click_actual
            print "Ran out of depth: %s, cllick attempt: %s" % (ran_out_depth, current_click_attempt)
            next_click_attempt = get_next_click_element_indices(current_click_attempt,
                    clicks_so_far, ran_out_depth=ran_out_depth)
        else:
            next_click_attempt = get_next_click_element_indices(current_click_actual,
                    clicks_so_far)
            print "Click succesful. Attempt: %s, Actual: %s" % (current_click_attempt, current_click_actual)
        # We are done with clicks. We can exit
        if next_click_attempt is None:
            break
        current_click_attempt = next_click_attempt
        driver.tear_down()
        

    # for i in range(0, MAX_ELEMENTS_CLICK): 
        # for j in range(0, MAX_ELEMENTS_CLICK_2):
            # driver = Driver(test_url, [i, j])
            # screenshots_taken = driver.run()
            # if screenshots_taken == 0 and driver.current_url == self.url:
                # driver.tear_down()
    


def test():
    # reader = LogReader()
    test_url = "http://nba-stream.com"
    test_url = "http://nflstream.tv"
    test_url = "http://fmovies.to"
    test_url = "http://megamovies.cc"
    test_url = "http://movie4u.cc"
    test_url = "http://putlocker.live"
    test_url = "http://movies123.in"
    test_url = "http://vexmovies.com"
    test_url = "http://fmovie.io"
    test_url = "http://onlinemoviescinema.com"
    # test_url = "http://einthusan.tv"
    driver = Driver(test_url, [8,1])
    driver.run()
    driver.tear_down()
    # log_lines = reader.get_log_lines()
    # print log_lines

if __name__ ==  "__main__":
    subprocess.call("pkill -f chromedriver", shell=True)
    # test()
    main()
