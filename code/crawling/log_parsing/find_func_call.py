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


def find_func_call(target_line_no, file_path):
    stack = []
    with open(file_path, "rb") as f:
        for current_no, line in enumerate(f, 1):
            if target_line_no == current_no:
                if len(stack) > 0:
                    print "Function call invocation log lines:", stack
                else:
                    print "The log line doesn't involve a JS funciton call"
                break
            elif "DidCallFunctionBegin" in line or "DidRunCompiledScriptBegin" in line:
                stack.append(current_no)
            elif "DidCallFunctionEnd" in line or "DidRunCompiledScriptEnd" in line:
                stack.pop()




parser = argparse.ArgumentParser()
parser.add_argument("line_number", type=int,
                    help="Line number that you want to analyze")
parser.add_argument("file_path", type=str,
                    help="Path of the log file")
args = parser.parse_args()
find_func_call(args.line_number, args.file_path)