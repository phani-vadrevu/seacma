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
from selenium.common.exceptions import ElementNotVisibleException, WebDriverException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
import os
import tldextract

from process_alerts import process_alerts
from get_clickable_elements import get_clickable_elements
from get_clickable_elements import print_elements
# from log_reader import LogReader
import file_url_dict
from input_urls import input_urls

from PIL import Image, ImageDraw

DEPTH = 2
# REPEAT = 8
REPEAT = 1
MAX_ELEMENTS_CLICK = 5

SHORT_PAUSE = 5
VERY_SHORT_PAUSE = 1
#SCREENSHOTS_PARENT_DIR = '/home/phani/malvertising/selenium/screenshots'
SCREENSHOTS_PARENT_DIR = '/home/phani/se-hunter/scratch'

# Some <a> tags have larger image elements as children.
# This function accounts for that case.
def get_largest_element(elem):
    child_elements = elem.find_elements_by_css_selector("*")
    largest_elem = (elem, elem.size['width'] * elem.size['height'])
    for c in child_elements:
        area = c.size['width'] * c.size['height']
        if area > largest_elem[1]:
            largest_elem = (c, area)
    return largest_elem[0]


def mark_element(elem, fname):
    click_coords = (elem.location['x'] + (elem.size['width'] / 2.0), 
            elem.location['y'] + (elem.size['height'] / 2.0))

    le = get_largest_element(elem)

    im = Image.open(fname)
    draw = ImageDraw.Draw(im)
    draw.rectangle([(le.location['x'],
                     le.location['y']),
                    (le.location['x'] + le.size['width'],
                     le.location['y'] + le.size['height'])],
                   fill=None,
                   outline='blue')
    draw.ellipse((click_coords[0] - 10, click_coords[1] - 10, 
                click_coords[0] + 10, click_coords[1] + 10),
                fill = 'red',
                outline = 'red')
    im.save(fname)


class Driver:
    """
    selections: list of length "DEPTH" showing which
    element to interact with at each level
    """
    def __init__(self, url, selections, attempt_number=0):
        self.url = url
        self.domain = tldextract.extract(url).registered_domain
        self.selections = selections
        self.attempt_number = attempt_number

        time.sleep(SHORT_PAUSE)

        #self.driver = webdriver.Firefox()

        options = Options()
        # options.binary_location = '/usr/bin/google-chrome-unstable'
        options.binary_location = '/home/phani/jsgraph/chromium/src/out/Default/chrome'
        #options.add_argument('--headless')
        options.add_argument('--incognito')
        options.add_argument('--enable-logging=test1.log')
        options.add_argument('--disk-cache-size=1')
        #options.add_argument('--user-agent="Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)"')
        options.add_argument('--user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36"')
        options.add_argument('--user-data-dir=/home/phani/chrome_data')
        self.driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"),
                                  chrome_options=options)

        # signal.signal(signal.SIGINT, self.signal_handler)
        self.driver.get(url)
        time.sleep(2 * SHORT_PAUSE)

        self.setup_screenshots()
        # Sometimes, websites might redirect to a different site. We would like to use the
        # name of this redirected site instead of the original one
        self.url = self.driver.current_url


    def setup_screenshots(self,): 
        self.screenshot_counter = 1
        # screenshot_dir = self.domain + "_" + "_".join([str(x) for x in self.selections])
        # screenshot_dir = self.domain + "_" + "_".join([str(x) for x in self.selections])
        self.screenshots_dir = os.path.join(SCREENSHOTS_PARENT_DIR, self.domain)
        try:
            os.mkdir(self.screenshots_dir)
        except OSError: 
            pass
        # Appending screenshot_number to the below string should give a valid final file path.
        # eg: + "_4.png"
        self.screenshots_path_string = os.path.join(self.screenshots_dir, self.domain + "_" + "_".join([str(x) for x in
            self.selections]) + "_a" + str(self.attempt_number))

    
    def tear_down(self,):
        try:
            print "Tearing down..."
            time.sleep(VERY_SHORT_PAUSE)
            self.driver.close()
        except:
            print "Excepting in tearing down..."
            return
        # self.driver.quit()


    def click_next_element(self, elements, i, s):
        print "called click_next_element. step number(i, begin:0):%s, selection at that step(s):%s" % (i, s)
        temp_ss_fname = 'temp_ss/ss_%s_%s.png' % (i, s)
        self.driver.save_screenshot(temp_ss_fname)
        refetch = False

        while s < len(elements):
            try:
                # print "Clicking an element"
                element = elements[s]
                print "Clicking an elem of index and size: ", s, element.size
                # print_elements([element], self.driver)
                mark_element(element, temp_ss_fname)
                old_url = self.driver.current_url
                element.click()
                print "Done clicking an element. URL:", (self.driver.current_url, "Dimensions:",
                    element.size['width'], element.size['height'])

            except StaleElementReferenceException as e:
                if refetch:
                    s += 1
                    refetch = False
                    continue
                print "Element was stale. Fetching elements again and trying.", len(elements), s, e
                elements = get_clickable_elements(self.driver)
                refetch = True

            except (WebDriverException, StaleElementReferenceException) as e:
                print "Element couldn't be clicked. Discarding this selection", len(elements), s, e
                s += 1

            # If try is successful
            else:
                time.sleep(2 * SHORT_PAUSE)
                self.screenshot_counter, ad_urls_subset = process_alerts(self.driver, self.url, self.screenshot_counter,
                        self.screenshots_path_string)
                self.ad_urls_dict.update(ad_urls_subset)
                # Either a screenshot should have been taken or the there should be a change in
                # the url
                if self.screenshot_counter == 1 and self.driver.current_url == old_url:
                    print "The click didn't event result in a navigation. Discarding this selection..."
                    s += 1
                    continue
                else:
                    #print "Successful click. Yay!", self.screenshot_counter, self.driver.current_url, old_url, temp_ss_fname
                    print "Successful click. Yay!", self.screenshot_counter, old_url, temp_ss_fname

                    self.click_element_indices.append(s)
                    break
        else:
            print "Ran out of elements at depth %s" % (i,)
            return False 
        return True 

    def run(self,):
        print "In run()"
        self.click_element_indices = []
        self.ad_urls_dict = {}
        for i, s in enumerate(self.selections):
            elements = get_clickable_elements(self.driver)
            print "In Driver.run(): Got these elements to try out:"
            #print_elements(elements, self.driver)
            try:
                return_stuff = self.click_next_element(elements, i, s)
                if not return_stuff:
                    return None, {}, i 
            except StaleElementReferenceException:
                print "Exception: stale element reference exception!"
                # If there's an exception, we just say that there's a problem at
                # the lowest depth?
                return None, self.ad_urls_dict, (len(self.selections) - 1)
                #return self.screenshot_counter, self.ad_urls_dict, self.selections
        return self.screenshot_counter, self.ad_urls_dict, self.click_element_indices 


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


