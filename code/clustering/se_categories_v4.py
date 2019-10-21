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
# 12 is Palo Alto Networks Firewall messagei, since its a client-based message
# we are just not considering it in either true positives or false positives.
se_categories = {
        'Windows Support': [163, 300, 606, ],
        'Fake Flash/Java/Media Player': [6, 10, 19, 20, 32, 33, 54, 64, 68, 56, 57,
            71, 72,73, 76, 77, 82, 89, 91, 97, 106, 116, 121, 124, 141, 154, 156, 164, 173, 178,
            206, 207, 216, 249, 260, 290, 291, 313, 368, 428, 461, 479, 491, 501, 517, 593,
            604, 622, 640, 733, 823, 858, ],
        'Fake AV/Scareware': [21, 69, 286, 718, 891],
        'Lottery/Gift': [1, 24, 100, 102, 335, 339, 363, 564, 928],
        'SE Registration': [0, 38, 90, 107, 119, 127, 166, 190, 200, 229, 238, 287, 327, 328,
            329, 360, 364, 439, 526, 532, 551, 568, 578, 589, 610, 634, 642, 643, 678, 711, 
            740, 765, 785, 847, 1109, 1230],
        'Notification' : [201, 321, 355, ]}
