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
import ipdb
import pprint

class ChainExtractor:
    def __init__(self, log_path):
        self.log_path = log_path
        # Request -> Referer
        self.referers = {}
        self.frame_urls = {}

        # Push state or replace state navigation is logged in two entries
        # So, the first entry is saved below until the second entry is
        # parsed.
        self.pending_push_states = {}  # Frame ID --> src_url
        self.redirections = {}   # Destination --> (Source, "Reason")
        self.collect_redirects()
        #self.collect_redirects2()
        #self.collect_frame_urls()

    def parse_line(self, line, entries):
        key, value = (x.strip() for x in line.split("=", 1))
        entries[key] = value

    def parse_log_entry(self, f):
        entries = {}
        pos = f.tell()
        line = f.readline()
        while line.startswith("  "):
            self.parse_line(line, entries)
            pos = f.tell()
            line = f.readline()
        # Rewind the extra line for the next log entry that was read
        f.seek(pos)
        return entries
        #print entries


    # Some log entries are single line (example: :DidCallV8MethodCallback)
    # For these, we use this function to get the frame ID
    def get_frameid(self, line):
        frameid = line.split('=')[1].split()[0]
        return frameid

    def update_redirections(self, dst, src, reason):
        if dst == "about:blank" or src == "about:blank":
            return False
        if not dst or not src:
            return False
        if dst == src:
            return False
        if dst in self.redirections:
            if self.redirections[dst][0] == src:
                return True
            else:
                # 'Load Frame's generally tend to be missing some links
                # and can hence be ignored.
                if reason == 'Load Frame':
                    return True
                # If src is already part of chain, then we can ignore
                if src in [x[0] for x in self.get_redirect_chain(dst)]:
                    return True
                # Need to investigate how to deal with these later
                return True
                #ipdb.set_trace()
                #raise Exception
        self.redirections[dst] = (src, reason)
        return True

    # Process entries where frame or frame_root URLs are to be used based
    # on which one might be empty
    def process_frame_based_entries(self, entries, key, reason):
        if 'frame_url' not in entries:
            print entries, key, reason
        if entries['frame_url'] != "about:blank":
            self.update_redirections(
                entries[key], entries['frame_url'], reason)
        elif entries['root_frame_url'] != "about:blank":
            self.update_redirections(
                entries[key], entries['root_frame_url'], reason)
        self.update_redirections(
            entries['frame_url'], entries['root_frame_url'], 'Parent Frame')

    def process_server_redirect(self, f):
        entries = self.parse_log_entry(f)
        self.update_redirections(
            entries['request_url'], entries['redirect_url'],
            "Server Redirect")

    def process_meta_refresh(self, f):
        entries = self.parse_log_entry(f)
        self.process_frame_based_entries(entries, 'refresh_url', "Meta Refresh")

    def process_js_navigation(self, f):
        entries = self.parse_log_entry(f)
        # If there is a problem with frame_url_origin then use either
        # frame_url or root_frame_url to link up url
        if self.update_redirections(entries['url'],
                                    entries['frame_url_origin'],
                                    "JS Navigation"):
            self.update_redirections(
                entries['frame_url'], entries['root_frame_url'], 'Parent Frame')
        else:
            self.process_frame_based_entries(entries, 'url', "JS Navigation")

    def process_window_open(self, f):
        entries = self.parse_log_entry(f)
        #print "*** entries:", entries
        self.process_frame_based_entries(entries, 'url', "Window Open")

    def process_load_frame(self, f):
        entries = self.parse_log_entry(f)
        self.process_frame_based_entries(entries, 'url', "Load Frame")

    def process_history_pushstate1(self, f, line):
        frame_id = self.get_frameid(line)
        entries = self.parse_log_entry(f)
        self.pending_push_states[frame_id] = entries['frame_url']

    def process_history_pushstate2(self, entries):
        frameid = entries['frame']
        if frameid not in self.pending_push_states:
            # Unexpected part2 without part1!
            return
        self.update_redirections(
            entries['frame_url'],
            self.pending_push_states[frameid],
            "History Push State")
        del self.pending_push_states[frameid]

    def collect_redirects(self,):
        with open(self.log_path, 'rb') as f:
            line = f.readline()
            while line:
                if "::DidReceiveMainResourceRedirect" in line:
                    self.process_server_redirect(f)
                elif "::DidHandleHttpRefresh" in line:
                    self.process_meta_refresh(f)
                elif "::WillNavigateFrame" in line:
                    self.process_js_navigation(f)
                elif "::WindowOpen" in line:
                    print "WindowOpen"
                    #ipdb.set_trace()
                    self.process_window_open(f)
                elif "::WillLoadFrame" in line:
                    self.process_load_frame(f)
                elif ("interface=History  attribute=replaceState" in line or
                      "interface=History  attribute=pushState" in line):
                    self.process_history_pushstate1(f, line)
                elif ("::DidCallV8MethodTemplate" in line):
                    entries = self.parse_log_entry(f)
                    if (entries['interface'] == 'History' and
                            (entries['attribute'] == 'pushState' or
                            entries['attribute'] == 'replaceState')):
                        self.process_history_pushstate2(entries)
                line = f.readline()

    def get_redirect_chain(self, finald):
        chain = []
        url = finald
        while url in self.redirections:
            chain.append((url, self.redirections[url][1]))
            url = self.redirections[url][0]
        chain.append((url, ""))
        return chain


    def print_redirect_chain(self, finald):
        url = finald
        while url in self.redirections:
            print "*** ", url, self.redirections[url][1]
            url = self.redirections[url][0]
        print "*** ", url


parser = argparse.ArgumentParser()
parser.add_argument("log_path", type=str,
                    help="Path of the log file")
parser.add_argument("url", type=str,
                    help="End URL for the chain")
args = parser.parse_args()

ce = ChainExtractor(args.log_path)
ce.print_redirect_chain(args.url)