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
import argparse
import os

import parse_utils


def remove_duplicates(input, output, inplace):
    prev_dict = {}
    line = ""
    print input.name
    print output.name

    while True:
        # Returns None if start of a log and
        # -1 if EOF
        line = parse_utils.not_log_start(input)
        #print line == -1, line, type(line)
        if line == -1:
            break
        elif line:
            output.write(line)
            continue
        line, entry_dict = parse_utils.peek_next_entry(input)
        lines = parse_utils.read_off_entry(input)
        del entry_dict['timestamp']
        if entry_dict != prev_dict:
            output.write(lines)
        prev_dict = entry_dict

    output.close()
    input.close()
    if inplace:
        os.rename(output.name, input.name)




parser = argparse.ArgumentParser()


parser.add_argument("input_file", type=argparse.FileType('rb'),
                    help="Path of the log file")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-o", "--out", type=argparse.FileType('wb'),
                    help="Path of the output file (default: dedudped_log.txt)",
                    default="deduped_log.txt")
group.add_argument("-i", "--inplace",
                   action="store_true",
                   help="Filter the log inplace")
args = parser.parse_args()
remove_duplicates(args.input_file, args.out, args.inplace)