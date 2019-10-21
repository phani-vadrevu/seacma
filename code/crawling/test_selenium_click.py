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
from PIL import Image, ImageDraw
import time

driver = webdriver.Firefox()
# signal.signal(signal.SIGINT, self.signal_handler)
driver.get("http://localhost:9899/test_selenium_click.html")

# elem = driver.find_element_by_id('myBtn')
elem = driver.find_element_by_id('sample_img')

click_coords = (elem.location['x'] + (elem.size['width'] / 2.0), 
        elem.location['y'] + (elem.size['height'] / 2.0))

print "Location:", elem.location
print "Size:", elem.size
print "Approximate click location X: %s, Y: %s" % click_coords

driver.save_screenshot('temp.png')
im = Image.open('temp.png')
draw = ImageDraw.Draw(im)
draw.ellipse((click_coords[0] - 10, click_coords[1] - 10, 
            click_coords[0] + 10, click_coords[1] + 10),
            fill = 'blue',
            outline = 'blue')
im.save('temp.png')


time.sleep(5)
elem.click()
print "Click done"
