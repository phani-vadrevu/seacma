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
# High priority things:
#

# Low priority things:
# python extract_chain_new.py ~/scratch/ad_jsgraph.log "http://www.reimagemac.com/lp/medd/index.php?tracking=expXML-mac&banner=Feed1_Open1_US_0.85_MAC4_86675&adgroup=&ads_name=Movies&keyword=86675&xml_uuid=28A11302-2457-4AE9-B5C6-A702D2745504&nms=1&lpx=mac4"
# Fix above
# When you see line 235505, , then you should take that runner into account when parsing
# line 236549. Keep a structure for these frames that are opened and when there is
# a WillLoadFrame, then immediately track that back and set up a redirection chain.
# Implemented the above fix using "pending_unknown_html_node_insert_frame_ids".
# TODO: Investigate this later and see what we are missing out.


# TODO: Inspect if Service workers are causing the bug below:
# line - 2443319 in ~/scratch/service_worker_bug.log has no runner.
# For now, this is simply handled by muting the assert in get_current_runner and in process set timeout
# Should inspect this further... later on

import argparse
import pprint
from collections import defaultdict
import timeout_decorator

from parse_utils import parse_log_entry, ignore_entry_url, peek_next_line
from utils import process_urls

REDIRECT_LIMIT = 30
LOG_PARSER_TIMEOUT = 120  # Time out in seconds

