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

import time
SHORT_PAUSE = 5
#TODO: Try to automate this if possible
# In potrait mode, PixelC
# From: https://mydevice.io
DEVICE_HEIGHT = 1280 
DEVICE_WIDTH = 900


def print_elements(elems, driver):
    for elem in elems:
        attrs = driver.execute_script('var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;', elem)
        # print "Name: %s, ID: %s, Location: %s, Size: %s" % (elem.tag_name, elem.get_attribute('id'), elem.location, elem.size)
        print "Name: %s, ID: %s, attrs: %s, Location: %s, Size: %s" % (elem.tag_name, elem.get_attribute('id'), attrs, elem.location, elem.size)
        # elem.click()


# Tries to retain return elements with unique sizes
def get_unique_sized_elements(elems):
    ret_elems = []
    prev = None
    for elem in elems:
        if not prev or (prev and (prev != (elem.size['width'], elem.size['height']))):
            ret_elems.append(elem)
        prev = (elem.size['width'], elem.size['height'])
    return ret_elems


# Given a list of elements,
# Sort the elements by area,   
def filter_elements(elems):
    # Removing elements that donot exist completely inside the visible area.
    #TODO: Should we remove elements from the other two sides as well?
    # TODO: This is a quick fix, we should instead make sure this Exception doesn't get
    # triggered
    # elems = [e for e in elems if e.location['x'] > 0 and e.location['y'] > 0]
    print "filter_elements()"
    elems2 = []
    for e in elems:
        try:
            # This check takes a long time. Not sure how to reduce this time
            if (e.location['x'] > 0 and e.location['y'] > 0 and (e.location['x'] +
            e.size['width']) < DEVICE_WIDTH and (e.location['y'] + 
            e.size['height']) < DEVICE_HEIGHT):
                elems2.append(e)
        except StaleElementReferenceException as e:
            print "Stale element exception, skipping an element"
            continue
    print "filter_elements(): Removed elements outside the viewport"
    elems = elems2
    elems = get_unique_sized_elements(elems) 
    print "filter_elements(): Retained only elements of unique size"

    # elems.sort(reverse=True, key=lambda x:(attrgetter('width')*attrgetter('height')))
    elems = sorted(elems, reverse=True, key=lambda x:x.size['width']*x.size['height'])
    elems = elems[:20]
    print "filter_elements(): Sorted elements by size and got the first few ones"
    # Below doesn't work on Android :(
    # print "Window rect: ", driver.get_window_rect()
    return elems
capabilities = {
  'chromeOptions': {
    'androidPackage': 'org.chromium.chrome',
  }
}


def get_clickable_elements(driver):
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
    print "get_clickable_elements(): found all elements"
    elems = divs + tds + a_elems + iframes
    elems = filter_elements(elems)
    return elems


if __name__ == "__main__":
    driver = webdriver.Remote('http://localhost:9515', capabilities)
    # driver.get('http://123moviesfree.com')
    driver.get('http://putlocker.kim')
    # driver.get('http://sockshare.net/watch/qvoeyOGl-guardians-of-the-galaxy-vol-2.html')
    # driver.get('http://sockshare.net/watch/qvoeyOGl-guardians-of-the-galaxy-vol-2.html')
    # driver.get('http://cafemovie.me/movie/deadpool-aOwMznWN')
    time.sleep(SHORT_PAUSE)
    elems = get_clickable_elements(driver)
    print_elements(elems, driver)
