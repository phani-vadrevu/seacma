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
#TODO: Is there a way we can include the "thumb" class divs in this?
# sockshare.net/watch/qvoeyOGl-guardians-of-the-galaxy-vol-2.html
#TODO: How about the <a> link here:
# http://cafemovie.me/movie/deadpool-aOwMznWN
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from operator import attrgetter
from PIL import Image, ImageDraw
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
from collections import defaultdict

import cProfile

import utils

import ipdb


SHORT_PAUSE = 5


def print_elements(elems, driver):
    for elem in elems:
        attrs = driver.execute_script('var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;', elem)
        # print "Name: %s, ID: %s, Location: %s, Size: %s" % (elem.tag_name, elem.get_attribute('id'), elem.location, elem.size)
        print "Name: %s, ID: %s, attrs: %s, Location: %s, Size: %s" % (elem.tag_name, elem.get_attribute('id'), attrs, elem.location, elem.size)
        # elem.click()


def element_coords(elem):
    loc = elem.location
    size = elem.size
    return (loc['x'] + (size['width'] / 2.0),
                        loc['y'] + (size['height'] / 2.0))


"""
# Some <a> tags have larger image elements as children.
# This function accounts for that case.
def replace_with_larger_children(elems):
    child_elements = elem.find_elements_by_css_selector("*")
    largest_area = 0
    if len(child_elements) > 0:
        largest_area = max(x.size['width'] * x.size['height'] for x in child_elements)
    largest_area = max(largest_area, elem.size['width'] * elem.size['height'])
"""


# Tries to retain return elements with unique sizes, and unique mid-points
# On some pages there are very close click-points that don't do anything different.
# Hence we try to filter out elements that have spatially close click points.
def get_unique_elements(elems):
    R = 100  # Coarseness in pixels for determining unique click points
    MAX_SAME_COORD = 2 # Don't allow more than 2 elements on same x or y coordinates.
    ret_elems = []
    prev_elems = set()
    prev_mid_points = set()
    prev_x = defaultdict(int)
    prev_y = defaultdict(int)
    for elem in elems:
        try:
            if (elem.size['width'], elem.size['height']) in prev_elems:
                continue
            coords = element_coords(elem)
            mp_rounded = (utils.any_round(coords[0], R), utils.any_round(coords[1], R))
            if mp_rounded in prev_mid_points:
                continue
            # prev_x doesn't make sense at all in pages where all different kinds of elements are vertically aligned
            # for example: https://onlinetviz.com/american-crime-story/2/1
            if (prev_y[elem.location['y']] >= MAX_SAME_COORD):
                continue
        except StaleElementReferenceException as e:
            continue
        #print "debug, unique size elems", elem.size['width'], elem.size['height']
        ret_elems.append(elem)
        prev_elems.add((elem.size['width'], elem.size['height']))
        prev_mid_points.add(mp_rounded)
        prev_x[elem.location['x']] += 1
        prev_y[elem.location['y']] += 1
    return ret_elems


def element_area(elem):
    return elem.size['width'] * elem.size['height']

# Given a list of elements,
# Sort the elements by area,
def filter_elements(elems, window_size):
    # Removing elements that donot exist completely inside the visible area.
    #TODO: Should we remove elements from the other two sides as well?
    # TODO: This is a quick fix, we should instead make sure this Exception doesn't get
    # triggered
    # elems = [e for e in elems if e.location['x'] > 0 and e.location['y'] > 0]
    #print "filter_elements()"
    elems2 = []
    for i, e in enumerate(elems):
        #if i % 50 == 0:
        #    print "%s done so far" % (i,)
        try:
            if check_elem_view_port(e, window_size):
                elems2.append(e)
        except StaleElementReferenceException as e:
            print "Stale element exception, skipping an element"
            continue
    print "filter_elements(): Removed elements outside the viewport done"
    elems = elems2
    elems = get_unique_elements(elems)
    print "filter_elements(): Retained only elements of unique size"

    elems = sorted(elems, reverse=True, key=element_area)
    elems = elems[:20]
    print "filter_elements(): Sorted elements by size and got the first few ones"
    # Below doesn't work on Android :(
    # print "Window rect: ", driver.get_window_rect()
    return elems


# Check if element is within vieport or not
def check_elem_view_port(e, window_size):
    # Its OK if part of the element is outside the view port.
    # We only need to make sure the the mid point of element is in the
    # view port so that we can click it.
    elem_coords = element_coords(e)
    return (elem_coords[0] < window_size['width'] and
        elem_coords[1] < window_size['height'])

