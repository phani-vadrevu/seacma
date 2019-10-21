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
"""
A class to read Malvertising logs from phone's output
"""
import subprocess
from collections import deque
from thread import start_new_thread

class LogReader:
    def collect_log_lines(self,):
        while True:
            line = self.proc.stdout.readline()
            if line != '':
                if "MALVERT" in line:
                    # print "Debug: got one!", line
                    self.lines_deque.append(line)
            else:
                break

    def get_log_lines(self,):
        lines_list = []
        while True:
            try:
                entry = self.lines_deque.popleft()
                lines_list.append(entry)
            except IndexError:
                break
        return lines_list
        
    def __init__(self,):
        self.lines_deque = deque() 
        self.proc = subprocess.Popen(['adb', 'logcat'], stdout = subprocess.PIPE)
        start_new_thread(self.collect_log_lines, ())