debug_url = "https://serve.popads.net/s?cid=18&iuid=1206431516&ts=1528126113&ps=2612706935&pw=281&pl=%21BVlaJy45jInpvQV7Ao%2BO2Jn0l71RpjJ2ixo87lhiuyhSeLDZavOrsHysyuICxgcmDCOvj4pFWyvCGMy6bSYFBN9Vevq2T0DSaUsCrPuvVD3%2BL4hyNdQIxMWnlMsXTNHD6yM5sGiI6NdRgjdHCosRBWX8tBhBUZs4KY7Z9HUpvZpJZNnKLBRQI3hJLuVsc3HEhZSL8UVm0MfN0vbv8eD3wYKqXVSTwb%2FARskgZJa6AfV3PsUVOKflQzrtMNsM%2BrYg0xv16rAGJK8WCRVzgu0PYA%3D%3D&s=1375,738,1,1375,738&v=nt.v&m=275,350,1,0,0,275,350,4,0,2,-1,-1,1375,738,1375,738"
class ChainExtractor(object):
    # The generated load_url in this code doesn't match the one from the redirect chain.
    # Its better to pass it explicitly to this function (after getting it from crawler logs)
    def __init__(self, log_path, load_url=None):
        self.log_path = log_path
        self.load_url = load_url
        self.frame_urls = {}

        # TODO: A frame can add a child frame that can also add an eventlistener(1),
        # or navigate frame(2)
        # While the JS spawned by the original frame is running? See below:
        # (1) line 64800 of test_js_eventlistener.txt
        # (2) line 115488 of test_iframe_src.txt
        # TODO: Are we introducing any ambiguity by not considering frame id
        # along with URL in redirections?
        # Consider this in the light of inter-frame redirections that we
        # might be missing othwerwise.
        # TODO: Our tracking of redirections misses this:
        # Consider what happens when a script includes an inline script
        # using dom.write. Since the newly added script will have the
        # original base HTML as the URL, that base HTML will be taken as the chain
        # originator.
        # But, probably, the above case is not that common as its not useful.

        # of form: frame_id --> [[],[],[]...]
        # The list can be: [frame_id, "compiled_script", script_id, script_src_URL]
        #                : [frame_id, "event_listener", event_target_id, event_name]
        #                : [frame_id, "scheduled_action", "function" or "code", value]
        #                : [frame_id, "request_animation_frame", callback_id]
        self.caller_stack = {}
        # of form: frame_id --> (target_id, event_name)

        # Push state or replace state navigation is logged in two entries
        # So, the first entry is saved below until the second entry is
        # parsed.
        self.pending_push_states = {}  # Frame ID --> src_url

        self.pending_handle_event = {} # Frame ID --> target

        # Temporary work-around for tracking window opens
        self.pending_window_open_frame_id = None

        self.pending_unknown_html_node_insert_frame_ids = set()
        self.frames_so_far = set()

        # Temporary work-around for bug related to unexplained compile scripts:
        self.ignore_script_run = None

        # New: Redirection nodes could be:
        # (frame_id, "URL", the_url)
        # (frame_id, "type", event_stuff)  --> type could be event_listener or scheduled_action

        # The redirection nodes could be:
        # EventHandler: (frameID, targetID, event_name)
        # URL
        # ScheduledAction: (frameID, code) # Note: its the same for both kinds of SAs
        # Destination --> (Source, "Reason")
        self.redirections = {}
        self.load_frame_redirections = {}
        self.parent_frames = {}
        self.child_frames = defaultdict(list)
        self.collect_redirects()
        self.process_load_frame_redirects()

    def debug_get_event_listeners(self,):
        ret_stuff = []
        for dest in self.redirections:
            if dest[1] == "event_listener":
                ret_stuff.append(dest)
        return ret_stuff

    def check_any_upstream_url_link(self, url):
        for dest in self.redirections:
            # Excluding cases where src is a about:blank URL
            if dest[1] == "URL" and dest[2] == url and not (
                    self.redirections[dest][0][1] == "URL" and
                    self.redirections[dest][0][2].strip('"') != 'about:blank'):
                return self.redirections[dest]

    def get_root_frame(self, frame_id):
        while frame_id in self.parent_frames:
            if frame_id == self.parent_frames[frame_id]:
                return frame_id
                #ipdb.set_trace()
            frame_id = self.parent_frames[frame_id]
        return frame_id

    # Check if any of the relatives of frame_id are in the frame_set
    # If so, return the matching relative.
    # If not, return None
    def check_frame_relation(self, frame_id):
        root_frame_id = self.get_root_frame(frame_id)
        frame_set = set(self.caller_stack.keys())
        # Frame Tree traversal DFS
        traversal_stack = [root_frame_id]
        while len(traversal_stack) != 0:
            frame_id = traversal_stack.pop()
            if frame_id in frame_set:
                return frame_id
            if frame_id in self.child_frames:
                traversal_stack = traversal_stack + self.child_frames[frame_id]
        return None

    @timeout_decorator.timeout(LOG_PARSER_TIMEOUT)
    def process_load_frame_redirects(self):
        for dest, src in self.load_frame_redirections.iteritems():
            #if dest[2] == debug_url:
            #    ipdb.set_trace()
            if dest not in self.redirections:
                self.redirections[dest] = src

    # Check if the frame or its parent, one of its kids or its siblings has started
    # the current JS execution.
    # If so, return the relevant caller frame ID. If not, return None
    def check_frame_id_call_stack(self, frame_id):
        if frame_id in self.caller_stack:
            return frame_id
        # Check Parent
        if (frame_id in self.parent_frames and
                self.parent_frames[frame_id] in self.caller_stack):
            return self.parent_frames[frame_id]
        # Check kids, get grand-kids
        grand_kids = []
        if frame_id in self.child_frames:
            for child_id in self.child_frames[frame_id]:
                if child_id in self.caller_stack:
                    return child_id
                if child_id in self.child_frames:
                    grand_kids = grand_kids + self.child_frames[child_id]
        # Check siblings
        if frame_id in self.parent_frames:
            parent_id = self.parent_frames[frame_id]
            for sibling_id in self.child_frames[parent_id]:
                if sibling_id in self.caller_stack:
                    return sibling_id
        # Check Grand kids
        for grand_kid_id in grand_kids:
            if grand_kid_id in self.caller_stack:
                return grand_kid_id
        return self.check_frame_relation(frame_id)


    def get_current_runner(self, frame_id, main_frame_id=None):

        if len(self.caller_stack) == 0:
            return None
        #if frame_id == '0x34a094467b68':
         #   ipdb.set_trace()
        frame_id = self.check_frame_id_call_stack(frame_id)
        try:
            assert (frame_id or
                main_frame_id in self.caller_stack)
        except:
            #ipdb.set_trace()
            return
        if frame_id is None:
            frame_id = main_frame_id
        assert len(self.caller_stack[frame_id]) > 0
        # Note: If returning the last one gives any problems (i.e. no further redirecting parent...)
        # then, may be we can return one above and so on... until we get to the root.
        # Note: returning 0 is wrong: sometimes, there can be element in the call stack who are not
        # exactly ancestors. For example, a handle event can happen while a scheduled action is running.
        return self.format_runner(self.caller_stack[frame_id][-1])

    # Format runner for storing in redirection chain.
    def format_runner(self, runner):
        if runner[1] == "compiled_script":
            return (runner[0], "URL", runner[3])
        elif runner[1] == "request_animation_frame":
            return runner
        # If runner has 4 elements
        else:
            return (runner[0], runner[1], (runner[2], runner[3]))


    def update_redirections(self, frame_id, dst, src, reason):
        dst = (frame_id, "URL", dst)
        src = (frame_id, "URL", src)
        if dst[2].strip('"') == "about:blank" or src[2].strip('"') == "about:blank":
            return False
        if not dst[2] or not src[2]:
            return False
        if dst[2] == src[2]:
            return False
        if dst in self.redirections:
            # If the redirection is already there
            if self.redirections[dst][0] == src:
                return True
            else:
                # TODO: Need to investigate how to deal with these later
                return True
                # 'Load Frame's generally tend to be missing some links
                # and can hence be ignored.
                #if reason == 'Load Frame':
                #    return True
                # If src is already part of chain, then we can ignore
                #if src in [x[0] for x in self.get_redirect_chain(dst)]:
                #    return True
                #ipdb.set_trace()
                #raise Exception
        self.redirections[dst] = (src, reason)
        return True

    # Process entries where frame or frame_root URLs are to be used based
    # on which one might be empty
    def process_frame_based_entries(self, entries, key, reason):
        assert 'frame_url' in entries
        if entries['frame_url'].strip('"') != "about:blank":
            frame_id = entries['frame']
            try:
                self.update_redirections(frame_id,
                    entries[key], entries['frame_url'], reason)
            except:
                pass
                #ipdb.set_trace()
        elif entries['local_frame_root_url'].strip('"') != "about:blank":
            frame_id = entries['local_frame_root']
            self.update_redirections(
                frame_id, entries[key], entries['local_frame_root_url'], reason)
        #self.update_redirections(
        #   entries['frame_url'], entries['local_frame_root_url'], 'Parent Frame')

    def process_server_redirect(self, f):
        entries = parse_log_entry(f)
        self.update_redirections(
            entries['frame'], entries['request_url'], entries['redirect_url'],
            "Server Redirect")

    # Frame IDs are the same across URLs.
    def process_meta_refresh(self, f):
        entries = parse_log_entry(f)
        self.process_frame_based_entries(entries, 'refresh_url', "Meta Refresh")

    # window.location
    # happens with the same FrameID
    def process_js_navigation(self, f):
        entries = parse_log_entry(f)
        runner = self.get_current_runner(entries['frame'], entries['main_frame'])
        if not runner and entries['origin_frame'] and entries['origin_frame'] != entries['frame']:
            runner = self.get_current_runner(entries['origin_frame'])
        if not runner:
            #print "Runner missing!!"
            #ipdb.set_trace()
            return
        dest = (entries['frame'], "URL", entries['url'])
        #if entries['url'] == debug_url:
        #    ipdb.set_trace()
        if runner and dest not in self.redirections:
            self.redirections[dest] = (
                                runner, 'JS Navigation')


    def process_window_open(self, f):
        entries = parse_log_entry(f)
        self.pending_window_open_frame_id = entries['frame']
        #self.redirections[entries['url']] = (self.get_current_runner(entries['frame']),
        #                                      'Window Open')

    def process_load_frame(self, f):
        entries = parse_log_entry(f)
        #if entries['load_url'] == debug_url:
        #    ipdb.set_trace()

        # Window Open
        frame_id = entries['frame']

        is_pending_unkown_node_insert = False
        if frame_id in self.pending_unknown_html_node_insert_frame_ids:
            is_pending_unkown_node_insert = True
            self.pending_unknown_html_node_insert_frame_ids.remove(frame_id)

        #if frame_id == "0x15d7c6f021e8":
        #    ipdb.set_trace()
        main_frame_id = entries['main_frame']

        if self.load_url is None and entries['load_url'].startswith('http'):
            self.load_url = entries['load_url']

        # TODO: Add URL to pending_window_open and double check to make sure that is the one that is being opened.

        # If there was a href link already inserted for this, then that is likely the reason for this WindowOpen
        # hence, we can ignore the current_runner and set a redirection for link click instead.
        dest = (frame_id, "URL", entries['load_url'])
        if self.pending_window_open_frame_id :
            src = (self.pending_window_open_frame_id, "URL", entries['load_url'])
            if src in self.redirections and src != dest:
                self.redirections[dest] = (src, "Anchor link click")
                self.pending_window_open_frame_id = None
                return

        # Else, its a window open that probably happened because of the current runner
        if (self.pending_window_open_frame_id and
                self.check_frame_id_call_stack(self.pending_window_open_frame_id)):
            runner = self.get_current_runner(self.pending_window_open_frame_id)
            self.redirections[dest] = (
                                runner, 'Window Open')
            self.parent_frames[frame_id] = self.pending_window_open_frame_id
            self.child_frames[self.pending_window_open_frame_id].append(frame_id)
            self.pending_window_open_frame_id = None
            return

        if is_pending_unkown_node_insert:
            #if frame_id == "0x3bdaa78421e8":
            #    ipdb.set_trace()
            src = self.check_any_upstream_url_link(entries['load_url'])
            if src and src != dest:
                self.redirections[dest] = (src[0], src[1] + " unknown")
            #else:
                #print dest
                #print "Nope!"


        ###########

        #print "totally unxpected!"
        #ipdb.set_trace()

        # Else (if no runner), then its a totally unexplained window open
        # We can atlead log the load frame.
        if entries['frame_url'].strip('"') != "about:blank":
            self.load_frame_redirections[(frame_id, "URL", entries['load_url'])] = (
                                    (frame_id, "URL", entries['frame_url']), "Load Frame")
        elif entries['local_frame_root_url'].strip('"') != "about:blank":
            self.load_frame_redirections[(frame_id, "URL", entries['load_url'])] = (
                (frame_id, "URL", entries['local_frame_root_url']), "Load Frame")

        self.process_frame_based_entries(entries, 'load_url', "Frame Load")

    def start_script_run(self, f):
        # TODO: Add script ID for cross checking
        entries = parse_log_entry(f)
        # Note: There might be an active JS Runner already
        # (Ex: line 2504 in test_delayed_js_nav_sa1.txt)
        frame_id = entries['frame']
        # Script run mapping to frame_url only makes sense when there
        #  is no current runner. If not, it could be due to say, a
        # scheduled action code or eval etc.
        # Its parent_farm or child frame could also be there.
        # Hence calling check_frame_id_call_stack
        related_frame_id = self.check_frame_id_call_stack(frame_id)

        if related_frame_id is None:
            if not entries['url'] and not self.ignore_script_run:
                self.ignore_script_run = entries['frame']
                return

            try:
                assert (entries['url'])
            except Exception:
                #ipdb.set_trace()
                return
            self.caller_stack[frame_id] = []
            dest = (entries['frame'], 'URL', entries['url'])
            # When a script is dynamically loaded by doc.write or v8setattribute,
            # then, we already set the redirection by this stage. We should make
            # sure not to rewrite it.
            if dest not in self.redirections:
                self.process_frame_based_entries(entries, "url", "Script Load")
            related_frame_id = frame_id
        self.caller_stack[related_frame_id].append((frame_id,
            "compiled_script", entries["scriptID"], entries['url']))

    def stop_script_run(self, f):
        entries = parse_log_entry(f)
        frame_id = entries['frame']
        if frame_id == self.ignore_script_run:
            self.ignore_script_run = None
            return
        frame_id = self.check_frame_id_call_stack(frame_id)
        try:
            assert self.caller_stack[frame_id][-1][1] == "compiled_script"
        except:
            return
        del self.caller_stack[frame_id][-1]
        if len(self.caller_stack[frame_id]) == 0:
            del self.caller_stack[frame_id]


    def start_event_handler_part1(self, f):
        entries = parse_log_entry(f)
        frame_id = entries['frame']
        target = (entries['current_target'])
        event = entries['event']
        assert frame_id not in self.pending_handle_event
        self.pending_handle_event[frame_id] = (target, event)


    def start_event_handler_part2(self, f, dom0=False):
        # TODO: Add script ID for cross checking
        entries = parse_log_entry(f)
        frame_id = entries['frame']
        if frame_id not in self.pending_handle_event:
            return
        target, event = self.pending_handle_event[frame_id]
        related_frame_id = self.check_frame_id_call_stack(frame_id)
        target = target + ":" + (
                entries['scriptID'] + " " + entries['callback_debug_name']).strip()
        if related_frame_id is None:
            self.caller_stack[frame_id] = []
            related_frame_id = frame_id
        dest = (frame_id,
            "event_listener", target, event)
        self.caller_stack[related_frame_id].append(dest)
        if dom0:
            label = 'dom0_%s_listener'
            self.redirections[dest] = (frame_id, "URL", entries['frame_url'], label)
        del self.pending_handle_event[frame_id]


    # line 2423 of test_dom0_eventlistener.txt has an example
    # The lazy compilation always happens after handle event call.
    # so, we link the current_event_listener to the frame_url when
    # we see this.
    def process_dom0_compilation(self, f):
        entries = parse_log_entry(f)
        frame_id = entries['frame']
        frame_id = self.check_frame_id_call_stack(frame_id)
        assert self.caller_stack[frame_id][-1][1] == "event_listener"
        handler = self.caller_stack[frame_id][-1]
        label = 'dom0_%s_listener' % (handler[3],)
        dest_tuple = (entries['frame'], "event_listener", (handler[2], handler[3]))
        self.redirections[dest_tuple] = ((frame_id, "URL", entries['frame_url']), label)

    # Sometimes, there can be more than one function call inside handleevent
    # TODO: Deal with this later. For now, just considering the last function call
    # for ending.
    def stop_event_handler(self, f):
        entries = parse_log_entry(f)
        #target = ":" + (
        #        entries['scriptID'] + " " + entries['callback_debug_name']).strip()

        frame_id = entries['frame']
        frame_id = self.check_frame_id_call_stack(frame_id)
        target = entries['current_target']

        assert self.caller_stack[frame_id][-1][1] == "event_listener"
        assert self.caller_stack[frame_id][-1][2].startswith(target)

        del self.caller_stack[frame_id][-1]
        if len(self.caller_stack[frame_id]) == 0:
            del self.caller_stack[frame_id]

    def start_animation_callback(self, f):
        entries = parse_log_entry(f)
        frame_id = entries['frame']
        callback_id = entries['callback_id']
        related_frame_id = self.check_frame_id_call_stack(frame_id)
        if related_frame_id is None:
            self.caller_stack[frame_id] = []
            related_frame_id = frame_id
        self.caller_stack[related_frame_id].append((
            frame_id, "request_animation_frame", callback_id))

    def stop_animation_callback(self, f):
        entries = parse_log_entry(f)
        frame_id = entries['frame']
        callback_id = entries['callback_id']
        related_frame_id = self.check_frame_id_call_stack(frame_id)
        if related_frame_id is None:
            self.caller_stack[frame_id] = []
            related_frame_id = frame_id
        try:
            assert self.caller_stack[related_frame_id][-1][1] == "request_animation_frame"
            assert self.caller_stack[frame_id][-1][2] == callback_id
        except:
            return
        del self.caller_stack[frame_id][-1]
        if len(self.caller_stack[frame_id]) == 0:
            del self.caller_stack[frame_id]

    def start_scheduled_action(self, f):
        entries = parse_log_entry(f)
        frame_id = entries['frame']
        name = "code" if "code" in entries else "function"
        value = (entries["code"].strip() if "code" in entries
                 else entries["scriptID"].strip() + " " +
                      entries['callback_debug_name'].strip())
        value = value.strip()
        related_frame_id = self.check_frame_id_call_stack(frame_id)
        if related_frame_id is None:
            self.caller_stack[frame_id] = []
            related_frame_id = frame_id
        self.caller_stack[related_frame_id].append((
            frame_id, "scheduled_action", name, value))

    def stop_scheduled_action(self, f):
        entries = parse_log_entry(f)
        frame_id = entries['frame']
        value = (entries["code"].strip() if "code" in entries
                 else entries["scriptID"].strip() + " " +
                      entries['callback_debug_name'].strip())
        value = value.strip()
        frame_id = self.check_frame_id_call_stack(frame_id)
        try:
            assert self.caller_stack[frame_id][-1][1] == "scheduled_action"
            assert self.caller_stack[frame_id][-1][3] == value
        except:
            return
        del self.caller_stack[frame_id][-1]
        if len(self.caller_stack[frame_id]) == 0:
            del self.caller_stack[frame_id]

    def process_history_pushstate1(self, entries):
        frame_id = entries['frame']
        self.pending_push_states[frame_id] = entries['frame_url']

    def process_history_pushstate2(self, entries):
        frame_id = entries['frame']
        # Unexpected part2 without part1!
        assert frame_id in self.pending_push_states
        self.update_redirections(
            entries['frame'],
            entries['frame_url'],
            self.pending_push_states[frame_id],
            "History Push State")
        del self.pending_push_states[frame_id]


    def process_addeventlistener(self, entries):
        dest_frameid = entries['frame']
        dest_targetid = entries['cpp_impl_ptr']
        dest_event = entries['args']['type'][9:-9] # Removing ::JSON::"
        # TODO: See if this makes us miss something!
        if (entries['args']['listener'].startswith('<=V8 VALUE NULL=>') or
                entries['args']['listener'].startswith('<=V8 VALUE UNDEFINED=>')):
            return
        try:
            assert entries['args']['listener'].startswith('<=V8 FUNCTION=>')
        except:
            #ipdb.set_trace()
            return
        code = entries['args']['listener'][15:].split('=', 1)[1].strip()
        dest_targetid = dest_targetid + ":" + code
        dest = (dest_frameid, "event_listener", (dest_targetid, dest_event))
        label = "%s_listener" % (dest_event,)
        #print "AddEventListener:", dest
        # To acount for a case where a background chromium script function starts up
        # without a compilescriptbegin and add an addeventlistener
        if ignore_entry_url(entries['frame_url']) and ignore_entry_url(entries['local_frame_root_url']):
            return
        runner = self.get_current_runner(entries['frame'], entries['main_frame'])
        if runner:
            self.redirections[dest] = (runner, label)

    def process_set_attribute_event_listener(self, entries):
        frame_id = entries['frame']
        target_id = entries['cpp_impl_ptr']
        assert 'attribute' in entries
        assert entries['attribute'].startswith('on')
        event = entries['attribute'][2:]
        target_id = target_id + ":" + (
                entries['scriptID'] + " " + entries['callback_debug_name']).strip()
        dest = (frame_id, "event_listener", (target_id, event))
        label = "on_%s_listener" % (event,)
        runner = self.get_current_runner(frame_id, entries['main_frame'])

        if runner and dest not in self.redirections:
            self.redirections[dest] = (runner, label)

    def set_animation_callback(self, entries):
        dest_frameid = entries['frame']
        callback_id = entries['callback_id']
        dest = (dest_frameid, "request_animation_frame", callback_id)
        runner = self.get_current_runner(dest_frameid)
        if runner and dest not in self.redirections:
            self.redirections[dest] = (runner, "animation_callback")

    def process_settimeout(self, entries):
        dest_frameid = entries['frame']
        handler = entries['args']['handler']

        if handler.startswith("::JSON::"):
            code = handler[9:-9].strip()
            name = "code"
        elif handler.startswith("<=V8 FUNCTION=>"):
            # Example: "<=V8 FUNCTION=> scriptID=21 (4,17) delayer": "21 (4,17) delayer"
            code = handler[15:].split('=', 1)[1].strip()
            name = "function"
        # handler can be <=V8 VALUE UNDEFINED=> or empty sometimes
        else:
            return
        dest = (dest_frameid, "scheduled_action", (name, code))
        runner = self.get_current_runner(dest_frameid, entries['main_frame'])
        # Muting to deal with unexplained settimeout calls probably related to service workers.
        #if not runner:
        #    ipdb.set_trace()
        if runner and dest not in self.redirections:
            self.redirections[dest] = (runner, "scheduled_action")

    def process_script_load(self, entries):
        frame_id = entries['frame']
        related_frame_id = self.check_frame_id_call_stack(frame_id)
        if ("src_url" in entries and
                related_frame_id is not None):
            runner = self.get_current_runner(related_frame_id)
            #print entries['src_url']
            url = process_urls(entries['src_url'], entries['frame_url'])
            dest = (frame_id, "URL", url)
            if runner and dest not in self.redirections:
                self.redirections[dest] = (runner, "Dynamic Script Load")

    def process_unknown_html_node_insert(self, entries):
        frame_id = entries['frame']
        if (frame_id not in self.frames_so_far):
            #self.caller_stack.keys()[0]
            self.pending_unknown_html_node_insert_frame_ids.add(entries['frame'])
            self.frames_so_far.add(frame_id)

    # TODO: Refactor this
    def process_set_attribute(self, entries):
        frame_id = entries['frame']
        if 'value' in entries and "V8 VALUE UNDEFINED" in entries['value']:
            return
        if (entries['attribute'] == 'src' and
                entries['interface'] == 'HTMLScriptElement'):
            assert "::JSON::" in entries['value']
            dest = (frame_id, "URL", entries["value"][9:-9])
            runner = self.get_current_runner(frame_id, entries['main_frame'])
            if runner and dest not in self.redirections:
                self.redirections[dest] = (runner, "Dynamic Script Load - set att")

        if (entries['attribute'] == 'href' and
                entries['interface'] == 'HTMLAnchorElement'):
            assert "::JSON::" in entries['value']
            dest = (frame_id, "URL", entries["value"][9:-9])
            runner = self.get_current_runner(frame_id, entries['main_frame'])
            # TODO: Do the below checks every where!
            if runner and dest != runner and (dest not in self.redirections):
                self.redirections[dest] = (runner, "Anchor link setup - set att")


    def process_set_attribute_method(self, entries):
        # TODO: This might to lead to a DOM node insert. We should look at this later.
        # look at the clicksor_support.txt example
        frame_id = entries['frame']
        if entries['args']['name'] == '::JSON::"href"::JSON::':
            assert "::JSON::" in entries['args']['value']
            dest = (frame_id, "URL", entries['args']["value"][9:-9])
            runner = self.get_current_runner(frame_id, entries['main_frame'])
            if runner and dest != runner and (dest not in self.redirections):
                self.redirections[dest] = (runner, "Anchor link setup - set att method")


    def set_child_frame(self, entries):
        frame_id = entries['frame']
        child_frame_id = entries['child_frame']
        self.parent_frames[child_frame_id] = frame_id
        self.child_frames[frame_id].append(child_frame_id)

    @timeout_decorator.timeout(LOG_PARSER_TIMEOUT)
    def collect_redirects(self,):
        with open(self.log_path, 'rb') as f:
            line = f.readline()
            while line:
                #if "060217.434604" in line:
                #    ipdb.set_trace()
                if "::DidReceiveMainResourceRedirect" in line:
                    self.process_server_redirect(f)
                elif "::DidHandleHttpRefresh" in line:
                    self.process_meta_refresh(f)
                elif "::WillNavigateFrame" in line:
                    self.process_js_navigation(f)
                elif "::WindowOpen" in line:
                    #print "WindowOpen"
                    #ipdb.set_trace()
                    self.process_window_open(f)
                elif "::WillLoadFrame" in line:
                    self.process_load_frame(f)
                elif "::DidCompileScript" in line:
                    self.start_script_run(f)
                elif "::DidRunCompiledScriptEnd" in line:
                    self.stop_script_run(f)
                elif "::DidCallHandleEventBegin" in line:
                    self.start_event_handler_part1(f)
                elif "::DidCallFunctionBegin" in line:
                    self.start_event_handler_part2(f)
                elif "::DidCompileLazyEventListener" in line:
                    self.start_event_handler_part2(f, dom0=True)
                #    self.process_dom0_compilation(f)
                elif "::DidCallHandleEventEnd" in line:
                    self.stop_event_handler(f)
                elif "::DidFireScheduledActionBegin" in line:
                    self.start_scheduled_action(f)
                elif "::DidFireScheduledActionEnd" in line:
                    self.stop_scheduled_action(f)
                elif "::ExecuteFrameRequestCallbackBegin" in line:
                    self.start_animation_callback(f)
                elif "::ExecuteFrameRequestCallbackEnd" in line:
                    self.stop_animation_callback(f)
                elif "::DidCallV8MethodCallback" in line:
                    entries = parse_log_entry(f)
                    if (entries['interface'] == 'History' and
                            (entries['attribute'] == 'pushState' or
                            entries['attribute'] == 'replaceState')):
                        self.process_history_pushstate1(entries)
                elif "::DidCallV8MethodTemplate" in line:
                    entries = parse_log_entry(f)
                    if (entries['interface'] == 'History' and
                            (entries['attribute'] == 'pushState' or
                            entries['attribute'] == 'replaceState')):
                        self.process_history_pushstate2(entries)
                    if (entries['interface'] == 'EventTarget' and
                            (entries['attribute'] == 'addEventListener')):
                        self.process_addeventlistener(entries)
                    if (entries['interface'] == 'Window' and
                            (entries['attribute'] == 'setTimeout' or
                            entries['attribute'] == 'setInterval')):
                        self.process_settimeout(entries)
                    if (entries['interface'] == 'Element' and
                            (entries['attribute'] == 'setAttribute')):
                        self.process_set_attribute_method(entries)
                elif "::RequestAnimationFrame" in line:
                    entries = parse_log_entry(f)
                    self.set_animation_callback(entries)
                elif "::DidCallV8SetAttributeEventListener" in line:
                    entries = parse_log_entry(f)
                    self.process_set_attribute_event_listener(entries)
                elif "::DidInsertDOMNode" in line:
                    entries = parse_log_entry(f)
                    if (entries['node'] == 'SCRIPT'):
                        self.process_script_load(entries)
                    elif (entries['node']) == 'HTML':
                        self.process_unknown_html_node_insert(entries)
                    # TODO: Add handling of Anchor element inserts
                elif "::DidCallV8SetAttribute" in line:
                    entries = parse_log_entry(f)
                    self.process_set_attribute(entries)
                elif "::DidCreateChildFrame" in line:
                    entries = parse_log_entry(f)
                    self.set_child_frame(entries)
                line = f.readline()

    def find_frame_id(self, url):
        found = []
        for key in self.redirections:
            if key[1] == "URL" and key[2] == url:
                found.append(key[0])
        return found

    def key_lookup(self, key):
        if key in self.redirections:
            return self.redirections[key]
        ## For some ads (example: RevenueHits network ads) the event listener set up and
        ## invocation code Frame IDs don't match. Hence we have this quick fix method to
        ## ignore the Frame IDs. The matching of key[2] itself is big evidence that these
        ## 2 are related anyway.
        ## QUICKFIX
        if key[1] == "event_listener":
            for existing_key in self.redirections:
                if (existing_key[1] == "event_listener" and
                    existing_key[2] == key[2]):
                    return self.redirections[existing_key]
        return None

    @timeout_decorator.timeout(LOG_PARSER_TIMEOUT)
    def get_redirect_chain(self, finald):
        #print self.redirections
        redirections = []
        redirection_set = set()
        found = self.find_frame_id(finald)
        #print "Found FrameIDs:", found
        if len(found) == 0:
            print "Could not find frameID for the given URL", finald
            return
        key = (found[0], "URL", finald)
        i = 0
        lookup = self.key_lookup(key)
        while lookup is not None:
            i += 1
            #print "*** ", key, self.redirections[key][1]
            if (key, lookup[1]) in redirection_set:
                print "Loop detected; breaking..."
                break
            redirections.append((key, lookup[1]))
            redirection_set.add((key, lookup[1]))
            key = lookup[0]
            lookup = self.key_lookup(key)
            # End criteria
            if key[1] == "URL" and key[2] == self.load_url:
                break
            if i == REDIRECT_LIMIT:
                break
        redirections.append((key, "FIRST"))
        #print "*** ", key
        #ipdb.set_trace()
        return redirections


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", type=str,
                        help="Path of the log file")
    parser.add_argument("url", type=str,
                        help="End URL for the chain")
    args = parser.parse_args()

    ce = ChainExtractor(args.log_path)
    print "args.url:", args.url
    #pprint.pprint(ce.redirections)
    redirections = ce.get_redirect_chain(args.url)
    pprint.pprint(redirections)
    #ipdb.set_trace()

if __name__ == "__main__":
    main()