# TODO: A large portion of the time is used ip getting the size and location of
# individual elements. So, we should instead use JS to get the size and location
# along with the elements. This will do a good speed up of the entire script
# Returns a list of coordinates for clickable elements in the current page.
def get_clickable_elements(driver):
    #return [(275.0, 350.0)]
    #TODO: also find iframe elements and click on them
    # Selecting only divs/tds that have no other divs/tds as children. 
    # Otherwise, the bigger divs that contain more than one clickable elements
    # will get selected.
    # divs = driver.find_elements_by_tag_name('div')
    print "get_clickable_elements()"
    divs = driver.find_elements_by_xpath('//div[not(descendant::div) and not(descendant::td)]')
    tds = driver.find_elements_by_xpath('//td[not(descendant::div) and not(descendant::td)]')
    iframes = driver.find_elements_by_tag_name('iframe')
    a_elems = driver.find_elements_by_tag_name('a')
    img_elems = driver.find_elements_by_tag_name('img')
    elems = divs + tds + a_elems + iframes + img_elems
    #ipdb.set_trace()
    print "found %s divs, %s tds, %s iframes, %s as and %s imgs" % (len(divs), len(tds), len(iframes), len(a_elems), len(img_elems))

    temp_ss_fname = 'temp_ss/all_elements.png'
    driver.save_screenshot(temp_ss_fname)

    print "get_clickable_elements(): found all elements, %s" % (len(elems),)
    window_size = driver.get_window_size()
    print "window_size:", window_size
    elems = filter_elements(elems, window_size)
    print "done filtering! %s " % (len(elems),)

    #ipdb.set_trace()

    """
    for elem in elems[:10]:
        print "Element area: %s" % (element_area(elem))
    """
    #ipdb.set_trace()

    """
    im = Image.open(temp_ss_fname)
    draw = ImageDraw.Draw(im)
    for le in elems:
        draw.rectangle([(le.location['x'],
                         le.location['y']),
                        (le.location['x'] + le.size['width'],
                         le.location['y'] + le.size['height'])],
                       fill=None,
                       outline='blue')
        click_coords = (le.location['x'] + (le.size['width'] / 2.0),
                        le.location['y'] + (le.size['height'] / 2.0))
        draw.ellipse((click_coords[0] - 10, click_coords[1] - 10,
                      click_coords[0] + 10, click_coords[1] + 10),
                     fill='red',
                     outline='red')
    im.save(temp_ss_fname)
    """

    #raw_input("Check it!")
    elem_coords = []
    for elem in elems:
        click_coords = element_coords(elem)
        print click_coords, elem.tag_name
        elem_coords.append(click_coords)
    return elem_coords


if __name__ == "__main__":
    options = Options()
    # options.binary_location = '/usr/bin/google-chrome-unstable'
    options.binary_location = '/home/phani/jsgraph/chromium/src/out/Default/chrome'
    options.add_argument('--headless')
    options.add_argument('--incognito')
    options.add_argument('--disable-popup-blocking')
    # Note: "start-maximized has no effect in headless mode which by default is in 800x600.
    # We need to explicitly set the window size that we would like.
    options.add_argument('--start-maximized')
    # TODO: Automate the setting of the coordinates below for headless mode.
    options.add_argument('--window-size=1375,738')
    options.add_argument('--enable-logging=test1.log')
    options.add_argument('--disk-cache-size=1')
    # Don't use extra quotes around user-agent here.. this will trip Cloud Fare's Browser Integrity Check
    # Make sure there are no quotes around the UA by checking here:
    # https://www.whatismybrowser.com/detect/what-http-headers-is-my-browser-sending
    options.add_argument('--user-agent=Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)')
    # options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36')
    options.add_argument('--user-data-dir=/home/phani/chrome_data')

    capabilities = DesiredCapabilities.CHROME
    # This allows driver.get() call to return immediately. If not, it wait until the page loads
    # which can be a problem on certain pages. See comments on stop_page_load()
    capabilities['pageLoadStrategy'] = "none"

    t0 = time.time()

    driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"),
                                   chrome_options=options,
                                   desired_capabilities=capabilities)
    # driver.get('http://123moviesfree.com')
    test_url = "https://www1.123movies.cafe/123movies/"
    #test_url = "https://www.nytimes.com"
    file_path = "/home/phani/scratch/clickable_elems_old.png"
    driver.get(test_url)
    # driver.get('http://sockshare.net/watch/qvoeyOGl-guardians-of-the-galaxy-vol-2.html')
    # driver.get('http://sockshare.net/watch/qvoeyOGl-guardians-of-the-galaxy-vol-2.html')
    # driver.get('http://cafemovie.me/movie/deadpool-aOwMznWN')
    time.sleep(4 * SHORT_PAUSE)
    driver.save_screenshot(file_path)
    print "Time @ setup:", time.time() - t0



    elems = get_clickable_elements(driver)
    print "Time @ getting elems:", time.time() - t0

    for elem in elems[:5]:
        print "Element: %s" % (elem,)
        utils.mark_coordinates(elem, file_path)
    #utils.mark_coordinates((680,680), file_path)

    #print_elements(elems, driver)
