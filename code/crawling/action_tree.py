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
import logging
import traceback

from browser_interactor import BrowserInteractor


# ActionTree doesn't know anything about webdriver, ad_miner
class ActionTree(object):
    def  __init__(self, log_id, bi) :
        # Depth of the tree
        self.depth = 3
        # Number of kids per node
        self.num_kids = 2
        # BrowserInteractor instance
        self.bi = bi

        # node_id --> node_id
        self.parents = {}
        # node_id --> [node_id, ...]
        self.kids = {}
        # Next Node ID to be alloted. ID 0 is for the root node.
        self.next_node_id = 1
        # Stores the ID to action mapping. Note that that the root node will not have an action mapping.
        self.id_to_action = {}
        # Next action to be performed. If explore_kids is True that means that that action had
        # already been performed (except when next_action is 0 which doesn't denote any action at all)
        self.next_action_node_id = 0
        # If explore_kids is True that means the kids of the "next_action" node need to be explored and
        # next_action should be replaced
        self.explore_kids = True
        self.logger = logging.getLogger(log_id)

    def take_next_action(self,):
        try:
            self.take_next_action_temp()
        except Exception as e:
            print "take_next_action(); Exception: ", e
            traceback.print_exc()
            raise e
            #ipdb.set_trace()


    # Will be called by ad_miner
    def take_next_action_temp(self,):
        self.logger.info("action_tree: take_next_action()")
        if self.next_action_node_id == -1:
            return False
        # TODO: Make sure depth requirements are met before we set explore_kids flag
        if self.explore_kids:
            self._explore_kids(self.next_action_node_id)
        #logging.info("DEBUG: URL when take_next_action is called: %s", self.bi.driver.current_url)
        while True:
            nodes, earlier_nodes = self._get_later_siblings(self.next_action_node_id)
            action_list = [self.id_to_action[x] for x in nodes]
            self.logger.debug("action_tree: action_list - %s", action_list)
            # *** action_list's length could be 0 only when take_next_action() is called
            # for the first_time on root node state. Otherwise, the code in this func
            # will ensure that its length is not 0.
            # *** We remove the last element to ensure we don't include the current
            # element in the path that needs to be ensured.
            self.bi.ensure_state(self._get_path(nodes[0])[:-1])
            action_index, is_dead_end = self.bi.find_first_effective_action(action_list)
            self.logger.debug("action_tree: action result - index: %s, dead_end?: %s",
                             action_index, is_dead_end)
            # Note: when there is no action then action_index would be = len(nodes)
            # hence, rem_node_list will be []
            final_node_list = earlier_nodes + nodes[action_index:]
            rem_node_list = nodes[action_index:]
            parent_node = self.parents[self.next_action_node_id]
            # TODO: Remove entries from self.parents as well
            self.kids[parent_node] = final_node_list

            # If there was a successful action already; is_dead_end is relevant only here
            if len(rem_node_list) >= 1:
                is_dead_end = is_dead_end or self._check_dead_end(rem_node_list[0])
                is_depth_left = self._check_depth(rem_node_list[0])
                if not is_dead_end and is_depth_left:
                    # Note: We temporarily set next_action_node_id to some value;
                    # but this will be rewritten by _explore_kids()
                    # the next time take_next_action() is called. We postpone this setting of next_action
                    # so as to optimize the performance; sometimes, it is not required to take any extra action on
                    # the kids nodes.
                    self.next_action_node_id = rem_node_list[0]
                    self.explore_kids = True
                    return True
                elif is_dead_end:
                    self.logger.debug("Dead end met; finding another action_list.")
                elif not is_depth_left:
                    self.logger.debug("Depth limit met; finding another action_list.")

            # is_dead_end is not relevant anymore
            if len(rem_node_list) <= 1:
                self.next_action_node_id = self._find_next_action_list(parent_node)
            else:
                self.next_action_node_id = self._find_next_action_list(rem_node_list[0])

            if len(rem_node_list) == 0:
                # If the last action_list didn't yield any results and no more
                # action_lists could be found by _find_next_action_list(),
                # then we ran out of the action tree; just return False
                if self.next_action_node_id == -1:
                    return False
                continue
            # whether next_action_node_id is -1 or not doesn't matter.
            # It will be taken care of in the next call.
            return True

    # For a given node, if we can insert a child node given the current depth limit,
    # return True.
    def _check_depth(self, node):
        node_depth = len(self._get_path(node))
        return node_depth < self.depth

    # Get the path from the root node.
    def _get_path(self, node):
        reverse_path = []
        while True:
            if node == 0:
                break
            reverse_path.append(self.id_to_action[node])
            node = self.parents[node]
        return reverse_path[::-1]

    # Check depth requirements before we set the explore_kids flag.
    def _check_dead_end(self, node):
        return False
        # TODO: Should we check for same URL redirections and treat them as a dead-end?

    # We don't worry about depth requirements here.
    # Given the just finished node, return the next node that will be used for a subsequent
    # take_next_action() call
    def _find_next_action_list(self, node):
        if node == 0:
            return -1
        x_and_later, earlier = self._get_later_siblings(node)
        # TODO: Add debug stuff here for > case
        if (len(earlier) + 1 >= self.num_kids) or len(x_and_later) == 1:
            return self._find_next_action_list(self.parents[node])
        return x_and_later[1]

    # Returns a list containing sibling nodes that come after the passed node (including the passed node)
    # and another list containing all nodes that are earlier (these are successful actions and need to be saved intact)
    def _get_later_siblings(self, node):
        all_nodes = self.kids[self.parents[node]]
        return all_nodes[all_nodes.index(node):], all_nodes[:all_nodes.index(node)]

    # Open the parent node, fill with kids, set status to the first kid and unset the explore kids flag
    def _explore_kids(self, parent):
        kids = self.bi.get_click_coords()
        kid_ids = self._insert_nodes(parent, kids)
        self.next_action_node_id = kid_ids[0]
        self.explore_kids = False

    # Get the IDs for the nodes, insert as kids for the parent and return the node IDs of the kids
    def _insert_nodes(self, parent, kids):
        kid_ids = []
        for kid in kids:
            self.id_to_action[self.next_node_id] = kid
            kid_ids.append(self.next_node_id)
            self.parents[self.next_node_id] = parent
            self.next_node_id = self.next_node_id + 1
        self.kids[parent] = kid_ids
        return kid_ids


    #(x, y) to "(x,y)"
    def _action_to_string(self, action):
        return "(%s,%s)" % action

    #"(x,y)" to (x, y)
    def _string_to_action(self, action_str):
        x,y = action_str.split(',')
        return (x[1:], y[:-1])
