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
import dhash
import random

def find_different_bits(h1, h2):
    h1i = int(h1, 16)
    h2i = int(h2, 16)
    return dhash.get_num_bits_different(h1i, h2i)

set1 = ["2c51714d2b23b62b000040ffff7f3400",
        "2c71711d2b23b26b881e00ffff7f3000",
        "2c71711d2b23b26b881e00ffff7f3000",
        "2c71714d2b23b26b280a00ffff7f3000",
        "2c71714d2b23b26b880a00ffff7f3000",
        "2c71714d2b23b26b880e00ffff7f3000",
        "2c71714d2b23b62b881e00ffff7f3400"]


if __name__ == "__main__":
    s = set1
    for _ in range(5):
        print find_different_bits(*random.sample(s, 2))