"""
Return the selection that produces ad-like tabs
"""
def find_elements_to_click(url):
    # Number of clicks at each level including the currently planned click
    # Note that this will be incremented by get_next_click_element_indices() 
    # even though the click hasn't yet been made
    clicks_so_far = [1] * DEPTH
    current_click_attempt = [0] * DEPTH
    #current_click_attempt = [0, 12]

    while True:
        print "*" * 100
        print "*" * 100
        driver = Driver(url, current_click_attempt, attempt_number=0)
        print "Attempting click: ", current_click_attempt
        screenshot_counter, url_dict, current_click_actual = driver.run()
        print "Click done. It returned: ", screenshot_counter, current_click_actual
        print "Ads were seen from the following URLS:", url_dict.values()
        if screenshot_counter is not None:
            screenshots_taken = screenshot_counter - 1
            if screenshots_taken > 0:
                print "Found clickable elements resulting in ads!", current_click_actual
                driver.tear_down()
                return current_click_actual, url_dict

        if screenshot_counter is None:
            ran_out_depth = current_click_actual
            print "Ran out of depth: %s, cllick attempt: %s" % (ran_out_depth, current_click_attempt)
            next_click_attempt = get_next_click_element_indices(current_click_attempt,
                    clicks_so_far, ran_out_depth=ran_out_depth)
        else:
            next_click_attempt = get_next_click_element_indices(current_click_actual,
                    clicks_so_far)
            print "Click successful. Attempt: %s, Actual: %s" % (current_click_attempt, current_click_actual)
        # We are done with clicks. We can exit
        if next_click_attempt is None:
            driver.tear_down()
            return None, None
        current_click_attempt = next_click_attempt
        driver.tear_down()


def experiment(url):
    click_elements, url_dict = find_elements_to_click(url)
    if click_elements is None:
        print  "Couldn't find any clicks that open ad-like tabs for %s" % (url,)
        return
    print "Found that this selection produces ad-like tabs:", click_elements
    """
    for i in range(1, REPEAT):
        driver = Driver(url, selections=click_elements, attempt_number=i) 
        screenshot_counter, url_dict_subset, current_click_actual = driver.run()
        if screenshot_counter is not None:
            url_dict.update(url_dict_subset)
        time.sleep(10)
        driver.tear_down()
        file_url_dict.update(url_dict)
    """


def main():
    print "# of input urls: %s" % (len(input_urls))
    for url in input_urls:
        experiment(url)


def test():
    # reader = LogReader()
    # test_url = "http://nba-stream.com"
    # test_url = "http://nflstream.tv"
    # test_url = "http://fmovies.to"
    # test_url = "http://movie4u.cc"
    # test_url = "http://putlocker.live"
    # test_url = "http://movies123.in"
    # test_url = "http://onlinemoviescinema.com"
    # test_url = "http://fmovie.io"
    # test_url = "http://putlocker.live"
    # test_url = "http://megamovies.cc"
    # test_url = "http://vexmovies.com"
    test_url = "http://dimensionpeliculas.net"
    experiment(test_url)
    

if __name__ ==  "__main__":
    # main()
    test()
    # experiment()
