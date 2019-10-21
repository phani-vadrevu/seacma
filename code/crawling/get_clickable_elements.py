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
import time
import os
from collections import defaultdict

import cProfile

import utils
import config

# TODO: Try to remove elements whose parentElement <a> tag or the tag itself (href) points to home page.
# Images that are larger than 900 sq. pixels in area will be placed at the beginning of
# the Action list. The idea is that images and as are more likely to lead to links than others.
IMG_PREFERENCE_THRESHOLD = 900
SHORT_PAUSE = 5

def get_elems_js(tab):
    js_script = """
function elementDimensions(element, wHeight, wWidth) {
	var boundRect = element.getBoundingClientRect();
	var midy = boundRect.top + (boundRect.height / 2.0);
	var midx = boundRect.left + (boundRect.width / 2.0);
	if (boundRect.height != 0 && boundRect.width != 0 &&
		midy < wHeight && midx < wWidth && midy > 0 && midx > 0)
		return [midx, midy, boundRect.height, boundRect.width];
	else
		return [];
}

// Args: an array of element objects, window height and window width
// This function filters out elements that are
// (1) of size 0
// (2) Outside the viewport vertically or horizontally. 
// Returns a array of arrays
function filterElementArrays(elements, wHeight, wWidth) {
	var elem_sizes = [];
	for (var element of elements){
		elem = elementDimensions(element, wHeight, wWidth);
		if (elem.length > 0)
			elem_sizes.push(elem);
	}
	return elem_sizes;
}

// Similar to filterElementArrays but takes xpathResult object as
// one of the arguments
function filterXpathResults(xpathResults, wHeight, wWidth) {
	var elem_sizes = [];
	var element = xpathResults.iterateNext();
  	while (element) {
		elem = elementDimensions(element, wHeight, wWidth);
		if (elem.length > 0)
			elem_sizes.push(elem);
  		element = xpathResults.iterateNext();
  	}
  	return elem_sizes;
}

function getElementsByXpath(path) { 	
  	var xpathres =  document.evaluate(
  						path, document, null, 
  						XPathResult.UNORDERED_NODE_ITERATOR_TYPE, null);
  	return xpathres;
}

// Returns 2 array of arrays representing element locations and sizes for 
// all elems (except <img> and <a>) and (<img> and <a>) elems. 
// The <img> and <a> elems are more likely to have interesting links and are
// hence preferred.
function getElementData() {
	var wHeight = window.innerHeight;
	var wWidth = window.innerWidth;
	var element_data = [];
    var divs_xpath = getElementsByXpath('//div[not(descendant::div) and not(descendant::td)]');
    var divs = filterXpathResults(divs_xpath, wHeight, wWidth);
    var tds_xpath = getElementsByXpath('//td[not(descendant::div) and not(descendant::td)]');
    var tds = filterXpathResults(tds_xpath, wHeight, wWidth);
    var iframe_elems = document.getElementsByTagName('iframe');
    var iframes = filterElementArrays(iframe_elems, wHeight, wWidth);
    var a_elems = document.getElementsByTagName('a');
    var as = filterElementArrays(a_elems, wHeight, wWidth);
    element_data = element_data.concat(divs, tds);
    var img_elems = document.getElementsByTagName('img');
    var imgs = filterElementArrays(img_elems, wHeight, wWidth);
    var prefs = imgs.concat(as, iframes)
    return [element_data, prefs];
}

getElementData();
    """

    return_elems = tab.Runtime.evaluate(expression=js_script, returnByValue=True)
    return_elems = return_elems['result']['value']
    return return_elems

# Tries to retain return elements with unique sizes, and unique mid-points
# On some pages there are very close click-points that don't do anything different.
# Hence we try to filter out elements that have spatially close click points.
def get_unique_elements(elems):
    R = 100  # Coarseness in pixels for determining unique click points
    MAX_SAME_COORD = 2 # Don't allow more than 2 elements on same x or y coordinates.
    ret_elems = []
    prev_elems = set()  # Contains width and height of prev elements
    prev_mid_points = set()
    prev_x = defaultdict(int)
    prev_y = defaultdict(int)
    for elem in elems:
        if (elem[3], elem[2]) in prev_elems:
            continue
        coords = (elem[0], elem[1])
        mp_rounded = (utils.any_round(coords[0], R), utils.any_round(coords[1], R))
        if mp_rounded in prev_mid_points:
            continue
        # prev_x doesn't make sense at all in pages where all different kinds of elements are vertically aligned
        # for example: https://onlinetviz.com/american-crime-story/2/1
        if (prev_y[elem[1]] >= MAX_SAME_COORD):
            continue
        #print "debug, unique size elems", elem.size['width'], elem.size['height']
        ret_elems.append(elem)
        prev_elems.add((elem[3], elem[2]))
        prev_mid_points.add(mp_rounded)
        prev_x[elem[0]] += 1
        prev_y[elem[1]] += 1
    return ret_elems


def element_area(elem):
    return elem[2] * elem[3]

# Given a list of elements, Sort the elements by area,
def filter_elements(elems, imgs):
    rest_imgs = []
    selected_imgs = []
    for img in imgs:
        if element_area(img) > IMG_PREFERENCE_THRESHOLD:
            selected_imgs.append(img)
        else:
            rest_imgs.append(img)

    # Giving preferential treatment to large images and placing them at the
    # beginning of the queue.
    imgs = sorted(selected_imgs, reverse=True, key=element_area)
    elems = elems + rest_imgs
    elems = sorted(elems, reverse=True, key=element_area)
    elems = imgs + elems

    elems = get_unique_elements(elems)
    #print "filter_elements(): Retained only elements of unique size"

    elems = elems[:20]
    #print "filter_elements(): Sorted elements by size and got the first few ones"
    return elems


def get_clickable_elements(tab, agent_name):
    #return [(275.0, 350.0)]

    elems, imgs = get_elems_js(tab)
    elems = filter_elements(elems, imgs)

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
        #print elem[0], elem[1]
        elem_coords.append((elem[0], elem[1]))

    # Ensuring that there is at least one click point all the time
    if len(elem_coords) == 0:
        width, height = config.USER_AGENTS[agent_name]['window_size_cmd']
        click_point = (width/2, height/2)
        #ipdb.set_trace()
        elem_coords.append(click_point)
    return elem_coords


# TODO: Make this a standalone module for testing
if __name__ == "__main__":
    pass
